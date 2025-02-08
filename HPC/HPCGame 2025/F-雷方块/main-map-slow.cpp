
#include <assert.h>
// #include <inttypes.h>  // int64_t
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

#include <cstdint>
#include <unordered_map>
#include <vector>

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
    int n;                 // 矩阵的行数、列数
    std::vector<int> row;  // 每一行的行号，用于行交换
    // std::vector<std::vector<int>> col;  // 每一行的列索引
    // std::vector<std::vector<i8>> val;   // 每一行的值
    std::vector<ColMap> col_val;  // 每一行的列索引和值
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

inline void clear_zero(ColMap &col) {
    for (auto it = col.begin(); it != col.end();) {
        if (it->second == 0)
            it = col.erase(it);
        else
            ++it;
    }
}


void solve(SparseMatrixRow &A, std::vector<i8> &B, std::vector<i8> &X) {
    int n = A.n;
    std::vector<int> row_idx = A.row;
    std::vector<ColMap> &col_val = A.col_val;

    // mod 3

    // 高斯消元
    for (int i = 0; i < n; i++) {
        // 打印矩阵
        // for (int i = 0; i < n; i++) {
        //     for (int j = 0; j < n; j++) {
        //         if (col_val[i].find(j) != col_val[i].end()) {
        //             i8 val = col_val[i][j];
        //             if (val == 1) {
        //                 printf("  1");
        //             } else if (val == -1) {
        //                 printf(" -1");
        //             } else {
        //                 assert(val != 0);
        //             }
        //         } else {
        //             printf("  0");
        //         }
        //     }
        //     printf("   ");
        //     printf("%d", B[i]);
        //     printf("\n");
        // }
        // printf("\n");

        // 找到第 i 列的主元

        int j;
        for (j = i; j < n; j++) {
            ColMap &col = col_val[j];
            if (col.find(i) == col.end()) continue;

            if (i == j) break;

            // 交换行
            std::swap(row_idx[i], row_idx[j]);
            std::swap(col_val[i], col_val[j]);
			std::swap(B[i], B[j]);
            break;
        }

        // printf("i = %d, j = %d\n", i, j);
        assert(j < n);

        i8 pivot = col_val[i][i];
        assert(pivot == 1 || pivot == -1);
        ColMap &curr_col = col_val[i];

        // 消元
        for (int k = i + 1; k < n; k++) {
            ColMap &col = col_val[k];
            if (col.find(i) == col.end()) continue;

            bool factor = get_factor(col[i], pivot);
            for (auto &kv : curr_col) {
                int col_idx = kv.first;
                i8 val = kv.second;
                col[col_idx] = sub(col[col_idx], val, factor);
            }

            B[k] = sub(B[k], B[i], factor);

            // 消除 0
            clear_zero(col);
        }

		// 更新当前进度
		fprintf(stderr, "Progress: %d / %d\r", i, n);
		fflush(stderr);
    }

    // 回代
    for (int i = n - 1; i > 0; i--) {
        i8 pivot = col_val[i][i];
        assert(pivot == 1 || pivot == -1);
        ColMap &curr_col = col_val[i];

        for (int j = i - 1; j >= 0; j--) {
            ColMap &col = col_val[j];
            if (col.find(i) == col.end()) continue;

            bool factor = get_factor(col[i], pivot);
            for (auto &kv : curr_col) {
                int col_idx = kv.first;
                i8 val = kv.second;
                col[col_idx] = sub(col[col_idx], val, factor);
            }
            B[j] = sub(B[j], B[i], factor);

            // 消除 0
            clear_zero(col);
        }
    }

    // 解
    for (int i = 0; i < n; i++) {
        i8 pivot = col_val[i][i];
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
    A.col_val.resize(new_N);

    for (int i = 0; i < new_N; i++) {
        A.row[i] = i;
        A.col_val[i].clear();
    }

    for (int i = 0; i < nnz; i++) {
        int row = my_A.row[i];
        int col = my_A.col[i];
        i8 val = my_A.val[i];
        A.col_val[row][col] = val;
        // printf("A[%d][%d] = %d\n", row, col, val);
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
    solve(A, B, X);
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
