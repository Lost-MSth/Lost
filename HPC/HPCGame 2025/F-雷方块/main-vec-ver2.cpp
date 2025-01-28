
#include <assert.h>
// #include <inttypes.h>  // int64_t
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

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

inline int find_nnz(const std::vector<int> &col, int idx) {
    for (int i = 0; i < col.size(); i++) {
        if (col[i] == idx) return i;
    }
    return -1;
}

// inline void vec_sub(std::vector<int> &col_a, std::vector<i8> &val_a,
// 					const std::vector<int> &col_b, const
// std::vector<i8> &val_b, 					bool factor) {
// 	// 注意：col_a, col_b 已经排序
// 	// 注意 a 会被修改
// 	std::vector<int> col_c;
// 	std::vector<i8> val_c;

// 	col_c.reserve(col_a.size() + col_b.size());
// 	val_c.reserve(col_a.size() + col_b.size());

// 	int i = 0, j = 0;

// 	while (i < col_a.size() && j < col_b.size()) {
// 		int col_a_i = col_a[i];
// 		int col_b_j = col_b[j];

// 		if (col_a_i < col_b_j) {
// 			col_c.push_back(col_a_i);
// 			val_c.push_back(val_a[i]);
// 			i++;
// 		} else if (col_a_i > col_b_j) {
// 			col_c.push_back(col_b_j);
// 			val_c.push_back(factor ? -val_b[j] : val_b[j]);
// 			j++;
// 		} else {
// 			i8 val = sub(val_a[i], val_b[j], factor);
// 			if (val != 0) {
// 				col_c.push_back(col_a_i);
// 				val_c.push_back(val);
// 			}
// 			i++;
// 			j++;
// 		}
// 	}

// 	while (i < col_a.size()) {
// 		col_c.push_back(col_a[i]);
// 		val_c.push_back(val_a[i]);
// 		i++;
// 	}

// 	while (j < col_b.size()) {
// 		col_c.push_back(col_b[j]);
// 		val_c.push_back(factor ? -val_b[j] : val_b[j]);
// 		j++;
// 	}

// 	// col_a = std::move(col_c);
// 	// val_a = std::move(val_c);
// 	col_a.swap(col_c);
// 	val_a.swap(val_c);
// }
inline void vec_sub(std::vector<int> &col_a, std::vector<i8> &val_a,
                    const std::vector<int> &col_b, const std::vector<i8> &val_b,
                    bool factor, int n, int n1, int col_idx) {
    // 注意：col_a, col_b 已经排序
    // 注意 a 会被修改

	// col_idx 是当前在消元哪一列
	// 数组非零指标范围就是 col_idx ~ col_idx + n1 * 2

	int start = col_idx;
	int end = std::min(col_idx + n1 * 2, n);
	int len = end - start + 1;

    // 向量化
    // std::vector<i8> tmp1(len, 0);
    // std::vector<i8> tmp2(len, 0);
	i8 tmp1[MAX_N] = {0};
	i8 tmp2[MAX_N] = {0};


    int size_a = col_a.size();
    int size_b = col_b.size();

    for (int i = 0; i < size_a; i++) {
        tmp1[col_a[i]-start] = val_a[i];
    }

    for (int i = 0; i < size_b; i++) {
        tmp2[col_b[i]-start] = factor ? -val_b[i] : val_b[i];
    }

    col_a.clear();
    val_a.clear();
    // col_a.reserve(size_a + size_b);
    // val_a.reserve(size_a + size_b);

    for (int i = 0; i < len; i++) {
        i8 val = mod3(tmp1[i] + tmp2[i]);
        if (val != 0) {
            col_a.push_back(i + start);
            val_a.push_back(val);
        }
    }
}

void solve(SparseMatrixRow &A, std::vector<i8> &B, std::vector<i8> &X, int n1) {
    int n = A.n;
    // std::vector<int> row_idx = A.row;
    std::vector<std::vector<int>> &col_idx = A.col;
    std::vector<std::vector<i8>> &col_val = A.val;

    // 高斯消元 mod 3
    for (int i = 0; i < n; i++) {
        // 打印数组
        // for (int i = 0; i < n; i++) {
        // 	for (int j = 0; j < n; j++) {
        // 		int idx = find_nnz(col_idx[i], j);
        // 		if (idx == -1) {
        // 			printf("  0");
        // 		} else {
        // 			printf("%3d", col_val[i][idx]);
        // 		}
        // 	}
        // 	printf(" | %3d\n", B[i]);
        // }
        // printf("\n");

        // 找到第 i 列的主元
        int j;
        int j_end = std::min(i + 1 + n1, n);
        for (j = i; j < j_end; j++) {
            // ColMap &col = col_val[j];
            // if (col.find(i) == col.end()) continue;
            std::vector<int> &col = col_idx[j];
            // nnz_idx = find_nnz(col, i);
            // if (nnz_idx == -1) continue;
            // 已经排序了，又假定有解，所以直接取第一个元素
            if (col[0] != i) continue;

            if (i == j) break;

            // 交换行
            // std::swap(row_idx[i], row_idx[j]);
            std::swap(col_idx[i], col_idx[j]);
            std::swap(col_val[i], col_val[j]);
            std::swap(B[i], B[j]);
            break;
        }

        // printf("i = %d, j = %d\n", i, j);
        assert(j < j_end);

        i8 pivot = col_val[i][0];
        // assert(pivot == 1 || pivot == -1);

        int k_end = std::min(j + 2 + n1, n);
        // 消元
        for (int k = j + 1; k < k_end; k++) {
            std::vector<int> &col = col_idx[k];
            // int idx = find_nnz(col, i);
            // if (idx == -1) continue;
            // 已经排序了，又假定有解，所以直接取第一个元素
            if (col[0] != i) continue;
            std::vector<i8> &val = col_val[k];

            bool factor = get_factor(val[0], pivot);

            // 两个向量相减
            vec_sub(col, val, col_idx[i], col_val[i], factor, n, n1, i);

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
        i8 pivot = col_val[i][0];
        assert(pivot == 1 || pivot == -1);

		int j_end = std::max(i - 2 * n1, 0);

        for (int j = i - 1; j >= j_end; j--) {
            std::vector<int> &col = col_idx[j];
            // 已经排序了，又假定有解，所以直接取最后一个元素
            if (col.back() != i) continue;
            std::vector<i8> &val = col_val[j];

            // bool factor = get_factor(col[idx], pivot);
            bool factor = get_factor(val.back(), pivot);

            // 两个向量相减
            // vec_sub(col, val, col_idx[i], col_val[i], factor);
            // 直接 pop 最后一个元素
            col.pop_back();
            val.pop_back();

            B[j] = sub(B[j], B[i], factor);
        }

        // 更新当前进度
        if (i % 1000 == 0) {
            fprintf(stderr, "Progress: %d / %d\r", i, n);
            fflush(stderr);
        }
    }

    // 解
    for (int i = 0; i < n; i++) {
        i8 pivot = col_val[i][0];
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
        for (int j = 0; j < tmp.size(); j++) {
            col.push_back(tmp[j].first);
            val.push_back(tmp[j].second);
            // printf("A[%d][%d] = %d\n", i, col[j], val[j]);
        }
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
