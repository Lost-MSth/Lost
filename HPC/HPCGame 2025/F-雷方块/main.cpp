#include <assert.h>
// #include <inttypes.h>  // int64_t
#include <bits/stdc++.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

#include <array>
#include <bitset>
#include <cstdint>
#include <functional>
// #include <unordered_map>
#include <immintrin.h>

#include <vector>

#define MAX_N 1025

typedef uint8_t u8;
// typedef int64_t i64;
typedef uint64_t u64;
typedef uint32_t u32;
// typedef int32_t i32;
typedef signed char i8;

// typedef std::map<int, i8> ColMap;
// typedef std::unordered_map<int, i8> ColMap;

typedef std::bitset<MAX_N> ARR;

struct SparseMatrix {
    int n;
    std::vector<int> row;
    std::vector<int> col;
    std::vector<uint8_t> val;
};

struct SparseMatrixRow {
    int n;                              // 矩阵的行数、列数
    std::vector<int> row;               // 每一行的行号，用于行交换
    std::vector<std::vector<int>> col;  // 每一行的列索引
    std::vector<std::vector<i8>> val;   // 每一行的值
    // std::vector<ColMap> col_val;  // 每一行的列索引和值
    std::vector<int> nnz_col;  // 每一行的第一个非零列索引
    // std::vector<std::array<i8, MAX_N>> arr;  // 每一行从第一个非零列开始的值
    // <std::bitset<MAX_N * 2>>
    //     arr;  // 每一行从第一个非零列开始的值，每个元素是 2 位
    std::vector<ARR> first;   // 非 0 控制位
    std::vector<ARR> second;  // 1 / 2 控制位，0 表示 1，1 表示 2
};

inline void set_ele(ARR &first, ARR &second, int idx, u8 val) {
    assert(val == 0 || val == 1 || val == 2);
    first[idx] = val != 0;
    second[idx] = val == 2;
}

inline u8 get_ele(const ARR &first, const ARR &second, int idx) {
    u8 x = first[idx] ? (second[idx] + 1) : 0;
    assert(x == 0 || x == 1 || x == 2);
    return x;
}

inline bool get_factor(u8 factor, u8 pivot) {
    if (pivot == 1) {
        return factor == 1;
    } else {
        return factor == 2;
    }
}

inline u8 mod3(u8 a) {
    // a = -2 ~ 2
    if (a == 3) {
        return 0;
    } else if (a == 4) {
        return 1;
    } else {
        return a;
    }
}

inline u8 sub(u8 a, u8 b, bool factor) {
    // a, b in {2, 1, 0}
    // factor = true: a - b
    if (factor) {
        if (b >= a) {
            return mod3(3 + a - b);
        } else {
            return mod3(a - b);
        }
    } else {
        return mod3(a + b);
    }
}

// inline int find_nnz(const std::vector<int> &col, int idx) {
//     for (int i = 0; i < col.size(); i++) {
//         if (col[i] == idx) return i;
//     }
//     return -1;
// }

inline void bit_add(ARR &a1, ARR &a2, const ARR &b1, const ARR &b2) {
    // ARR nonzero = a1 & b1;  // 两个都是非零

    // // ARR a2_b2 = ;
    // a1 = (nonzero & ~(a2 ^ b2)) | (~nonzero & (a1 ^ b1));
    // a2 = (nonzero & ~(a2 | b2)) | (~nonzero & (a2 ^ b2));

    char *a1_ptr = (char *)&a1;
    char *a2_ptr = (char *)&a2;
    const char *b1_ptr = (const char *)&b1;
    const char *b2_ptr = (const char *)&b2;

    __m128i *a1_ptr_sse = (__m128i *)a1_ptr;
    __m128i *a2_ptr_sse = (__m128i *)a2_ptr;
    const __m128i *b1_ptr_sse = (const __m128i *)b1_ptr;
    const __m128i *b2_ptr_sse = (const __m128i *)b2_ptr;

#pragma unroll
    for (int i = 0; i < MAX_N / 128; i++) {
        __m128i a1_val = _mm_loadu_si128(&a1_ptr_sse[i]);
        __m128i a2_val = _mm_loadu_si128(&a2_ptr_sse[i]);
        __m128i b1_val = _mm_loadu_si128(&b1_ptr_sse[i]);
        __m128i b2_val = _mm_loadu_si128(&b2_ptr_sse[i]);

        __m128i nonzero = _mm_and_si128(a1_val, b1_val);
        __m128i a2_b2 = _mm_xor_si128(a2_val, b2_val);
        __m128i a1_result = _mm_or_si128(
            _mm_andnot_si128(a2_b2, nonzero),
            _mm_andnot_si128(nonzero, _mm_xor_si128(a1_val, b1_val)));
        __m128i a2_result = _mm_or_si128(
            _mm_andnot_si128(_mm_or_si128(a2_val, b2_val), nonzero),
            _mm_andnot_si128(nonzero, a2_b2));
        _mm_storeu_si128(&a1_ptr_sse[i], a1_result);
        _mm_storeu_si128(&a2_ptr_sse[i], a2_result);
    }
    // 最后一个 1025
    auto nnz = a1[MAX_N - 1] & b1[MAX_N - 1];
    a1[MAX_N - 1] = (nnz & ~(a2[MAX_N - 1] ^ b2[MAX_N - 1])) |
                    (~nnz & (a1[MAX_N - 1] ^ b1[MAX_N - 1]));
    a2[MAX_N - 1] = (nnz & ~(a2[MAX_N - 1] | b2[MAX_N - 1])) |
                    (~nnz & (a2[MAX_N - 1] ^ b2[MAX_N - 1]));
}

inline int vec_sub(ARR &a1, ARR &a2, const ARR &b1, const ARR &b2,
                   bool factor) {
    // 注意：密集 bits
    // 注意 a1 a2 会被改

    // ARR tmp1;
    // ARR tmp2;

    if (factor) {
        // a - b
        // 按照 b1 反转 b2，注意 b1 也是 inv_b1
        bit_add(a1, a2, b1, b1 ^ b2);
    } else {
        // a + b
        bit_add(a1, a2, b1, b2);
    }

    // 找到第一个非零元素
    // int nnz_idx = tmp1._Find_first();
    int nnz_idx = a1._Find_first();
    // printf("nnz_idx = %d\n", nnz_idx);
    // assert(nnz_idx != MAX_N);

    // 重新赋值
    // a1 = tmp1 >> nnz_idx;
    // a2 = tmp2 >> nnz_idx;
    a1 >>= nnz_idx;
    a2 >>= nnz_idx;

    return nnz_idx;
}

void solve(SparseMatrixRow &A, std::vector<u8> &B, std::vector<u8> &X, int n1) {
    int n = A.n;
    // std::vector<int> row_idx = A.row;
    // std::vector<std::vector<int>> &col_idx = A.col;
    // std::vector<std::vector<i8>> &col_val = A.val;
    std::vector<int> &nnz_idx = A.nnz_col;
    // std::vector<std::array<i8, MAX_N>> &rows = A.arr;
    std::vector<ARR> &rows_first = A.first;
    std::vector<ARR> &rows_second = A.second;

    // 高斯消元 mod 3
    for (int i = 0; i < n; i++) {
        // 打印数组
        // for (int ii = 0; ii < n; ii++) {
        // 	for (int jj = 0; jj < nnz_idx[ii]; jj++) {
        // 		printf("  0");
        // 	}
        // 	for (int jj = nnz_idx[ii]; jj < MAX_N; jj++) {
        // 		if (jj >= n) break;
        // 		// printf("%3d", rows[ii][jj-nnz_idx[ii]]);
        // 		// printf("%3d", get_ele(rows[ii], jj - nnz_idx[ii]));
        // 		printf("%3d", get_ele(rows_first[ii], rows_second[ii],
        // jj - nnz_idx[ii]));
        // 	}
        // 	for (int jj = MAX_N; jj < n; jj++) {
        // 		printf("  0");
        // 	}
        // 	printf(" | %3d\n", B[ii]);
        // }
        // printf("\n");

        // 找到第 i 列的主元
        int j;
        int j_end = std::min(i + 1 + n1, n);
        for (j = i; j < j_end; j++) {
            // 直接看非零列号
            if (nnz_idx[j] != i) continue;
            if (i == j) break;

            // 交换行
            // std::swap(row_idx[i], row_idx[j]);
            // std::swap(col_idx[i], col_idx[j]);
            // std::swap(col_val[i], col_val[j]);
            std::swap(nnz_idx[i], nnz_idx[j]);
            std::swap(rows_first[i], rows_first[j]);
            std::swap(rows_second[i], rows_second[j]);
            std::swap(B[i], B[j]);
            break;
        }

        // printf("i = %d, j = %d\n", i, j);
        assert(j < j_end);

        // std::array<i8, MAX_N> &pivot_row = rows[i];
        // std::bitset<MAX_N * 2> &pivot_row = rows[i];
        ARR &pivot_row_first = rows_first[i];
        ARR &pivot_row_second = rows_second[i];
        // i8 pivot = pivot_row[0];
        u8 pivot = pivot_row_second[0] + 1;

        // assert(pivot == 1 || pivot == -1);

        int k_end = std::min(j + 2 + n1, n);
        // 消元
#pragma omp parallel for
        for (int k = j + 1; k < k_end; k++) {
            // std::vector<int> &col = col_idx[k];

            // 直接看非零列号
            if (nnz_idx[k] != i) continue;

            // 两个向量相减
            // 注意 nnz_idx 是需要加上偏移的
            // bool factor = get_factor(get_ele(rows[k], 0), pivot);
            bool factor = get_factor(rows_second[k][0] + 1, pivot);
            // nnz_idx[k] += vec_sub(rows[k], pivot_row, factor);
            nnz_idx[k] += vec_sub(rows_first[k], rows_second[k],
                                  pivot_row_first, pivot_row_second, factor);

            B[k] = sub(B[k], B[i], factor);
        }

        // 更新当前进度
        // if (i % 1000 == 0) {
        //     fprintf(stderr, "Progress: %d / %d\r", i, n);
        //     fflush(stderr);
        // }
    }

    // 回代
    for (int i = n - 1; i > 0; i--) {
        // i8 pivot = rows[i][0];
        // u8 pivot = get_ele(rows[i], 0);
        // u8 pivot = get_ele(rows_first[i], rows_second[i], 0);
        u8 pivot = rows_second[i][0] + 1;
        // assert(pivot == 1 || pivot == -1);

        int j_end = std::max(i - 2 * n1, 0);

        // #pragma omp parallel for schedule(static)
        for (int j = i - 1; j >= j_end; j--) {
            // 需要算一下偏移
            int col_i_idx = i - j;
            // i8 element = rows[j][col_i_idx];
            // u8 element = get_ele(rows[j], col_i_idx);
            // if (element == 0) continue;
            if (rows_first[j][col_i_idx] == 0) continue;

            // u8 element = get_ele(rows_first[j], rows_second[j], col_i_idx);
            u8 element = rows_second[j][col_i_idx] + 1;

            bool factor = get_factor(element, pivot);

            B[j] = sub(B[j], B[i], factor);
        }

        // 更新当前进度
        // if (i % 1000 == 0) {
        //     fprintf(stderr, "Progress: %d / %d\r", i, n);
        //     fflush(stderr);
        // }
    }

    // 解
#pragma omp parallel for schedule(static)
    for (int i = 0; i < n; i++) {
        // i8 pivot = rows[i][0];
        // u8 pivot = get_ele(rows_first[i], rows_second[i], 0);
        u8 pivot = rows_second[i][0] + 1;
        // int idx = row_idx[i];
        if (pivot == 1) {
            X[i] = B[i];
        } else {
            X[i] = (3 - B[i]) % 3;
        }
    }
}

inline size_t idx(int i, int j, int n) { return i * n + j; }

void init_matrix(int *m, SparseMatrix &A, std::vector<uint8_t> &b,
                 std::vector<int> &nnz_idx, int n1, int n2) {
    std::vector<int> idx2nnzidx(n1 * n2, -1);

    for (int i = 0; i < n1 * n2; i++) {
        if (m[i] == 0) continue;
        b[i] = 3 - m[i];
        nnz_idx.push_back(i);
        idx2nnzidx[i] = nnz_idx.size() - 1;
    }

    for (int i = 0; i < n2; i++) {
        for (int j = 0; j < n1; j++) {
            int my_idx = idx(i, j, n1);

            if (m[my_idx] == 0) continue;

            A.row.push_back(idx2nnzidx[my_idx]);
            A.col.push_back(idx2nnzidx[my_idx]);
            A.val.push_back(1);
            // A.row.push_back(my_idx);
            // A.col.push_back(my_idx);
            // A.val.push_back(1);

            if (i > 0 && m[idx(i - 1, j, n1)] != 0) {
                A.row.push_back(idx2nnzidx[my_idx]);
                A.col.push_back(idx2nnzidx[idx(i - 1, j, n1)]);
                A.val.push_back(1);
            }

            if (i < n2 - 1 && m[idx(i + 1, j, n1)] != 0) {
                A.row.push_back(idx2nnzidx[my_idx]);
                A.col.push_back(idx2nnzidx[idx(i + 1, j, n1)]);
                A.val.push_back(1);
            }

            if (j > 0 && m[idx(i, j - 1, n1)] != 0) {
                A.row.push_back(idx2nnzidx[my_idx]);
                A.col.push_back(idx2nnzidx[idx(i, j - 1, n1)]);
                A.val.push_back(1);
            }

            if (j < n1 - 1 && m[idx(i, j + 1, n1)] != 0) {
                A.row.push_back(idx2nnzidx[my_idx]);
                A.col.push_back(idx2nnzidx[idx(i, j + 1, n1)]);
                A.val.push_back(1);
            }
        }
    }
}

/** solve several sparse linear systems */
int main(int argc, char **argv) {
    FILE *input_file = fopen("in.data", "rb");

    int n1;
    int n2;

    fread(&n1, 1, sizeof(n1), input_file);
    fread(&n2, 1, sizeof(n2), input_file);

    int *matrix = (int *)malloc(sizeof(int) * n1 * n2);
    int *ans = (int *)calloc(n1 * n2, sizeof(int));

    fprintf(stderr, "n1 = %zu, n2 = %zu\n", n1, n2);

    printf("Begin Reading...\n");

    fread(matrix, 1, sizeof(int) * n1 * n2, input_file);

    fclose(input_file);

    int N = n1 * n2;

    SparseMatrix my_A;
    my_A.n = n1 * n2;
    my_A.row.clear();
    my_A.col.clear();
    my_A.val.clear();
    std::vector<uint8_t> my_B(my_A.n, 0);

    std::vector<int> nnz_idx;

    init_matrix(matrix, my_A, my_B, nnz_idx, n1, n2);

    int new_N = nnz_idx.size();
    int nnz = my_A.row.size();

    printf("new_N = %d, nnz = %d\n", new_N, nnz);

    // for (int i = 0; i < new_N; i++) {
    // 	printf("nnz_idx[%d] = %d\n", i, nnz_idx[i]);
    // }

    static SparseMatrixRow A;
    A.n = new_N;
    A.row.resize(new_N);
    // A.col_val.resize(new_N);
    A.col.resize(new_N);
    A.val.resize(new_N);
    A.nnz_col.resize(new_N);
    // A.arr.resize(new_N);
    A.first.resize(new_N);
    A.second.resize(new_N);

    for (int i = 0; i < new_N; i++) {
        A.row[i] = i;
        A.col[i].clear();
        A.val[i].clear();

        // 对角线元素
        A.col[i].push_back(i);
        A.val[i].push_back(1);
    }

    for (int i = 0; i < nnz; i++) {
        int row = my_A.row[i];
        int col = my_A.col[i];
        if (row == col) continue;
        i8 val = my_A.val[i];
        A.col[row].push_back(col);
        A.val[row].push_back(val);
        // printf("A[%d][%d] = %d\n", row, col, val);
    }

    // sort by col index
    for (int i = 0; i < new_N; i++) {
        std::vector<int> &col = A.col[i];
        std::vector<i8> &val = A.val[i];
        std::vector<std::pair<int, i8>> tmp;
        for (int j = 0; j < col.size(); j++) {
            tmp.push_back(std::make_pair(col[j], val[j]));
        }
        std::sort(tmp.begin(), tmp.end());
        col.clear();
        val.clear();

        int nnz_idx = tmp[0].first;
        A.nnz_col[i] = nnz_idx;
        ARR &first = A.first[i];
        ARR &second = A.second[i];
        first.reset();
        second.reset();

        for (int j = 0; j < tmp.size(); j++) {
            // col.push_back(tmp[j].first);
            // val.push_back(tmp[j].second);
            // printf("A[%d][%d] = %d\n", i, col[j], val[j]);
            assert(tmp[j].first - nnz_idx < MAX_N);
            // arr[tmp[j].first - nnz_idx] = tmp[j].second;
            // set_ele(arr, tmp[j].first - nnz_idx, tmp[j].second);
            set_ele(first, second, tmp[j].first - nnz_idx, tmp[j].second);
        }
        // print
        // printf("nnz_idx[%d] = %d\n", i, nnz_idx);
        // for (int j = 0; j < std::min(MAX_N, new_N); j++) {
        // 	printf("%3d", arr[j]);
        // }
        // printf("\n");
    }

    fprintf(stderr, "Loading B\n");

    std::vector<u8> B;
    B.resize(new_N);
    for (int i = 0; i < new_N; i++) {
        int x = my_B[nnz_idx[i]];
        B[i] = x == -1 ? 2 : x;
        // printf("B[%d] = %d\n", i, B[i]);
    }

    std::vector<u8> X;
    X.resize(new_N);

    printf("Begin Testing...\n");
    auto start_time = omp_get_wtime();
    solve(A, B, X, n1);
    auto end_time = omp_get_wtime();
    printf("Total Time: %lf seconds\n", end_time - start_time);

    for (int i = 0; i < new_N; i++) {
        ans[nnz_idx[i]] = X[i];
        // printf("ans[%d] = X[%d] = %d\n", nnz_idx[i], i, x);
    }

    FILE *output_file = fopen("out.data", "w");
    fwrite(ans, 1, sizeof(int) * n1 * n2, output_file);
    fclose(output_file);

    free(ans);
    free(matrix);

    return 0;

    // exit(EXIT_SUCCESS);
}
