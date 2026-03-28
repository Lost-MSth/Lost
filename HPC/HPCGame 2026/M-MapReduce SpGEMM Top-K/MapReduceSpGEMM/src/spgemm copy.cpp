#include "spgemm_topk.h"
#include <mpi.h>
#include <algorithm>
#include <vector>
#include <cstring>
#include <string>
#include <cstdio>
#include <limits>

// --- 辅助结构 ---
struct PartialTriplet {
    int i;
    int j;
    double v;
};

// --- 极速 I/O ---
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

inline int fast_dtoa(double value, char* buffer) {
    return sprintf(buffer, "%.6g", value);
}

// --- MPI 类型 ---
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
    // Phase 1: Shuffle (A by col, B by row)
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
    // 预处理: 索引构建与全局信息获取
    // ==========================================================
    // 1. A 按行排序
    std::sort(A_k.begin(), A_k.end(), [](const Triplet& a, const Triplet& b){
        if (a.r != b.r) return a.r < b.r;
        return a.c < b.c;
    });

    // 2. B 按行排序并构建 CSR
    std::sort(B_k.begin(), B_k.end(), [](const Triplet& a, const Triplet& b){
        return a.r < b.r;
    });
    
    int max_k_local = B_k.empty() ? -1 : B_k.back().r;
    int local_max_n = -1;
    for(const auto& t : B_k) if(t.c > local_max_n) local_max_n = t.c;

    std::vector<int> B_row_ptr;
    if (max_k_local >= 0) {
        B_row_ptr.assign(max_k_local + 2, 0);
        for(const auto& t : B_k) B_row_ptr[t.r + 1]++;
        for(size_t i=0; i<B_row_ptr.size()-1; ++i) B_row_ptr[i+1] += B_row_ptr[i];
    }

    // 3. 获取全局最大行号和最大列号 (用于 SPA 大小)
    int local_max_row = A_k.empty() ? 0 : A_k.back().r;
    int global_max_row = 0;
    int global_max_col = 0;
    
    // 两个 reduce 合并做一个
    int local_maxes[2] = {local_max_row, local_max_n};
    int global_maxes[2] = {0, 0};
    MPI_Allreduce(local_maxes, global_maxes, 2, MPI_INT, MPI_MAX, comm);
    global_max_row = global_maxes[0];
    global_max_col = global_maxes[1];

    // ==========================================================
    // 内存池预分配
    // ==========================================================
    // SPA (用于 Phase 2 和 Phase 4)
    // 确保大小足以容纳全局最大的列 j
    int spa_size = global_max_col + 1;
    if (spa_size < 4096) spa_size = 4096;
    std::vector<double> dense_acc(spa_size, 0.0);
    std::vector<int> visited(spa_size, -1);
    std::vector<int> dirty_stack;
    dirty_stack.reserve(8192);

    // 发送缓冲区 Phase 2 -> 3
    std::vector<std::vector<PartialTriplet>> send_bufs(size);
    for(int i=0; i<size; ++i) send_bufs[i].reserve(16384);

    // Phase 4 归并用的辅助结构
    // 增大 Batch Size 以摊销 MPI 延迟
    const int BATCH_SIZE = 512;
    std::vector<PartialTriplet> merge_buf; // 用于 Radix Sort 的临时 buffer
    merge_buf.reserve(BATCH_SIZE * 1024);  // 预估大小
    std::vector<int> batch_row_counts(BATCH_SIZE, 0);
    std::vector<int> batch_row_offsets(BATCH_SIZE + 1, 0);
    std::vector<std::pair<int, double>> row_candidates; // Top-K 候选
    row_candidates.reserve(4096);

    // 输出字符串缓冲
    std::string result_str;
    result_str.reserve(2 * 1024 * 1024);
    char line_buf[512];

    size_t a_ptr = 0;

    // ==========================================================
    // Batched Pipeline Loop
    // ==========================================================
    for (int r_start = 0; r_start <= global_max_row; r_start += BATCH_SIZE) {
        int r_end = r_start + BATCH_SIZE;

        // --- Step A: Local Compute (SPA) ---
        for(int i=0; i<size; ++i) send_bufs[i].clear();

        while (a_ptr < A_k.size() && A_k[a_ptr].r < r_end) {
            int curr_i = A_k[a_ptr].r;
            
            while (a_ptr < A_k.size() && A_k[a_ptr].r == curr_i) {
                int k = A_k[a_ptr].c;
                double valA = A_k[a_ptr].v;
                a_ptr++;

                if (k <= max_k_local) {
                    int b_idx = B_row_ptr[k];
                    int b_end = B_row_ptr[k+1];
                    for (; b_idx < b_end; ++b_idx) {
                        int j = B_k[b_idx].c;
                        // 这里不需要检查 j >= dense_acc.size()，因为我们按 global_max_col 分配了
                        
                        if (visited[j] != curr_i) {
                            visited[j] = curr_i;
                            dense_acc[j] = 0.0;
                            dirty_stack.push_back(j);
                        }
                        dense_acc[j] += valA * B_k[b_idx].v;
                    }
                }
            }

            if (!dirty_stack.empty()) {
                int target = curr_i % size;
                auto& buf = send_bufs[target];
                for (int col : dirty_stack) {
                    buf.push_back({curr_i, col, dense_acc[col]});
                }
                dirty_stack.clear();
            }
        }

        // --- Step B: Shuffle ---
        std::vector<int> send_cnts(size);
        int total_send = 0;
        for(int i=0; i<size; ++i) {
            send_cnts[i] = send_bufs[i].size();
            total_send += send_cnts[i];
        }
        std::vector<int> send_displs(size + 1, 0);
        for(int i=0; i<size; ++i) send_displs[i+1] = send_displs[i] + send_cnts[i];

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
        
        // 释放扁平缓冲
        if (sbuf_flat.capacity() > 10000000) std::vector<PartialTriplet>().swap(sbuf_flat);

        // --- Step C: Optimized Merge & Top-K (Radix Partition + SPA) ---
        if (rbuf.empty()) continue;

        // 1. Radix Partition: 将 rbuf 按行号 i 分桶到 merge_buf
        // 这里的 i 范围是 [r_start, r_end)
        std::fill(batch_row_counts.begin(), batch_row_counts.end(), 0);
        
        for (const auto& t : rbuf) {
            batch_row_counts[t.i - r_start]++;
        }
        
        batch_row_offsets[0] = 0;
        for (int i = 0; i < BATCH_SIZE; ++i) {
            batch_row_offsets[i+1] = batch_row_offsets[i] + batch_row_counts[i];
        }

        // 避免每次都 resize
        if (merge_buf.size() < rbuf.size()) merge_buf.resize(rbuf.size());
        
        // 分发数据
        // 注意：这里复用 batch_row_offsets 作为写入游标
        for (const auto& t : rbuf) {
            int offset_idx = t.i - r_start;
            merge_buf[batch_row_offsets[offset_idx]++] = t;
        }
        // 恢复 offsets (右移一位得到起始位置)
        for (int i = BATCH_SIZE; i > 0; --i) batch_row_offsets[i] = batch_row_offsets[i-1];
        batch_row_offsets[0] = 0;

        // 2. 逐行处理
        for (int i = 0; i < BATCH_SIZE; ++i) {
            int count = batch_row_counts[i];
            if (count == 0) continue;
            
            int r_abs = r_start + i;
            if (r_abs % size != rank) continue; // 理论上 rbuf 只包含发给我的数据，但这层检查无害

            int start_idx = batch_row_offsets[i];
            int end_idx = start_idx + count;

            // 使用 SPA 进行聚合 (Reuse dense_acc)
            // 这里的 generation id 使用 (r_abs + 1) * -1 或者其他的，避免和 Phase 2 冲突
            // Phase 2 用的是正数 visited[j] = curr_i.
            // Phase 4 用负数 visited[j] = -r_abs - 2.
            int visit_tag = -r_abs - 2;

            for (int k = start_idx; k < end_idx; ++k) {
                int col = merge_buf[k].j;
                double val = merge_buf[k].v;

                if (visited[col] != visit_tag) {
                    visited[col] = visit_tag;
                    dense_acc[col] = 0.0;
                    dirty_stack.push_back(col);
                }
                dense_acc[col] += val;
            }

            // 收集结果
            row_candidates.clear();
            for (int col : dirty_stack) {
                row_candidates.push_back({col, dense_acc[col]});
            }
            dirty_stack.clear();

            // Top-K
            int k_avail = row_candidates.size();
            int k_take = (k_avail < topK) ? k_avail : topK;

            if (k_take > 0) {
                std::nth_element(row_candidates.begin(), row_candidates.begin() + k_take, row_candidates.end(),
                    [](const auto& a, const auto& b){
                        if (a.second != b.second) return a.second > b.second;
                        return a.first < b.first;
                    });
                std::sort(row_candidates.begin(), row_candidates.begin() + k_take,
                    [](const auto& a, const auto& b){
                        if (a.second != b.second) return a.second > b.second;
                        return a.first < b.first;
                    });
            }

            // 输出
            char* p = fast_itoa(r_abs, line_buf);
            result_str.append(line_buf, p - line_buf);
            for (int x = 0; x < k_take; ++x) {
                result_str += ' ';
                p = fast_itoa(row_candidates[x].first, line_buf);
                result_str.append(line_buf, p - line_buf);
                result_str += ':';
                int len = fast_dtoa(row_candidates[x].second, line_buf);
                result_str.append(line_buf, len);
            }
            result_str += '\n';
        }
    }

    // 清理
    std::vector<Triplet>().swap(A_k);
    std::vector<Triplet>().swap(B_k);

    ComputeResult res;
    res.local_txt = result_str;
    res.t_compute = MPI_Wtime() - t1; // 简化统计
    res.t_shuffle = t1 - t_start;
    res.t_row_reduce = 0;
    return res;
}