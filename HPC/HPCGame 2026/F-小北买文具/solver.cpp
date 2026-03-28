#include <omp.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>

int mydgetrf(double* A, int* ipiv, int n, int block_size) {
    // Blocked LU with partial pivoting; block panel is factored sequentially,
    // trailing update is tiled and parallel.
    for (int k = 0; k < n; k += block_size) {
        const int bk = std::min(block_size, n - k);

        // Panel factorization (partial pivoting) on the current block column.
        for (int kk = 0; kk < bk; kk++) {
            int global_k = k + kk;
            int pivot_row = global_k;
            double max_val = fabs(A[global_k * n + global_k]);

            for (int i = global_k + 1; i < n; i++) {
                double val = fabs(A[i * n + global_k]);
                if (val > max_val) {
                    max_val = val;
                    pivot_row = i;
                }
            }

            if (max_val < 1e-14) {
                return 0;  // Matrix is singular
            }

            ipiv[global_k] = pivot_row;

            if (pivot_row != global_k) {
                for (int j = 0; j < n;
                     j++) {  // full-row swap keeps previous columns in sync
                    double tmp = A[global_k * n + j];
                    A[global_k * n + j] = A[pivot_row * n + j];
                    A[pivot_row * n + j] = tmp;
                }
            }

            // Compute multipliers for rows below the pivot within trailing
            // rows.
            for (int i = global_k + 1; i < n; i++) {
                A[i * n + global_k] =
                    A[i * n + global_k] / A[global_k * n + global_k];
                for (int j = global_k + 1; j < k + bk; j++) {
                    A[i * n + j] -= A[i * n + global_k] * A[global_k * n + j];
                }
            }
        }

        // Compute U for the current block rows to the right of the block (A12 =
        // L11^{-1} * A12).
        int col_start = k + bk;
        if (col_start < n) {
            for (int i = 0; i < bk; i++) {
                int row = k + i;
                for (int j = col_start; j < n; j++) {
                    double sum = A[row * n + j];
                    for (int p = k; p < row; p++) {
                        sum -= A[row * n + p] * A[p * n + j];
                    }
                    A[row * n + j] = sum;  // U(row, j)
                }
            }
        }

        // Trailing submatrix update: A(k+bk:n, k+bk:n) -= L_block * U_block
        int row_start = k + bk;
        col_start = k + bk;
        if (row_start < n && col_start < n) {
            // Tile the trailing update for cache locality and parallelize
            // tiles.
            const int tile = 128;
#pragma omp parallel for collapse(2) schedule(static)
            for (int ii = row_start; ii < n; ii += tile) {
                for (int jj = col_start; jj < n; jj += tile) {
                    int imax = std::min(tile, n - ii);
                    int jmax = std::min(tile, n - jj);
                    for (int i = 0; i < imax; i++) {
                        double* Arow = &A[(ii + i) * n + jj];
                        for (int kk = 0; kk < bk; kk++) {
                            double lik = A[(ii + i) * n + (k + kk)];
                            const double* Urow = &A[(k + kk) * n + jj];
#pragma omp simd
                            for (int j = 0; j < jmax; j++) {
                                Arow[j] -= lik * Urow[j];
                            }
                        }
                    }
                }
            }
        }
    }

    return 1;
}

void mydtrsv(char UPLO, double* A, double* B, int n, int* ipiv) {
    // Solve triangular system
    // A is in row-major format
    // UPLO='L': solve Lx=B (L has unit diagonal)
    // UPLO='U': solve Ux=B (U has non-unit diagonal)

    if (UPLO == 'L' || UPLO == 'l') {
        // Forward substitution for lower triangular system with unit diagonal
        // Apply pivoting first
        for (int i = 0; i < n; i++) {
            if (ipiv[i] != i) {
                double tmp = B[i];
                B[i] = B[ipiv[i]];
                B[ipiv[i]] = tmp;
            }
        }

        // Solve Lx=B where L has unit diagonal
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < i; j++) {
                B[i] -= A[i * n + j] * B[j];
            }
            // Note: L[i,i] = 1, so no division needed
        }
    } else if (UPLO == 'U' || UPLO == 'u') {
        // Backward substitution for upper triangular system
        // Solve Ux=B
        for (int i = n - 1; i >= 0; i--) {
            for (int j = i + 1; j < n; j++) {
                B[i] -= A[i * n + j] * B[j];
            }
            B[i] /= A[i * n + i];
        }
    }
}

void my_solver(int n, double* A, double* b) {
    int* ipiv = (int*)malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) ipiv[i] = i;
    const int block_size =
        16;  // tune for cache size; balance panel cost vs locality
    if (mydgetrf(A, ipiv, n, block_size) == 0) {
        printf("LU factorization failed: coefficient matrix is singular.\n");
        free(ipiv);
        return;
    }
    mydtrsv('L', A, b, n, ipiv);
    mydtrsv('U', A, b, n, ipiv);
    free(ipiv);
}
