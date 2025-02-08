
#include <assert.h>
// #include <inttypes.h>  // int64_t
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

#include <array>
#include <cstdint>
#include <functional>
#include <unordered_map>
#include <vector>

#define MAX_N 1025

typedef uint8_t u8;
// typedef int64_t i64;
typedef uint64_t u64;
typedef uint32_t u32;
// typedef int32_t i32;
typedef signed char i8;

// typedef std::map<int, i8> ColMap;
typedef std::unordered_map<int, i8> ColMap;

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
    std::vector<std::array<i8, MAX_N>> arr;  // 每一行从第一个非零列开始的值
};

inline bool get_factor(i8 factor, i8 pivot) {
    if (pivot == 1) {
        return factor == 1;
    } else {
        return factor == -1;
    }
}

inline i8 mod3(i8 a) {
    // a = -2 ~ 2
    if (a == 2) {
        return -1;
    } else if (a == -2) {
        return 1;
    } else {
        return a;
    }
}

inline i8 sub(i8 a, i8 b, bool factor) {
    // a, b in {-1, 0, 1}
    // factor = true: a - b
    if (factor) {
        return mod3(a - b);
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

inline int vec_sub(std::array<i8, MAX_N> &arr_a, const std::array<i8, MAX_N> &arr_b, bool factor) {
    // 注意：arr_a, arr_b 是密集数组
    // 注意 arr_a 会被修改

    std::array<i8, MAX_N> tmp = {0};

	// 两个数组开头的偏移一样的，所以对齐了
	#pragma omp simd
    for (int i = 0; i < MAX_N; i++) {
        tmp[i] = sub(arr_a[i], arr_b[i], factor);
    }

    // 找到第一个非零元素
    int nnz_idx;
    for (int i = 0; i < MAX_N; i++) {
        if (tmp[i] != 0) {
            nnz_idx = i;
            break;
        }
    }
    // assert(nnz_idx != MAX_N);

    // 清空 arr_a
	#pragma omp simd
    for (int i = 0; i < MAX_N; i++) {
        arr_a[i] = 0;
    }
    // 重新赋值
	#pragma omp simd
    for (int i = nnz_idx; i < MAX_N; i++) {
        arr_a[i - nnz_idx] = tmp[i];
    }

    return nnz_idx;
}

void solve(SparseMatrixRow &A, std::vector<i8> &B, std::vector<i8> &X, int n1) {
    int n = A.n;
    // std::vector<int> row_idx = A.row;
    // std::vector<std::vector<int>> &col_idx = A.col;
    // std::vector<std::vector<i8>> &col_val = A.val;
    std::vector<int> &nnz_idx = A.nnz_col;
    std::vector<std::array<i8, MAX_N>> &rows = A.arr;

    // 高斯消元 mod 3
    for (int i = 0; i < n; i++) {
        // 打印数组
        // for (int ii = 0; ii < n; ii++) {
		// 	for (int jj = 0; jj < nnz_idx[ii]; jj++) {
		// 		printf("  0");
		// 	}
        // 	for (int jj = nnz_idx[ii]; jj < MAX_N; jj++) {
		// 		if (jj >= n) break;
		// 		printf("%3d", rows[ii][jj-nnz_idx[ii]]);
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
            std::swap(rows[i], rows[j]);
            std::swap(B[i], B[j]);
            break;
        }

        // printf("i = %d, j = %d\n", i, j);
        assert(j < j_end);

        std::array<i8, MAX_N> &pivot_row = rows[i];
		i8 pivot = pivot_row[0];

        // assert(pivot == 1 || pivot == -1);

        int k_end = std::min(j + 2 + n1, n);
        // 消元
        for (int k = j + 1; k < k_end; k++) {
            // std::vector<int> &col = col_idx[k];

            // 直接看非零列号
            if (nnz_idx[k] != i) continue;

            // 两个向量相减
			// 注意 nnz_idx 是需要加上偏移的
			bool factor = get_factor(rows[k][0], pivot);
            nnz_idx[k] += vec_sub(rows[k], pivot_row, factor);

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
        i8 pivot = rows[i][0];
        // assert(pivot == 1 || pivot == -1);

    	int j_end = std::max(i - 2 * n1, 0);

        for (int j = i - 1; j >= j_end; j--) {
            // 需要算一下偏移
			int col_i_idx = i - j;
			i8 element = rows[j][col_i_idx];

            if (element == 0) continue;

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
    for (int i = 0; i < n; i++) {
        i8 pivot = rows[i][0];
        // int idx = row_idx[i];
        if (pivot == 1) {
            X[i] = B[i];
        } else {
            X[i] = -B[i];
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

    SparseMatrixRow A;
    A.n = new_N;
    A.row.resize(new_N);
    // A.col_val.resize(new_N);
    A.col.resize(new_N);
    A.val.resize(new_N);
    A.nnz_col.resize(new_N);
    A.arr.resize(new_N);

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
        std::array<i8, MAX_N> &arr = A.arr[i];
		arr.fill(0);

        for (int j = 0; j < tmp.size(); j++) {
            // col.push_back(tmp[j].first);
            // val.push_back(tmp[j].second);
            // printf("A[%d][%d] = %d\n", i, col[j], val[j]);
            assert(tmp[j].first - nnz_idx < MAX_N);
            arr[tmp[j].first - nnz_idx] = tmp[j].second;
        }

		// print
		// printf("nnz_idx[%d] = %d\n", i, nnz_idx);
		// for (int j = 0; j < std::min(MAX_N, new_N); j++) {
		// 	printf("%3d", arr[j]);
		// }
		// printf("\n");
    }

    fprintf(stderr, "Loading B\n");

    std::vector<i8> B;
    B.resize(new_N);
    for (int i = 0; i < new_N; i++) {
        B[i] = my_B[nnz_idx[i]];
        B[i] = mod3(B[i]);
        // printf("B[%d] = %d\n", i, B[i]);
    }

    std::vector<i8> X;
    X.resize(new_N);

    printf("Begin Testing...\n");
    auto start_time = omp_get_wtime();
    solve(A, B, X, n1);
    auto end_time = omp_get_wtime();
    printf("Total Time: %lf seconds\n", end_time - start_time);

    for (int i = 0; i < new_N; i++) {
        i8 x = X[i];
        if (x == -1) x = 2;
        ans[nnz_idx[i]] = x;

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
