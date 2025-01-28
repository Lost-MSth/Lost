#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <kblas.h>


#include "hpl-ai.h"

#define A(i, j) *HPLAI_INDEX2D(A, (i), (j), lda)
#define B(i, j) *HPLAI_INDEX2D(B, (i), (j), ldb)
#define C(i, j) *HPLAI_INDEX2D(C, (i), (j), ldc)

void sgemm(char transa, char transb, int m, int n, int k,
           float alpha, float *A, int lda, float *B, int ldb,
           float beta, float *C, int ldc) {
    CBLAS_TRANSPOSE ta = (transa == 'N') ? CblasNoTrans : CblasTrans;
    CBLAS_TRANSPOSE tb = (transb == 'N') ? CblasNoTrans : CblasTrans;
    cblas_sgemm(CblasColMajor, ta, tb, m, n, k, alpha, A, lda, B, ldb, beta, C, ldc);
}

void strsm(char side, char uplo, char transa, char diag, int m, int n,
           float alpha, float *A, int lda, float *B, int ldb) {
    CBLAS_SIDE s = (side == 'L') ? CblasLeft : CblasRight;
    CBLAS_UPLO u = (uplo == 'U') ? CblasUpper : CblasLower;
    CBLAS_TRANSPOSE ta = (transa == 'N') ? CblasNoTrans : CblasTrans;
    CBLAS_DIAG d = (diag == 'N') ? CblasNonUnit : CblasUnit;
    cblas_strsm(CblasColMajor, s, u, ta, d, m, n, alpha, A, lda, B, ldb);
}

void dtrsm(char side, char uplo, char transa, char diag, int m, int n,
           double alpha, double *A, int lda, double *B, int ldb) {
    CBLAS_SIDE s = (side == 'L') ? CblasLeft : CblasRight;
    CBLAS_UPLO u = (uplo == 'U') ? CblasUpper : CblasLower;
    CBLAS_TRANSPOSE ta = (transa == 'N') ? CblasNoTrans : CblasTrans;
    CBLAS_DIAG d = (diag == 'N') ? CblasNonUnit : CblasUnit;
    cblas_dtrsm(CblasColMajor, s, u, ta, d, m, n, alpha, A, lda, B, ldb);
}

double dlange(char norm, int m, int n, double *A, int lda) {
    int i, j;
    if (norm == 'F') {
        return cblas_dnrm2(m * n, A, 1);
    } else if (norm == 'I') {
        double *work = (double *)malloc(m * sizeof(double));
        memset(work, 0, m * sizeof(double));
        double max = 0.0;
        for (j = 0; j < n; ++j) {
            for (i = 0; i < m; ++i) {
                work[i] += fabs(A(i, j));
            }
        }
        for (i = 0; i < m; ++i) {
            if (max < work[i]) {
                max = work[i];
            }
        }
        free(work);
        return max;
    }
    return 0;
}

void dgemv(char trans, int m, int n, double alpha, double *A,
           int lda, double *X, int incx, double beta, double *Y,
           int incy) {
    CBLAS_TRANSPOSE t = (trans == 'N') ? CblasNoTrans : CblasTrans;
    cblas_dgemv(CblasColMajor, t, m, n, alpha, A, lda, X, incx, beta, Y, incy);
}
