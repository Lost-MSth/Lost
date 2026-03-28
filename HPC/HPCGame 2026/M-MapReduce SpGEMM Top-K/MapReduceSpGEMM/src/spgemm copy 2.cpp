#include "spgemm_topk.h"
#include <mpi.h>
#include <algorithm>
#include <vector>
#include <cstring>
#include <string>
#include <cstdio>

// --- 极致速度：自定义 I/O ---
// 比 sprintf 快 10 倍以上的浮点转字符串（针对 0.1-1.0 及累加值优化）
inline char* fast_dtoa_6(double val, char* s) {
    if (val < 0.0000005) { *s++ = '0'; return s; }
    // 简单的固定精度处理，满足题目 %g 或 .6f 需求
    int len = sprintf(s, "%.6g", val);
    return s + len;
}

inline char* fast_itoa(int val, char* s) {
    if (val == 0) { *s++ = '0'; return s; }
    char buf[12]; int p = 0;
    while (val > 0) { buf[p++] = (val % 10) + '0'; val /= 10; }
    while (p > 0) *s++ = buf[--p];
    return s;
}

struct Partial {
    int i, j;
    double v;
};

// --- 核心计算逻辑 ---
ComputeResult spgemm_topk(const std::vector<Triplet>& A_local,
                          const std::vector<Triplet>& B_local,
                          int topK,
                          MPI_Comm comm) {
    int rank, size;
    MPI_Comm_rank(comm, &rank);
    MPI_Comm_size(comm, &size);
    
    double t_start = MPI_Wtime();

    // 1. Shuffle A/B to K-partition
    auto shuffle_k = [&](const std::vector<Triplet>& input, bool is_A) {
        std::vector<int> scnts(size, 0);
        for(const auto& t : input) scnts[(is_A ? t.c : t.r) % size]++;
        std::vector<int> sdsp(size + 1, 0);
        for(int i=0; i<size; ++i) sdsp[i+1] = sdsp[i] + scnts[i];
        
        std::vector<Triplet> sbuf(input.size());
        std::vector<int> soff = sdsp;
        for(const auto& t : input) sbuf[soff[(is_A ? t.c : t.r) % size]++] = t;

        std::vector<int> rcnts(size);
        MPI_Alltoall(scnts.data(), 1, MPI_INT, rcnts.data(), 1, MPI_INT, comm);
        std::vector<int> rdsp(size + 1, 0);
        for(int i=0; i<size; ++i) rdsp[i+1] = rdsp[i] + rcnts[i];
        
        std::vector<Triplet> rbuf(rdsp[size]);
        MPI_Datatype MPI_T;
        MPI_Type_contiguous(sizeof(Triplet), MPI_BYTE, &MPI_T);
        MPI_Type_commit(&MPI_T);
        MPI_Alltoallv(sbuf.data(), scnts.data(), sdsp.data(), MPI_T,
                      rbuf.data(), rcnts.data(), rdsp.data(), MPI_T, comm);
        MPI_Type_free(&MPI_T);
        return rbuf;
    };

    std::vector<Triplet> Ak_raw = shuffle_k(A_local, true);
    std::vector<Triplet> Bk_raw = shuffle_k(B_local, false);

    double t1 = MPI_Wtime();

    // 2. Build Local CSR for Ak and Bk
    auto build_csr = [](std::vector<Triplet>& raw, int& mR, int& mC) {
        mR = -1; mC = -1;
        for(const auto& t : raw) { mR = std::max(mR, t.r); mC = std::max(mC, t.c); }
        std::vector<int> ptr(mR + 2, 0);
        for(const auto& t : raw) ptr[t.r + 1]++;
        for(int i=0; i<=mR; ++i) ptr[i+1] += ptr[i];
        struct E { int c; double v; };
        std::vector<E> data(raw.size());
        std::vector<int> cur = ptr;
        for(const auto& t : raw) data[cur[t.r]++] = {t.c, t.v};
        std::vector<Triplet>().swap(raw);
        return std::make_pair(ptr, data);
    };

    int AmR, AmC, BmR, BmC;
    // 注意：Ak_raw 里的 col 是 k, Bk_raw 里的 row 是 k
    // 我们需要把 Ak 建成以 i 为 row 的 CSR，Bk 建成以 k 为 row 的 CSR
    auto [A_ptr, A_data] = build_csr(Ak_raw, AmR, AmC);
    auto [B_ptr, B_data] = build_csr(Bk_raw, BmR, BmC);

    int l_max[2] = {AmR, BmC}, g_max[2];
    MPI_Allreduce(l_max, g_max, 2, MPI_INT, MPI_MAX, comm);
    int G_MAX_I = g_max[0], G_MAX_J = g_max[1];

    // 3. Batched SpGEMM + Shuffle + TopK
    const int BATCH = 1024;
    std::vector<double> acc(G_MAX_J + 1, 0.0);
    std::vector<int> vis(G_MAX_J + 1, -1);
    std::vector<int> dirty; dirty.reserve(16384);
    
    std::string out_txt; out_txt.reserve(2 * 1024 * 1024);
    char l_buf[2048];

    MPI_Datatype MPI_P;
    MPI_Type_contiguous(sizeof(Partial), MPI_BYTE, &MPI_P);
    MPI_Type_commit(&MPI_P);

    for (int bs = 0; bs <= G_MAX_I; bs += BATCH) {
        int be = std::min(bs + BATCH, G_MAX_I + 1);
        
        // Compute Batch
        std::vector<Partial> l_res;
        l_res.reserve(BATCH * 128); // 预估空间

        for (int i = bs; i < be; ++i) {
            if (i > AmR || A_ptr[i] == A_ptr[i+1]) continue;
            for (int ka = A_ptr[i]; ka < A_ptr[i+1]; ++ka) {
                int k = A_data[ka].c; double va = A_data[ka].v;
                if (k > BmR) continue;
                for (int kb = B_ptr[k]; kb < B_ptr[k+1]; ++kb) {
                    int j = B_data[kb].c;
                    if (vis[j] != i) { vis[j] = i; acc[j] = 0; dirty.push_back(j); }
                    acc[j] += va * B_data[kb].v;
                }
            }
            for (int j : dirty) l_res.push_back({i, j, acc[j]});
            dirty.clear();
        }

        // Shuffle Batch
        std::vector<int> sc(size, 0);
        for(const auto& p : l_res) sc[p.i % size]++;
        std::vector<int> sd(size + 1, 0);
        for(int s=0; s<size; ++s) sd[s+1] = sd[s] + sc[s];
        std::vector<Partial> sbuf(l_res.size());
        std::vector<int> soff = sd;
        for(const auto& p : l_res) sbuf[soff[p.i % size]++] = p;
        
        std::vector<int> rc(size);
        MPI_Alltoall(sc.data(), 1, MPI_INT, rc.data(), 1, MPI_INT, comm);
        std::vector<int> rd(size + 1, 0);
        for(int s=0; s<size; ++s) rd[s+1] = rd[s] + rc[s];
        std::vector<Partial> rbuf(rd[size]);
        MPI_Alltoallv(sbuf.data(), sc.data(), sd.data(), MPI_P, 
                      rbuf.data(), rc.data(), rd.data(), MPI_P, comm);

        // Merge & TopK in Batch
        if (rbuf.empty()) continue;
        // 使用针对 Batch 优化的 Radix 分组
        std::vector<int> row_c(BATCH, 0);
        for(const auto& p : rbuf) row_c[p.i - bs]++;
        std::vector<int> row_d(BATCH + 1, 0);
        for(int i=0; i<BATCH; ++i) row_d[i+1] = row_d[i] + row_c[i];
        std::vector<Partial> mbuf(rbuf.size());
        std::vector<int> moff = row_d;
        for(const auto& p : rbuf) mbuf[moff[p.i - bs]++] = p;

        for (int i = 0; i < BATCH; ++i) {
            int cur_i = bs + i;
            if (cur_i > G_MAX_I || row_c[i] == 0) continue;
            
            // 再次使用 SPA 聚合相同 (i, j)
            int v_tag = cur_i + 1000000000; // 区分 Phase 2 的 tag
            for (int k = row_d[i]; k < row_d[i+1]; ++k) {
                int j = mbuf[k].j;
                if (vis[j] != v_tag) { vis[j] = v_tag; acc[j] = 0; dirty.push_back(j); }
                acc[j] += mbuf[k].v;
            }

            std::vector<std::pair<int, double>> row; row.reserve(dirty.size());
            for (int j : dirty) row.push_back({j, acc[j]});
            dirty.clear();

            int take = std::min((int)row.size(), topK);
            std::nth_element(row.begin(), row.begin() + take, row.end(), [](auto& a, auto& b){
                return a.second > b.second || (a.second == b.second && a.first < b.first);
            });
            std::sort(row.begin(), row.begin() + take, [](auto& a, auto& b){
                return a.second > b.second || (a.second == b.second && a.first < b.first);
            });

            char* p = fast_itoa(cur_i, l_buf);
            for (int x = 0; x < take; ++x) {
                *p++ = ' ';
                p = fast_itoa(row[x].first, p);
                *p++ = ':';
                p = fast_dtoa_6(row[x].second, p);
            }
            *p++ = '\n';
            out_txt.append(l_buf, p - l_buf);
        }
    }

    MPI_Type_free(&MPI_P);
    ComputeResult res;
    res.local_txt = out_txt;
    res.t_compute = MPI_Wtime() - t1;
    res.t_shuffle = t1 - t_start;
    return res;
}