
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
    // std::vector<std::array<i8, MAX_N>> arr;  // 每一行从第一个非零列开始的值
    std::vector<std::bitset<MAX_N * 2>>
        arr;  // 每一行从第一个非零列开始的值，每个元素是 2 位
};

inline void set_ele(std::bitset<MAX_N * 2> &arr, int idx, u8 val) {
    assert(val == 0 || val == 1 || val == 2);
    arr[idx * 2] = val & 1;
    arr[idx * 2 + 1] = (val >> 1) & 1;
}

inline u8 get_ele(const std::bitset<MAX_N * 2> &arr, int idx) {
    u8 x = arr[idx * 2] | (arr[idx * 2 + 1] << 1);
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

inline void clear_zero(std::bitset<MAX_N * 2> &arr) {
	// 因为 11 表示 0，所以我们需要把所有 11 变成 00
	for (int i = 0; i < MAX_N; i++) {
		if (arr[i * 2] & arr[i * 2 + 1]) {
			arr[i * 2] = 0;
			arr[i * 2 + 1] = 0;
		}
	}
}

inline void bit_add(const std::bitset<MAX_N * 2> &a, const std::bitset<MAX_N * 2> &b, std::bitset<MAX_N * 2> &ans) {
	// a + b

	for (int i = 0; i < MAX_N; i++) {
		auto a1 = a[i * 2];
		auto a2 = a[i * 2 + 1];
		auto b1 = b[i * 2];
		auto b2 = b[i * 2 + 1];
		auto c1 = a1 ^ b1;
		auto c2 = a2 ^ b2;
		if ((a1 | a2) & !(a1 ^ b1) & !(a2 ^ b2)) {
			// 两个都是 1 或者 2
			ans[i * 2] = !a1;
			ans[i * 2 + 1] = !a2;
		} else {
			ans[i * 2] = c1;
			ans[i * 2 + 1] = c2;
		}
	}
}

inline int vec_sub(std::bitset<MAX_N * 2> &arr_a,
                   const std::bitset<MAX_N * 2> &arr_b, bool factor) {
    // 注意：arr_a, arr_b 是密集 bits
    // 注意 arr_a 会被修改

	// print
	// for (int i = 0; i < 18; i++) {
	// 	printf("%3d", get_ele(arr_a, i));
	// }
	// printf("\n");
	// for (int i = 0; i < 18; i++) {
	// 	printf("%3d", get_ele(arr_b, i));
	// }
	// printf("\n");
	// printf("factor = %d\n", factor);

    // std::array<i8, MAX_N> tmp = {0};
    std::bitset<MAX_N * 2> tmp;

    // 两个数组开头的偏移一样的，所以对齐了
    // #pragma omp simd
        // for (int i = 0; i < MAX_N; i++) {
        //     tmp[i] = sub(arr_a[i], arr_b[i], factor);
        // }
	// for (int i = 0; i < MAX_N; i++) {
	// 	set_ele(tmp, i, sub(get_ele(arr_a, i), get_ele(arr_b, i), factor));
	// }

	if (factor) {
		// a - b
		std::bitset<MAX_N * 2> inv_b(arr_b);
		inv_b.flip();
		clear_zero(inv_b);
		bit_add(arr_a, inv_b, tmp);
		clear_zero(tmp);
	} else {
		// a + b
		bit_add(arr_a, arr_b, tmp);
		clear_zero(tmp);
	}

	// print
	// for (int i = 0; i < 18; i++) {
	// 	printf("%3d", get_ele(tmp, i));
	// }
	// printf("\n");
    

    // 找到第一个非零元素
    int nnz_idx = tmp._Find_first() / 2;
	// printf("nnz_idx = %d\n", nnz_idx);
    assert(nnz_idx != MAX_N);

    // 清空 arr_a
    arr_a.reset();
    // 重新赋值
    // #pragma omp simd
    //     for (int i = nnz_idx; i < MAX_N; i++) {
    //         arr_a[i - nnz_idx] = tmp[i];
    //     }
    // for (int i = nnz_idx; i < MAX_N; i++) {
    // 	set_ele(arr_a, i - nnz_idx, get_ele(tmp, i));
    // }
	int offset = nnz_idx * 2;
    for (int i = offset; i < MAX_N * 2; i++) {
        arr_a[i - offset] = tmp[i];
    }

    return nnz_idx;
}



void solve(SparseMatrixRow &A, std::vector<u8> &B, std::vector<u8> &X, int n1) {
    int n = A.n;
    // std::vector<int> row_idx = A.row;
    // std::vector<std::vector<int>> &col_idx = A.col;
    // std::vector<std::vector<i8>> &col_val = A.val;
    std::vector<int> &nnz_idx = A.nnz_col;
    // std::vector<std::array<i8, MAX_N>> &rows = A.arr;
    std::vector<std::bitset<MAX_N * 2>> &rows = A.arr;

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
		// 		printf("%3d", get_ele(rows[ii], jj - nnz_idx[ii]));
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

        // std::array<i8, MAX_N> &pivot_row = rows[i];
        std::bitset<MAX_N * 2> &pivot_row = rows[i];
        // i8 pivot = pivot_row[0];
        u8 pivot = get_ele(pivot_row, 0);

        // assert(pivot == 1 || pivot == -1);

        int k_end = std::min(j + 2 + n1, n);
        // 消元
        for (int k = j + 1; k < k_end; k++) {
            // std::vector<int> &col = col_idx[k];

            // 直接看非零列号
            if (nnz_idx[k] != i) continue;

            // 两个向量相减
            // 注意 nnz_idx 是需要加上偏移的
            bool factor = get_factor(get_ele(rows[k], 0), pivot);
            nnz_idx[k] += vec_sub(rows[k], pivot_row, factor);

            B[k] = sub(B[k], B[i], factor);
        }

        // 更新当前进度
        if (i % 1000 == 0) {
            fprintf(stderr, "Progress: %d / %d\r", i, n);
            fflush(stderr);
        }
    }

    // 回代
    for (int i = n - 1; i > 0; i--) {
        // i8 pivot = rows[i][0];
        u8 pivot = get_ele(rows[i], 0);
        // assert(pivot == 1 || pivot == -1);

        int j_end = std::max(i - 2 * n1, 0);

        for (int j = i - 1; j >= j_end; j--) {
            // 需要算一下偏移
            int col_i_idx = i - j;
            // i8 element = rows[j][col_i_idx];
            u8 element = get_ele(rows[j], col_i_idx);

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
        // i8 pivot = rows[i][0];
        u8 pivot = get_ele(rows[i], 0);
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
        std::bitset<MAX_N * 2> &arr = A.arr[i];
        arr.reset();

        for (int j = 0; j < tmp.size(); j++) {
            // col.push_back(tmp[j].first);
            // val.push_back(tmp[j].second);
            // printf("A[%d][%d] = %d\n", i, col[j], val[j]);
            assert(tmp[j].first - nnz_idx < MAX_N);
            // arr[tmp[j].first - nnz_idx] = tmp[j].second;
            set_ele(arr, tmp[j].first - nnz_idx, tmp[j].second);
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
