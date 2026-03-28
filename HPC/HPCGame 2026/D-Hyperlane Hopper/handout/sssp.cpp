#include <omp.h>
#include <algorithm>
#include <cstdint>
#include <limits>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

static const uint64_t INF_OUTPUT = 1000000000000000000ULL;
static const uint64_t INF_CALC = 0x3f3f3f3f3f3f3f3fULL;

void calculate(uint32_t n, uint32_t m, uint32_t* edges, uint64_t* dis) {
    int T = omp_get_max_threads();

    uint32_t* row_offset = (uint32_t*)aligned_alloc(64, (n + 1) * sizeof(uint32_t));
    memset(row_offset, 0, (n + 1) * sizeof(uint32_t));
    uint32_t* cols = (uint32_t*)aligned_alloc(64, m * sizeof(uint32_t));
    uint32_t* weights = (uint32_t*)aligned_alloc(64, m * sizeof(uint32_t));

    // =========================================================
    // 1. 自适应 CSR 构建
    // =========================================================
    if (m < 15ull * n) {
        // 稀疏图路径：直接使用原子操作，减少内存分配和零初始化开销
        #pragma omp parallel for
        for (uint32_t i = 0; i < m; i++) {
            __atomic_fetch_add(&row_offset[edges[3 * i] + 1], 1, __ATOMIC_RELAXED);
        }
        for (uint32_t i = 0; i < n; i++) row_offset[i + 1] += row_offset[i];

        uint32_t* cur_pos = (uint32_t*)aligned_alloc(64, (n + 1) * sizeof(uint32_t));
        memcpy(cur_pos, row_offset, (n + 1) * sizeof(uint32_t));
        #pragma omp parallel for
        for (uint32_t i = 0; i < m; i++) {
            uint32_t u = edges[3 * i];
            uint32_t p = __atomic_fetch_add(&cur_pos[u], 1, __ATOMIC_RELAXED);
            cols[p] = edges[3 * i + 1];
            weights[p] = edges[3 * i + 2];
        }
        free(cur_pos);
    } else {
        // 稠密图路径：线程局部统计，适合 M 极大（10^9）的情况
        uint32_t* thread_deg = (uint32_t*)aligned_alloc(64, (uint64_t)T * (n + 1) * sizeof(uint32_t));
        memset(thread_deg, 0, (uint64_t)T * (n + 1) * sizeof(uint32_t));
        #pragma omp parallel
        {
            int tid = omp_get_thread_num();
            uint32_t* my_deg = thread_deg + (uint64_t)tid * (n + 1);
            #pragma omp for schedule(static)
            for (uint32_t i = 0; i < m; i++) my_deg[edges[3 * i]]++;
        }
        for (uint32_t j = 0; j < n; j++) {
            uint32_t sum = 0;
            for (int i = 0; i < T; i++) {
                uint32_t d = thread_deg[(uint64_t)i * (n + 1) + j];
                thread_deg[(uint64_t)i * (n + 1) + j] = row_offset[j] + sum;
                sum += d;
            }
            row_offset[j + 1] = row_offset[j] + sum;
        }
        #pragma omp parallel
        {
            int tid = omp_get_thread_num();
            uint32_t* my_pos = thread_deg + (uint64_t)tid * (n + 1);
            #pragma omp for schedule(static)
            for (uint32_t i = 0; i < m; i++) {
                uint32_t u = edges[3 * i];
                uint32_t p = my_pos[u]++;
                cols[p] = edges[3 * i + 1];
                weights[p] = edges[3 * i + 2];
            }
        }
        free(thread_deg);
    }

    // =========================================================
    // 2. 初始化
    // =========================================================
    #pragma omp parallel for schedule(static, 1024)
    for (uint32_t i = 0; i < n; i++) dis[i] = INF_CALC;
    dis[0] = 0;

    uint32_t factor = m / n;
    uint32_t delta = 200000;
    if (factor <= 5) {delta = 2000000000;}
    else if (factor <= 50) {delta = 200000;}
    else if (factor <= 500) {delta = 200000;}
    else if (factor <= 5000) {delta = 10000;}

    // =========================================================
    // 3. 并行 Delta-Stepping
    // =========================================================
    const uint32_t NUM_BUCKETS = 2048;
    std::vector<uint32_t> buckets[NUM_BUCKETS];
    buckets[0].push_back(0);

    uint64_t cur_bucket = 0;
    size_t alive = 1;

    uint32_t* frontier_curr = (uint32_t*)aligned_alloc(64, (m + n) * sizeof(uint32_t));
    uint32_t* frontier_next = (uint32_t*)aligned_alloc(64, (m + n) * sizeof(uint32_t));
    uint32_t curr_size = 0;
    uint32_t next_size = 0;

    struct LocalBuf {
        uint32_t q[8192];
        uint32_t head;
    };
    std::vector<LocalBuf> t_lights(T);
    std::vector<std::vector<std::pair<uint32_t, uint64_t>>> t_heavies(T);
    for(int i=0; i<T; ++i) t_heavies[i].reserve(4096);

    while (alive > 0) {
        uint32_t slot = cur_bucket % NUM_BUCKETS;
        if (buckets[slot].empty()) {
            cur_bucket++;
            continue;
        }

        // --- 并行提取当前桶节点 ---
        curr_size = 0;
        uint32_t b_size = buckets[slot].size();
        uint32_t* b_data = buckets[slot].data();
        
        #pragma omp parallel
        {
            int tid = omp_get_thread_num();
            uint32_t local_cnt = 0;
            static uint32_t* temp_f; 
            #pragma omp single
            temp_f = frontier_curr;

            std::vector<uint32_t> my_f; // 局部暂存
            #pragma omp for nowait
            for (uint32_t i = 0; i < b_size; i++) {
                uint32_t u = b_data[i];
                uint64_t b = dis[u] / delta;
                if (b == cur_bucket) my_f.push_back(u);
                else if (b > cur_bucket) {
                    // 只有主线程稍后处理 heavy 碰撞，或者这里加锁。
                    // 稀疏图中碰撞较少，由 single 线程处理
                }
            }
            if(!my_f.empty()) {
                uint32_t p = __atomic_fetch_add(&curr_size, (uint32_t)my_f.size(), __ATOMIC_RELAXED);
                memcpy(temp_f + p, my_f.data(), my_f.size() * sizeof(uint32_t));
            }
        }
        
        // 处理碰撞节点（b > cur_bucket 的节点留着下一次处理）
        std::vector<uint32_t> next_b;
        for (uint32_t u : buckets[slot]) {
            uint64_t b = dis[u] / delta;
            if (b > cur_bucket) next_b.push_back(u);
            else if (b < cur_bucket) alive--;
        }
        buckets[slot].swap(next_b);

        while (curr_size > 0) {
            alive -= curr_size;
            next_size = 0;

            #pragma omp parallel
            {
                int tid = omp_get_thread_num();
                auto& L = t_lights[tid];
                auto& H = t_heavies[tid];
                L.head = 0; H.clear();

                #pragma omp for schedule(dynamic, 128)
                for (uint32_t i = 0; i < curr_size; i++) {
                    uint32_t u = frontier_curr[i];
                    uint64_t du = dis[u];
                    uint32_t end = row_offset[u+1];
                    for (uint32_t e = row_offset[u]; e < end; e++) {
                        uint32_t v = cols[e];
                        uint64_t nd = du + weights[e];
                        if (nd < dis[v]) {
                            uint64_t old = __atomic_load_n(&dis[v], __ATOMIC_RELAXED);
                            while (nd < old) {
                                if (__atomic_compare_exchange_n(&dis[v], &old, nd, false, __ATOMIC_SEQ_CST, __ATOMIC_RELAXED)) {
                                    uint64_t b = nd / delta;
                                    if (b <= cur_bucket) {
                                        L.q[L.head++] = v;
                                        if (L.head == 8192) {
                                            uint32_t p = __atomic_fetch_add(&next_size, 8192, __ATOMIC_RELAXED);
                                            memcpy(frontier_next + p, L.q, 8192 * sizeof(uint32_t));
                                            L.head = 0;
                                        }
                                    } else H.emplace_back(v, b);
                                    break;
                                }
                            }
                        }
                    }
                }
                if (L.head > 0) {
                    uint32_t p = __atomic_fetch_add(&next_size, L.head, __ATOMIC_RELAXED);
                    memcpy(frontier_next + p, L.q, L.head * sizeof(uint32_t));
                }
            }

            for (int t = 0; t < T; t++) {
                if (!t_heavies[t].empty()) {
                    alive += t_heavies[t].size();
                    for (auto& p : t_heavies[t])
                        buckets[p.second % NUM_BUCKETS].push_back(p.first);
                }
            }
            alive += next_size;
            curr_size = next_size;
            std::swap(frontier_curr, frontier_next);
        }
        cur_bucket++;
    }

    #pragma omp parallel for schedule(static, 1024)
    for (uint32_t i = 0; i < n; i++) if (dis[i] >= INF_CALC) dis[i] = INF_OUTPUT;

    free(row_offset); free(cols); free(weights);
    free(frontier_curr); free(frontier_next);
}