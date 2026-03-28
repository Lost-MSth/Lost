#include <omp.h>

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <queue>
#include <unordered_map>
#include <utility>
#include <vector>

// Simple aligned allocator to keep hot arrays cacheline-aligned for SIMD/load.
template <class T, std::size_t Alignment = 64>
struct AlignedAllocator {
    using value_type = T;
    T* allocate(std::size_t n) {
        if (n > static_cast<std::size_t>(-1) / sizeof(T)) throw std::bad_alloc();
        void* p = std::aligned_alloc(Alignment, ((n * sizeof(T) + Alignment - 1) / Alignment) * Alignment);
        if (!p) throw std::bad_alloc();
        return reinterpret_cast<T*>(p);
    }
    void deallocate(T* p, std::size_t) noexcept { std::free(p); }
    template <class U>
    struct rebind { using other = AlignedAllocator<U, Alignment>; };
    using is_always_equal = std::true_type;
    friend constexpr bool operator==(const AlignedAllocator&, const AlignedAllocator&) noexcept {
        return true;
    }
    friend constexpr bool operator!=(const AlignedAllocator&, const AlignedAllocator&) noexcept {
        return false;
    }
};

// Local INF avoids reliance on external TU linkage of const globals.
constexpr uint64_t INF_LOCAL = 1000000000000000000ull;

void calculate(uint32_t n, uint32_t m, uint32_t* edges, uint64_t* dis) {
    // Array-based delta-stepping (no bucket map) with light/heavy split.
    const uint64_t BASE_DELTA = 1ull << 19;  // fixed delta
    const int P = omp_get_max_threads();

    const uint32_t edge_start = 0;
    const uint32_t effective_edges = m;

    // Degrees on original ids.
    std::vector<uint32_t, AlignedAllocator<uint32_t>> degree(n, 0);
#pragma omp parallel for schedule(static, 1 << 15)
    for (int i = edge_start; i < static_cast<int>(m); ++i) {
        uint32_t u = edges[i * 3];
#pragma omp atomic
        ++degree[u];
    }

    std::vector<uint32_t, AlignedAllocator<uint32_t>> head(n + 1, 0);
    for (uint32_t i = 0; i < n; ++i) {
        head[i + 1] = head[i] + degree[i];
    }

    std::vector<uint32_t, AlignedAllocator<uint32_t>> adj_to(effective_edges);
    std::vector<uint64_t, AlignedAllocator<uint64_t>> adj_w(effective_edges);
    std::vector<std::atomic<uint32_t>, AlignedAllocator<std::atomic<uint32_t>>>
        cursor(n + 1);
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

    // Atomic distance array on original ids (seeded from dis input).
    std::vector<std::atomic<uint64_t>, AlignedAllocator<std::atomic<uint64_t>>>
        dist(n);
#pragma omp parallel for schedule(static)
    for (int i = 0; i < static_cast<int>(n); ++i) {
        dist[i].store(dis[i], std::memory_order_relaxed);
    }
    dist[0].store(0, std::memory_order_relaxed);

    // Per-iteration tag for dedup inside a step.
    std::vector<std::atomic<uint64_t>, AlignedAllocator<std::atomic<uint64_t>>>
        seen(n);
#pragma omp parallel for schedule(static)
    for (int i = 0; i < static_cast<int>(n); ++i) {
        seen[i].store(0, std::memory_order_relaxed);
    }
    uint64_t tag_counter = 1;

    // In-queue flags (array-based PQ).
    std::vector<std::atomic<uint8_t>, AlignedAllocator<std::atomic<uint8_t>>> inQ(n);
#pragma omp parallel for schedule(static)
    for (int i = 0; i < static_cast<int>(n); ++i) {
        inQ[i].store(0, std::memory_order_relaxed);
    }
    inQ[0].store(1, std::memory_order_relaxed);

    std::vector<std::vector<uint32_t, AlignedAllocator<uint32_t>>> next_tls(P);
    std::vector<std::vector<uint32_t, AlignedAllocator<uint32_t>>> extract_tls(P);
    std::vector<std::vector<uint32_t, AlignedAllocator<uint32_t>>> remain_tls(P);
    std::vector<std::vector<uint32_t, AlignedAllocator<uint32_t>>> add_tls(P);
    std::vector<std::vector<uint32_t, AlignedAllocator<uint32_t>>> add_heavy_tls(P);

    std::vector<uint32_t, AlignedAllocator<uint32_t>> active;
    active.reserve(std::max<uint32_t>(1024, n / 256 + 1));
    active.push_back(0);
    const size_t dense_threshold = std::max<uint32_t>(1024, n / 4 + 1);
    bool dense_mode = false;

    while (true) {
        if (active.empty() && !dense_mode) break;

        // Decide dense/sparse mode based on active size.
        if (!dense_mode && active.size() > dense_threshold) {
            dense_mode = true;
        }

        uint64_t theta = INF_LOCAL;
        if (dense_mode) {
            uint64_t min_dist = INF_LOCAL;
#pragma omp parallel for reduction(min : min_dist)
            for (int i = 0; i < static_cast<int>(n); ++i) {
                if (inQ[i].load(std::memory_order_relaxed)) {
                    uint64_t d = dist[i].load(std::memory_order_relaxed);
                    if (d < min_dist) min_dist = d;
                }
            }
            if (min_dist == INF_LOCAL) break;
            theta = min_dist + BASE_DELTA;
        } else {
            // Sample-based threshold (rho-stepping style) to reduce iterations.
            const size_t active_sz = active.size();
            if (active_sz <= 1024) {
                uint64_t min_dist = INF_LOCAL;
#pragma omp parallel for reduction(min : min_dist)
                for (int idx = 0; idx < static_cast<int>(active_sz); ++idx) {
                    uint32_t v = active[idx];
                    if (inQ[v].load(std::memory_order_relaxed)) {
                        uint64_t d = dist[v].load(std::memory_order_relaxed);
                        if (d < min_dist) min_dist = d;
                    }
                }
                if (min_dist == INF_LOCAL) break;
                theta = min_dist + BASE_DELTA;
            } else {
                const size_t sample_n = std::min<size_t>(4096, active_sz);
                const size_t stride = std::max<size_t>(1, active_sz / sample_n);
                std::vector<uint64_t, AlignedAllocator<uint64_t>> samples;
                samples.reserve(sample_n);
                for (size_t i = 0; i < active_sz && samples.size() < sample_n; i += stride) {
                    uint32_t v = active[i];
                    if (!inQ[v].load(std::memory_order_relaxed)) continue;
                    samples.push_back(dist[v].load(std::memory_order_relaxed));
                }
                if (samples.empty()) break;
                std::sort(samples.begin(), samples.end());
                size_t rho = std::max<size_t>(4096, active_sz / 8);
                size_t q = std::min(samples.size() - 1,
                                    static_cast<size_t>((static_cast<double>(rho) * samples.size()) / active_sz));
                theta = samples[q];
            }
        }

        // Extract vertices within current bucket [min_dist, theta].
        for (int t = 0; t < P; ++t) {
            extract_tls[t].clear();
            remain_tls[t].clear();
        }
#pragma omp parallel
        {
            int tid = omp_get_thread_num();
            auto& local_extract = extract_tls[tid];
            auto& local_remain = remain_tls[tid];
            if (dense_mode) {
#pragma omp for schedule(static)
                for (int i = 0; i < static_cast<int>(n); ++i) {
                    if (!inQ[i].load(std::memory_order_relaxed)) continue;
                    uint64_t d = dist[i].load(std::memory_order_relaxed);
                    if (d <= theta) {
                        // Each vertex is handled by a single iteration; no exchange needed.
                        inQ[i].store(0, std::memory_order_relaxed);
                        local_extract.push_back(static_cast<uint32_t>(i));
                    }
                }
            } else {
#pragma omp for schedule(static)
                for (int idx = 0; idx < static_cast<int>(active.size()); ++idx) {
                    uint32_t v = active[idx];
                    if (!inQ[v].load(std::memory_order_relaxed)) continue;
                    uint64_t d = dist[v].load(std::memory_order_relaxed);
                    if (d <= theta) {
                        if (inQ[v].exchange(0, std::memory_order_relaxed)) {
                            local_extract.push_back(v);
                        }
                    } else {
                        local_remain.push_back(v);
                    }
                }
            }
        }

        std::vector<uint32_t, AlignedAllocator<uint32_t>> frontier;
        for (auto& vec : extract_tls) {
            frontier.insert(frontier.end(), vec.begin(), vec.end());
        }
        if (!dense_mode) {
            active.clear();
            for (auto& vec : remain_tls) {
                active.insert(active.end(), vec.begin(), vec.end());
            }
        }
        if (frontier.empty()) {
            continue;
        }

        std::vector<uint32_t, AlignedAllocator<uint32_t>> processed;

        // Process light edges within this bucket (bucket fusion style).
        while (!frontier.empty()) {
            const uint64_t tag = tag_counter++;
            processed.insert(processed.end(), frontier.begin(), frontier.end());
            for (int t = 0; t < P; ++t) {
                next_tls[t].clear();
                add_tls[t].clear();
            }

#pragma omp parallel
            {
                int tid = omp_get_thread_num();
                auto& local_next = next_tls[tid];
#pragma omp for schedule(static) nowait
                for (int idx = 0; idx < static_cast<int>(frontier.size()); ++idx) {
                    uint32_t u = frontier[idx];
                    uint64_t du = dist[u].load(std::memory_order_relaxed);
                    for (uint32_t e = head[u]; e < head[u + 1]; ++e) {
                        uint64_t w = adj_w[e];
                        if (w > BASE_DELTA) continue;  // heavy
                        uint32_t v = adj_to[e];
                        uint64_t cand = du + w;
                        uint64_t old = dist[v].load(std::memory_order_relaxed);
                        while (cand < old &&
                               !dist[v].compare_exchange_weak(
                                   old, cand, std::memory_order_relaxed)) {
                        }
                        if (cand < old) {
                            if (cand <= theta) {
                                uint64_t prev = seen[v].load(std::memory_order_relaxed);
                                while (prev != tag &&
                                       !seen[v].compare_exchange_weak(
                                           prev, tag, std::memory_order_relaxed)) {
                                }
                                if (prev != tag) {
                                    local_next.push_back(v);
                                }
                            } else {
                                if (!inQ[v].exchange(1, std::memory_order_relaxed)) {
                                    add_tls[tid].push_back(v);
                                }
                            }
                        }
                    }
                }
            }

            std::vector<uint32_t, AlignedAllocator<uint32_t>> next_frontier;
            for (auto& vec : next_tls) {
                next_frontier.insert(next_frontier.end(), vec.begin(), vec.end());
            }
            if (!dense_mode) {
                for (auto& vec : add_tls) {
                    active.insert(active.end(), vec.begin(), vec.end());
                }
            }
            if (next_frontier.empty()) break;
            frontier.swap(next_frontier);
        }

        // Heavy edges from processed vertices.
#pragma omp parallel
        {
#pragma omp for schedule(static) nowait
            for (int idx = 0; idx < static_cast<int>(processed.size()); ++idx) {
                uint32_t u = processed[idx];
                uint64_t du = dist[u].load(std::memory_order_relaxed);
                for (uint32_t e = head[u]; e < head[u + 1]; ++e) {
                    uint64_t w = adj_w[e];
                    if (w <= BASE_DELTA) continue;
                    uint32_t v = adj_to[e];
                    uint64_t cand = du + w;
                    uint64_t old = dist[v].load(std::memory_order_relaxed);
                    while (cand < old &&
                           !dist[v].compare_exchange_weak(
                               old, cand, std::memory_order_relaxed)) {
                    }
                    if (cand < old) {
                        if (!inQ[v].exchange(1, std::memory_order_relaxed)) {
                            add_heavy_tls[omp_get_thread_num()].push_back(v);
                        }
                    }
                }
            }
        }
        if (!dense_mode) {
            for (auto& vec : add_heavy_tls) {
                active.insert(active.end(), vec.begin(), vec.end());
            }
        }
        for (int t = 0; t < P; ++t) {
            add_heavy_tls[t].clear();
        }

        if (dense_mode) {
            // Check if we can switch back to sparse mode.
            size_t inq_count = 0;
#pragma omp parallel for reduction(+:inq_count)
            for (int i = 0; i < static_cast<int>(n); ++i) {
                if (inQ[i].load(std::memory_order_relaxed)) {
                    ++inq_count;
                }
            }
            if (inq_count < dense_threshold) {
                active.clear();
                for (int t = 0; t < P; ++t) {
                    extract_tls[t].clear();
                }
#pragma omp parallel
                {
                    int tid = omp_get_thread_num();
                    auto& local_extract = extract_tls[tid];
#pragma omp for schedule(static)
                    for (int i = 0; i < static_cast<int>(n); ++i) {
                        if (inQ[i].load(std::memory_order_relaxed)) {
                            local_extract.push_back(static_cast<uint32_t>(i));
                        }
                    }
                }
                for (auto& vec : extract_tls) {
                    active.insert(active.end(), vec.begin(), vec.end());
                }
                dense_mode = false;
            }
        }
    }

#pragma omp parallel for schedule(static)
    for (int i = 0; i < static_cast<int>(n); ++i) {
        dis[i] = dist[i].load(std::memory_order_relaxed);
    }
}