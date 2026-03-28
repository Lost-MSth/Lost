#include <omp.h>

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <queue>
#include <unordered_map>
#include <utility>
#include <vector>

extern const uint64_t MAX_WEIGHT;
extern const uint64_t INF;

void calculate(uint32_t n, uint32_t m, uint32_t* edges, uint64_t* dis) {
    // Parallel delta-stepping SSSP (Ulrich Meyer, Peter Sanders, 2003)
    // Buckets group vertices by distance range [k * DELTA, (k + 1) * DELTA).
    // Light edges (w <= DELTA) are relaxed repeatedly inside the active bucket,
    // heavy edges are scheduled into future buckets.
    // Larger DELTA reduces bucket count for random heavy weights; tune as
    // needed.
    const uint64_t DELTA = 1ull << 22;  // tuned for random 1..1e7 weights
    const int P = omp_get_max_threads();

    // Build CSR adjacency; 32-bit offsets are enough (m <= 2e8).
    const uint32_t edge_start = 0;
    const uint32_t effective_edges = m;

    std::vector<uint32_t> degree(n, 0);
#pragma omp parallel for schedule(static, 1 << 15)
    for (int i = edge_start; i < static_cast<int>(m); ++i) {
        uint32_t u = edges[i * 3];
#pragma omp atomic
        ++degree[u];
    }

    std::vector<uint32_t> head(n + 1, 0);
    for (uint32_t i = 0; i < n; ++i) {
        head[i + 1] = head[i] + degree[i];
    }

    std::vector<uint32_t> adj_to(effective_edges);
    std::vector<uint64_t> adj_w(effective_edges);
    std::vector<std::atomic<uint32_t>> cursor(n + 1);
#pragma omp parallel for schedule(static)
    for (int i = 0; i < static_cast<int>(n + 1); ++i) {
        cursor[i].store(head[i], std::memory_order_relaxed);
    }

#pragma omp parallel for schedule(static, 1 << 15)
    for (int i = edge_start; i < static_cast<int>(m); ++i) {
        uint32_t u = edges[i * 3];
        uint32_t v = edges[i * 3 + 1];
        uint64_t w = edges[i * 3 + 2];
        uint32_t pos = cursor[u].fetch_add(1, std::memory_order_relaxed);
        adj_to[pos] = v;
        adj_w[pos] = w;
    }

    // Atomic distance array to avoid races during relaxations.
    std::vector<std::atomic<uint64_t>> dist(n);
#pragma omp parallel for schedule(static)
    for (int i = 0; i < static_cast<int>(n); ++i) {
        dist[i].store(dis[i], std::memory_order_relaxed);
    }

    // Compact bucket storage: external vectors hold payloads, map is only
    // id->slot.
    std::vector<uint64_t> bucket_key;
    std::vector<std::vector<uint32_t>> bucket_val;
    std::vector<size_t> free_slots;
    bucket_key.reserve(n / 8 + 16);
    bucket_val.reserve(n / 8 + 16);
    free_slots.reserve(n / 8 + 16);
    std::unordered_map<uint64_t, size_t> bucket_idx;
    bucket_idx.reserve(n / 8 + 16);
    bucket_idx.max_load_factor(0.7f);
    auto ensure_slot = [&](uint64_t id) -> size_t {
        auto it = bucket_idx.find(id);
        if (it != bucket_idx.end()) {
            return it->second;
        }
        size_t slot;
        if (!free_slots.empty()) {
            slot = free_slots.back();
            free_slots.pop_back();
            bucket_key[slot] = id;
            bucket_val[slot].clear();
        } else {
            slot = bucket_key.size();
            bucket_key.push_back(id);
            bucket_val.emplace_back();
        }
        bucket_idx.emplace(id, slot);
        return slot;
    };

    auto push_bucket = [&](uint64_t id, const std::vector<uint32_t>& vertices) {
        size_t slot = ensure_slot(id);
        auto& dest = bucket_val[slot];
        dest.insert(dest.end(), vertices.begin(), vertices.end());
    };

    auto push_bucket_single = [&](uint64_t id, uint32_t v) {
        size_t slot = ensure_slot(id);
        bucket_val[slot].push_back(v);
    };

    std::priority_queue<uint64_t, std::vector<uint64_t>, std::greater<uint64_t>>
        active;
    push_bucket_single(0, 0);
    active.push(0);

    // Per-iteration dedup tag to avoid sort/unique overhead.
    std::vector<std::atomic<uint64_t>> seen(n);
#pragma omp parallel for schedule(static)
    for (int i = 0; i < static_cast<int>(n); ++i) {
        seen[i].store(0, std::memory_order_relaxed);
    }
    uint64_t tag_counter = 1;

    // Thread-local buffers reused across buckets to cut allocations.
    std::vector<std::vector<uint32_t>> next_tls(P);
    std::vector<std::unordered_map<uint64_t, std::vector<uint32_t>>> future_tls(
        P);
    std::vector<std::unordered_map<uint64_t, std::vector<uint32_t>>> heavy_tls(
        P);
    for (int t = 0; t < P; ++t) {
        future_tls[t].reserve(32);
        future_tls[t].max_load_factor(0.7f);
        heavy_tls[t].reserve(32);
        heavy_tls[t].max_load_factor(0.7f);
    }

    while (!active.empty()) {
        uint64_t current_bucket = active.top();
        active.pop();
        auto it_slot = bucket_idx.find(current_bucket);
        if (it_slot == bucket_idx.end()) {
            continue;
        }
        size_t slot = it_slot->second;
        auto& slot_vec = bucket_val[slot];
        if (slot_vec.empty()) {
            bucket_idx.erase(it_slot);
            bucket_key[slot] = UINT64_MAX;
            free_slots.push_back(slot);
            continue;
        }

        std::vector<uint32_t> frontier;
        frontier.swap(slot_vec);
        bucket_idx.erase(it_slot);
        bucket_key[slot] = UINT64_MAX;
        slot_vec.clear();
        free_slots.push_back(slot);
        std::vector<uint32_t> processed;  // R set in delta-stepping

        // Process all light edges reachable inside this bucket.
        while (!frontier.empty()) {
            const uint64_t tag = tag_counter++;
            processed.insert(processed.end(), frontier.begin(), frontier.end());
            for (int t = 0; t < P; ++t) {
                next_tls[t].clear();
                future_tls[t].clear();
            }

#pragma omp parallel
            {
                int tid = omp_get_thread_num();
                auto& local_next = next_tls[tid];
                auto& local_future = future_tls[tid];
#pragma omp for schedule(static) nowait
                for (int idx = 0; idx < static_cast<int>(frontier.size());
                     ++idx) {
                    uint32_t u = frontier[idx];
                    uint64_t du = dist[u].load(std::memory_order_relaxed);
                    for (uint32_t e = head[u]; e < head[u + 1]; ++e) {
                        uint64_t w = adj_w[e];
                        if (w > DELTA) {
                            continue;  // heavy edges handled later
                        }

                        uint32_t v = adj_to[e];
                        uint64_t cand = du + w;
                        uint64_t old = dist[v].load(std::memory_order_relaxed);
                        while (cand < old &&
                               !dist[v].compare_exchange_weak(
                                   old, cand, std::memory_order_relaxed)) {
                        }
                        if (cand < old) {
                            uint64_t target_bucket = cand / DELTA;
                            if (target_bucket == current_bucket) {
                                uint64_t prev =
                                    seen[v].load(std::memory_order_relaxed);
                                while (
                                    prev != tag &&
                                    !seen[v].compare_exchange_weak(
                                        prev, tag, std::memory_order_relaxed)) {
                                }
                                if (prev != tag) {
                                    local_next.push_back(v);
                                }
                            } else {
                                local_future[target_bucket].push_back(v);
                            }
                        }
                    }
                }
            }

            std::vector<uint32_t> next_frontier;
            for (auto& vec : next_tls) {
                next_frontier.insert(next_frontier.end(), vec.begin(),
                                     vec.end());
            }
            for (auto& m : future_tls) {
                for (auto& kv : m) {
                    bool fresh = bucket_idx.find(kv.first) == bucket_idx.end();
                    push_bucket(kv.first, kv.second);
                    if (fresh) {
                        active.push(kv.first);
                    }
                }
            }

            if (next_frontier.empty()) {
                break;
            }
            frontier.swap(next_frontier);
        }

        // Relax heavy edges from all vertices settled in this bucket.
        for (int t = 0; t < P; ++t) {
            heavy_tls[t].clear();
        }
#pragma omp parallel
        {
            int tid = omp_get_thread_num();
            auto& local_updates = heavy_tls[tid];
#pragma omp for schedule(static) nowait
            for (int idx = 0; idx < static_cast<int>(processed.size()); ++idx) {
                uint32_t u = processed[idx];
                uint64_t du = dist[u].load(std::memory_order_relaxed);
                for (uint32_t e = head[u]; e < head[u + 1]; ++e) {
                    uint64_t w = adj_w[e];
                    if (w <= DELTA) {
                        continue;
                    }
                    uint32_t v = adj_to[e];
                    uint64_t cand = du + w;
                    uint64_t old = dist[v].load(std::memory_order_relaxed);
                    while (cand < old &&
                           !dist[v].compare_exchange_weak(
                               old, cand, std::memory_order_relaxed)) {
                    }
                    if (cand < old) {
                        uint64_t target_bucket = cand / DELTA;
                        local_updates[target_bucket].push_back(v);
                    }
                }
            }
        }
        for (auto& m : heavy_tls) {
            for (auto& kv : m) {
                bool fresh = bucket_idx.find(kv.first) == bucket_idx.end();
                push_bucket(kv.first, kv.second);
                if (fresh) {
                    active.push(kv.first);
                }
            }
        }
    }

#pragma omp parallel for schedule(static)
    for (int i = 0; i < static_cast<int>(n); ++i) {
        dis[i] = dist[i].load(std::memory_order_relaxed);
    }
}