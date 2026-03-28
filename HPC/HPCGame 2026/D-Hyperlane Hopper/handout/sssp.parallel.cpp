#include <vector>
#include <algorithm>
#include <cstdint>
#include <queue>
#include <unordered_map>
#include <atomic>
#include <utility>
#include <omp.h>

extern const uint64_t MAX_WEIGHT;
extern const uint64_t INF;

void calculate(uint32_t n, uint32_t m, uint32_t *edges, uint64_t *dis)
{
    // Parallel delta-stepping SSSP (Ulrich Meyer, Peter Sanders, 2003)
    // Buckets group vertices by distance range [k * DELTA, (k + 1) * DELTA).
    // Light edges (w <= DELTA) are relaxed repeatedly inside the active bucket,
    // heavy edges are scheduled into future buckets.
    // Larger DELTA reduces bucket count for random heavy weights; tune as needed.
    const uint64_t DELTA = 1ull << 20; // 1,048,576

    // Build CSR adjacency once. Sequential build is cache-friendly and simple.
    const uint32_t edge_start = 0;
    const uint32_t effective_edges = m;

    std::vector<uint32_t> degree(n, 0);
    for (uint32_t i = edge_start; i < m; ++i)
    {
        ++degree[edges[i * 3]];
    }

    std::vector<uint64_t> head(n + 1, 0);
    for (uint32_t i = 0; i < n; ++i)
    {
        head[i + 1] = head[i] + degree[i];
    }

    std::vector<uint32_t> adj_to(effective_edges);
    std::vector<uint64_t> adj_w(effective_edges);
    std::vector<uint64_t> cursor = head; // write positions per vertex
    for (uint32_t i = edge_start; i < m; ++i)
    {
        uint32_t u = edges[i * 3];
        uint32_t v = edges[i * 3 + 1];
        uint64_t w = edges[i * 3 + 2];
        uint64_t pos = cursor[u]++;
        adj_to[pos] = v;
        adj_w[pos] = w;
    }

    // Atomic distance array to avoid races during relaxations.
    std::vector<std::atomic<uint64_t>> dist(n);
#pragma omp parallel for schedule(static)
    for (int i = 0; i < static_cast<int>(n); ++i)
    {
        dist[i].store(dis[i], std::memory_order_relaxed);
    }

    // Sparse bucket storage to avoid gigantic arrays; priority queue tracks smallest non-empty bucket.
    std::unordered_map<uint64_t, std::vector<uint32_t>> buckets;
    buckets[0].push_back(0);
    std::priority_queue<uint64_t, std::vector<uint64_t>, std::greater<uint64_t>> active;
    active.push(0);

    while (!active.empty())
    {
        uint64_t current_bucket = active.top();
        active.pop();
        auto it_bucket = buckets.find(current_bucket);
        if (it_bucket == buckets.end() || it_bucket->second.empty())
        {
            continue;
        }

        std::vector<uint32_t> frontier = std::move(it_bucket->second);
        buckets.erase(it_bucket);
        std::vector<uint32_t> processed; // R set in delta-stepping
        std::vector<std::pair<uint64_t, uint32_t>> future_light; // vertices updated to later buckets

        // Process all light edges reachable inside this bucket.
        while (!frontier.empty())
        {
            processed.insert(processed.end(), frontier.begin(), frontier.end());

            std::vector<uint32_t> next_frontier;
#pragma omp parallel
            {
                std::vector<uint32_t> local_next;
                std::vector<std::pair<uint64_t, uint32_t>> local_future;
#pragma omp for schedule(dynamic, 64) nowait
                for (int idx = 0; idx < static_cast<int>(frontier.size()); ++idx)
                {
                    uint32_t u = frontier[idx];
                    uint64_t du = dist[u].load(std::memory_order_relaxed);
                    for (uint64_t e = head[u]; e < head[u + 1]; ++e)
                    {
                        uint64_t w = adj_w[e];
                        if (w > DELTA)
                        {
                            continue; // heavy edges handled later
                        }

                        uint32_t v = adj_to[e];
                        uint64_t cand = du + w;
                        uint64_t old = dist[v].load(std::memory_order_relaxed);
                        while (cand < old && !dist[v].compare_exchange_weak(old, cand, std::memory_order_relaxed))
                        {
                            // old updated with current value, keep trying
                        }
                        if (cand < old)
                        {
                            uint64_t target_bucket = cand / DELTA;
                            if (target_bucket == current_bucket)
                            {
                                local_next.push_back(v);
                            }
                            else
                            {
                                local_future.emplace_back(target_bucket, v);
                            }
                        }
                    }
                }
#pragma omp critical
                next_frontier.insert(next_frontier.end(), local_next.begin(), local_next.end());
#pragma omp critical
                future_light.insert(future_light.end(), local_future.begin(), local_future.end());
            }

            if (next_frontier.empty())
            {
                break;
            }

            // Deduplicate to keep bucket work small.
            std::sort(next_frontier.begin(), next_frontier.end());
            next_frontier.erase(std::unique(next_frontier.begin(), next_frontier.end()), next_frontier.end());
            frontier.swap(next_frontier);
        }

        // Schedule vertices discovered via light edges into their target future buckets.
        for (const auto &item : future_light)
        {
            uint64_t target_bucket = item.first;
            uint32_t v = item.second;
            auto &vec = buckets[target_bucket];
            bool was_empty = vec.empty();
            vec.push_back(v);
            if (was_empty)
            {
                active.push(target_bucket);
            }
        }

        // Relax heavy edges from all vertices settled in this bucket.
        std::vector<std::pair<uint32_t, uint64_t>> heavy_updates;
#pragma omp parallel
        {
            std::vector<std::pair<uint32_t, uint64_t>> local_updates;
#pragma omp for schedule(dynamic, 64) nowait
            for (int idx = 0; idx < static_cast<int>(processed.size()); ++idx)
            {
                uint32_t u = processed[idx];
                uint64_t du = dist[u].load(std::memory_order_relaxed);
                for (uint64_t e = head[u]; e < head[u + 1]; ++e)
                {
                    uint64_t w = adj_w[e];
                    if (w <= DELTA)
                    {
                        continue;
                    }
                    uint32_t v = adj_to[e];
                    uint64_t cand = du + w;
                    uint64_t old = dist[v].load(std::memory_order_relaxed);
                    while (cand < old && !dist[v].compare_exchange_weak(old, cand, std::memory_order_relaxed))
                    {
                        // retry
                    }
                    if (cand < old)
                    {
                        local_updates.emplace_back(v, cand);
                    }
                }
            }
#pragma omp critical
            heavy_updates.insert(heavy_updates.end(), local_updates.begin(), local_updates.end());
        }

        // Schedule heavy-edge relaxations into appropriate buckets.
        for (const auto &item : heavy_updates)
        {
            uint32_t v = item.first;
            uint64_t dv = item.second;
            uint64_t target_bucket = dv / DELTA;
            auto &vec = buckets[target_bucket];
            bool was_empty = vec.empty();
            vec.push_back(v);
            if (was_empty)
            {
                active.push(target_bucket);
            }
        }
    }

#pragma omp parallel for schedule(static)
    for (int i = 0; i < static_cast<int>(n); ++i)
    {
        dis[i] = dist[i].load(std::memory_order_relaxed);
    }
}