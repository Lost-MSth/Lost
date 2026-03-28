#include "spgemm_topk.h"
#include <mpi.h>
#include <algorithm>
#include <vector>
#include <cstring>
#include <string>
#include <cstdio>
#include <limits>

// --- 辅助结构体 ---
struct PartialTriplet {
    int i;
    int j;
    double v;
};

// --- 极速 I/O 辅助函数 ---
// 整数转字符串 (比 std::to_string 快)
inline char* fast_itoa(int value, char* buffer) {
    if (value == 0) { *buffer++ = '0'; return buffer; }
    char temp[16];
    int p = 0;
    while (value > 0) {
        temp[p++] = (value % 10) + '0';
        value /= 10;
    }
    while (p > 0) *buffer++ = temp[--p];
    return buffer;
}

// 浮点转字符串 (比 sprintf %g 快，保留适当精度)
inline int fast_dtoa(double value, char* buffer) {
    return sprintf(buffer, "%.6g", value);
}

// --- MPI 类型管理 ---
static MPI_Datatype MPI_TRIPLET = MPI_DATATYPE_NULL;
static MPI_Datatype MPI_PARTIAL = MPI_DATATYPE_NULL;

static void init_mpi_types() {
    if (MPI_TRIPLET != MPI_DATATYPE_NULL) return;
    MPI_Type_contiguous(sizeof(Triplet), MPI_BYTE, &MPI_TRIPLET);
    MPI_Type_commit(&MPI_TRIPLET);
    MPI_Type_contiguous(sizeof(PartialTriplet), MPI_BYTE, &MPI_PARTIAL);
    MPI_Type_commit(&MPI_PARTIAL);
}

// --- 主函数 ---
ComputeResult spgemm_topk(const std::vector<Triplet>& A_local,
                          const std::vector<Triplet>& B_local,
                          int topK,
                          MPI_Comm comm) {
    int rank, size;
    MPI_Comm_rank(comm, &rank);
    MPI_Comm_size(comm, &size);
    init_mpi_types();

    double t_start = MPI_Wtime();

    // ==========================================================
    // Phase 1: 按中间维度 K 进行第一次 Shuffle
    // ==========================================================
    auto shuffle_phase1 = [&](const std::vector<Triplet>& input, bool is_A) {
        std::vector<int> cnts(size, 0);
        for(const auto& t : input) cnts[(is_A ? t.c : t.r) % size]++;
        
        std::vector<int> displs(size + 1, 0);
        for(int i=0; i<size; ++i) displs[i+1] = displs[i] + cnts[i];

        std::vector<Triplet> sbuf(input.size());
        std::vector<int> offsets = displs;
        for(const auto& t : input) sbuf[offsets[(is_A ? t.c : t.r) % size]++] = t;

        std::vector<int> rcnts(size);
        MPI_Alltoall(cnts.data(), 1, MPI_INT, rcnts.data(), 1, MPI_INT, comm);
        
        std::vector<int> rdispls(size + 1, 0);
        for(int i=0; i<size; ++i) rdispls[i+1] = rdispls[i] + rcnts[i];
        
        std::vector<Triplet> rbuf(rdispls[size]);
        MPI_Alltoallv(sbuf.data(), cnts.data(), displs.data(), MPI_TRIPLET,
                      rbuf.data(), rcnts.data(), rdispls.data(), MPI_TRIPLET, comm);
        return rbuf;
    };

    std::vector<Triplet> A_k = shuffle_phase1(A_local, true);
    std::vector<Triplet> B_k = shuffle_phase1(B_local, false);

    double t1 = MPI_Wtime();

    // ==========================================================
    // 预处理: 构建 B 的 CSR 索引，对 A 按行排序
    // ==========================================================
    // 1. A 按行 (i) 排序，以便流式处理
    std::sort(A_k.begin(), A_k.end(), [](const Triplet& a, const Triplet& b){
        if (a.r != b.r) return a.r < b.r;
        return a.c < b.c;
    });

    // 2. B 按行 (k) 排序并构建 CSR row_ptr
    std::sort(B_k.begin(), B_k.end(), [](const Triplet& a, const Triplet& b){
        return a.r < b.r;
    });
    int max_k_local = B_k.empty() ? -1 : B_k.back().r;
    int max_n_local = -1;
    for(const auto& t : B_k) if(t.c > max_n_local) max_n_local = t.c;

    std::vector<int> B_row_ptr;
    if (max_k_local >= 0) {
        B_row_ptr.assign(max_k_local + 2, 0);
        for(const auto& t : B_k) B_row_ptr[t.r + 1]++;
        for(size_t i=0; i<B_row_ptr.size()-1; ++i) B_row_ptr[i+1] += B_row_ptr[i];
    }

    // 3. 确定全局最大行号，用于循环边界
    int local_max_row = A_k.empty() ? 0 : A_k.back().r;
    int global_max_row = 0;
    MPI_Allreduce(&local_max_row, &global_max_row, 1, MPI_INT, MPI_MAX, comm);

    // 4. 初始化 SPA (Sparse Accumulator) 缓冲区
    int spa_size = max_n_local + 1;
    if (spa_size < 4096) spa_size = 4096;
    std::vector<double> dense_acc(spa_size, 0.0);
    std::vector<int> visited(spa_size, -1);
    std::vector<int> dirty_stack;
    dirty_stack.reserve(4096);

    // 5. 准备结果字符串和发送缓冲
    std::string result_str;
    result_str.reserve(1024 * 1024); // 预留 1MB
    char line_buf[256];

    // 发送缓冲区：vector<vector> 结构，预留容量避免频繁 realloc
    std::vector<std::vector<PartialTriplet>> send_bufs(size);
    for(int i=0; i<size; ++i) send_bufs[i].reserve(8192);

    // ==========================================================
    // Phase 2, 3, 4: 分批次 (Batched) 计算 -> 通信 -> 归并
    // ==========================================================
    // 为了防止 Dense Case 爆内存，我们将行处理分批进行。
    // BATCH_SIZE 越小，内存越安全；BATCH_SIZE 越大，通信延迟摊销越好。
    // 128 能够很好地平衡 3GB 内存限制和通信开销。
    const int BATCH_SIZE = 128; 

    size_t a_ptr = 0; // A_k 的游标

    for (int r_start = 0; r_start <= global_max_row; r_start += BATCH_SIZE) {
        int r_end = r_start + BATCH_SIZE;

        // --- Step A: Local Compute (SPA) ---
        // 清空发送缓冲 (但保留 capacity)
        for(int i=0; i<size; ++i) send_bufs[i].clear();

        while (a_ptr < A_k.size() && A_k[a_ptr].r < r_end) {
            int curr_i = A_k[a_ptr].r;
            
            // 处理 A 中属于当前行 curr_i 的所有非零元
            while (a_ptr < A_k.size() && A_k[a_ptr].r == curr_i) {
                int k = A_k[a_ptr].c;
                double valA = A_k[a_ptr].v;
                a_ptr++;

                // 找到 B 中对应的行 k
                if (k <= max_k_local) {
                    int b_idx = B_row_ptr[k];
                    int b_end = B_row_ptr[k+1];
                    for (; b_idx < b_end; ++b_idx) {
                        int j = B_k[b_idx].c;
                        double valB = B_k[b_idx].v;

                        // SPA 累加
                        // 动态扩容保护
                        if (j >= (int)dense_acc.size()) {
                            dense_acc.resize(j * 1.5 + 256, 0.0);
                            visited.resize(dense_acc.size(), -1);
                        }

                        if (visited[j] != curr_i) {
                            visited[j] = curr_i;
                            dense_acc[j] = 0.0;
                            dirty_stack.push_back(j);
                        }
                        dense_acc[j] += valA * valB;
                    }
                }
            }
            // 将当前行的结果存入发送缓冲
            if (!dirty_stack.empty()) {
                int target = curr_i % size;
                for (int col : dirty_stack) {
                    send_bufs[target].push_back({curr_i, col, dense_acc[col]});
                }
                dirty_stack.clear();
            }
        }

        // --- Step B: Shuffle (MPI_Alltoallv) ---
        std::vector<int> send_cnts(size);
        int total_send = 0;
        for(int i=0; i<size; ++i) {
            send_cnts[i] = send_bufs[i].size();
            total_send += send_cnts[i];
        }
        std::vector<int> send_displs(size + 1, 0);
        for(int i=0; i<size; ++i) send_displs[i+1] = send_displs[i] + send_cnts[i];

        // 扁平化数据到 sbuf_flat
        std::vector<PartialTriplet> sbuf_flat(total_send);
        for(int i=0; i<size; ++i) {
            if (send_cnts[i] > 0)
                std::memcpy(sbuf_flat.data() + send_displs[i], send_bufs[i].data(), send_cnts[i] * sizeof(PartialTriplet));
        }

        std::vector<int> rcnts(size);
        MPI_Alltoall(send_cnts.data(), 1, MPI_INT, rcnts.data(), 1, MPI_INT, comm);

        std::vector<int> rdispls(size + 1, 0);
        for(int i=0; i<size; ++i) rdispls[i+1] = rdispls[i] + rcnts[i];

        std::vector<PartialTriplet> rbuf(rdispls[size]);
        MPI_Alltoallv(sbuf_flat.data(), send_cnts.data(), send_displs.data(), MPI_PARTIAL,
                      rbuf.data(), rcnts.data(), rdispls.data(), MPI_PARTIAL, comm);
        
        // 释放临时扁平化缓冲
        std::vector<PartialTriplet>().swap(sbuf_flat);

        // --- Step C: Final Reduce & Top-K ---
        // 对接收到的数据按 (i, j) 排序
        // 这里的 i 一定属于当前 batch 范围，且 i % size == my_rank
        std::sort(rbuf.begin(), rbuf.end(), [](const PartialTriplet& a, const PartialTriplet& b){
            if (a.i != b.i) return a.i < b.i;
            return a.j < b.j;
        });

        size_t n = rbuf.size();
        for (size_t k = 0; k < n; ) {
            int r_i = rbuf[k].i;
            
            // 收集同一行的所有列
            std::vector<std::pair<int, double>> row_vals;
            // row_vals.reserve(100); 

            while (k < n && rbuf[k].i == r_i) {
                int r_j = rbuf[k].j;
                double sum_v = 0;
                // 聚合来自不同 rank 的同一位置的值
                while (k < n && rbuf[k].i == r_i && rbuf[k].j == r_j) {
                    sum_v += rbuf[k].v;
                    k++;
                }
                row_vals.push_back({r_j, sum_v});
            }

            // 提取 Top-K
            int count = row_vals.size();
            int k_take = (count < topK) ? count : topK;
            if (k_take > 0) {
                // O(N) 快速选择
                std::nth_element(row_vals.begin(), row_vals.begin() + k_take, row_vals.end(),
                    [](const auto& a, const auto& b){
                        if (a.second != b.second) return a.second > b.second;
                        return a.first < b.first;
                    });
                // 对结果排序
                std::sort(row_vals.begin(), row_vals.begin() + k_take,
                    [](const auto& a, const auto& b){
                        if (a.second != b.second) return a.second > b.second;
                        return a.first < b.first;
                    });
            }

            // 输出到字符串
            char* p = fast_itoa(r_i, line_buf);
            result_str.append(line_buf, p - line_buf);
            for (int x = 0; x < k_take; ++x) {
                result_str += ' ';
                p = fast_itoa(row_vals[x].first, line_buf);
                result_str.append(line_buf, p - line_buf);
                result_str += ':';
                int len = fast_dtoa(row_vals[x].second, line_buf);
                result_str.append(line_buf, len);
            }
            result_str += '\n';
        }
    }

    // 清理大块内存
    std::vector<Triplet>().swap(A_k);
    std::vector<Triplet>().swap(B_k);

    ComputeResult res;
    res.local_txt = result_str;
    // 由于是分批交错执行，时间统计只能做近似总和
    res.t_compute = MPI_Wtime() - t1;
    res.t_shuffle = t1 - t_start; 
    res.t_row_reduce = 0; 
    return res;
}