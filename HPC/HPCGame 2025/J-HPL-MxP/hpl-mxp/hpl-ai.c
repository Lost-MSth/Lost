#include "hpl-ai.h"
#include <stdio.h>
#include <stdlib.h>
#include <float.h>
#include <string.h>
#include <math.h>
#include <stdio.h>
#include <sys/time.h>


#define S(i, j) *HPLAI_INDEX2D(src, (i), (j), ldsrc)
#define D(i, j) *HPLAI_INDEX2D(dst, (i), (j), lddst)
#define A(i, j) *HPLAI_INDEX2D(A, (i), (j), lda)

#define LCG_A 6364136223846793005ULL
#define LCG_C 1ULL
#define LCG_MUL 5.4210108624275222e-20f

#define MCG_A 14647171131086947261ULL
#define MCG_MUL 2.328306436538696e-10f

void convert_double_to_float(double *src, int ldsrc, float *dst,
                             int lddst, int m, int n) {
    int i, j;
    for (i = 0; i < m; ++i) {
        for (j = 0; j < n; ++j) {
            D(i, j) = (float)S(i, j);
        }
    }
    return;
}

void convert_float_to_double(float *src, int ldsrc, double *dst,
                             int lddst, int m, int n) {
    int i, j;
    for (i = 0; i < m; ++i) {
        for (j = 0; j < n; ++j) {
            D(i, j) = (double)S(i, j);
        }
    }
    return;
}

// Linear Congruential Generator (LCG).
inline unsigned long long lcg_rand(unsigned long long *piseed) {
    *piseed = *piseed * LCG_A + LCG_C;
    return *piseed;
}

// LCG jump ahead function to go through N steps in log(N) time.
inline void lcg_advance(unsigned int delta, unsigned long long *piseed) {
    unsigned long long accum_a = LCG_A;
    unsigned long long accum_c = LCG_C;
    while (delta != 0) {
        if (delta & 1) {
            delta = delta - 1;
            *piseed = *piseed * accum_a + accum_c;
        }
        delta = delta / 2;
        accum_c *= accum_a + LCG_C;
        accum_a *= accum_a;
    }
}

// Generate double floating-point number from uniform(-0.5, 0.5) from LCG.
inline double lcg_rand_double(unsigned long long *piseed) {
    return ((double)lcg_rand(piseed)) * LCG_MUL - 0.5;
}

// Multiplicative Congruential Generator (MCG). Seed should be odd number.
inline unsigned long int mcg_rand(unsigned long long *piseed) {
    *piseed *= MCG_A;
    return *piseed >> 32; /* use high 32 bits */
}

// Jump ahead function to go through N steps in log(N) time.
inline void mcg_advance(unsigned int delta, unsigned long long *piseed) {
    unsigned long long accum = MCG_A;
    while (delta != 0) {
        if (delta & 1) {
            delta = delta - 1;
            *piseed *= accum;
        }
        delta = delta / 2;
        accum = accum * accum;
    }
}

// Generate double floating-point number from uniform(-0.5, 0.5) from MCG.
inline double mcg_rand_double(unsigned long long *piseed) {
    return ((double)mcg_rand(piseed)) * MCG_MUL - 0.5;
}

// Generate a row diagonally dominant square matrix A.
void matgen(double *A, int lda, int m, unsigned long long iseed) {

    int i, j;

    double *diag = (double *)malloc(m * sizeof(double));
    memset(diag, 0, m * sizeof(double));

    for (j = 0; j < m; j++) {
        for (i = 0; i < m; i++) {
            A(i, j) = lcg_rand_double(&iseed);
            diag[i] += fabs(A(i, j));
        }
    }

    for (i = 0; i < m; i++) {
        A(i, i) = diag[i] - fabs(A(i, i));
    }

    free(diag);
}

void vecgen(double *v, int n, unsigned long long iseed) {
    int i;
    for (i = 0; i < n; i++) {
        v[i] = lcg_rand_double(&iseed);
    }
    return;
}

double get_wtime(void) {
    struct timeval t;
    gettimeofday(&t, NULL);
    return t.tv_sec + t.tv_usec * 1e-6;
}

void print_matrix_float(float *A, int lda, int m, int n) {

    int i, j;

    if (lda < m) {
        return;
    }
    printf("[%s", m==1 ? " " : "\n");
    for (i = 0; i < m; ++i) {
        for (j = 0; j < n; ++j) {
            printf(" %10.6f", A(i, j));
        }
        printf("%s", m>1 ? "\n" : " ");
    }
    printf("];\n");
    return;
}

void print_matrix_double(double *A, int lda, int m, int n) {

    int i, j;

    if (lda < m) {
        return;
    }
    printf("[%s", m==1 ? "" : "\n");
    for (i = 0; i < m; ++i) {
        for (j = 0; j < n; ++j) {
            printf(" %14.10e", A(i, j));
        }
        printf("%s", m>1 ? "\n" : " ");
    }
    printf("];\n");
    return;
}


int main(int argc, char* argv[]) {

    const int n = 20000;      // matrix size
    const int max_it = 200;  // maximum number of iterations in GMRES

    double time_convert, time_factor, time_solve, time_gmres, time_total;

    int lda = (n + 16 - 1) / 16 * 16;  // round up to multiple of 16
    unsigned long long iseed = 1;      // RNG seed

    double* A = (double*)malloc(lda * n * sizeof(double));
    double* LU = (double*)malloc(lda * n * sizeof(double));
    double* b = (double*)malloc(n * sizeof(double));
    double* x = (double*)malloc(n * sizeof(double));
    float* sA = (float*)malloc(lda * n * sizeof(float));
    float* sb = (float*)malloc(n * sizeof(float));

    matgen(A, lda, n, iseed);
    vecgen(b, n, iseed+1);

    printf(
        "======================================================================"
        "==========\n");
    printf(
        "                        HPL-AI Mixed-Precision Benchmark              "
        "          \n");
    printf(
        "       Written by Yaohung Mike Tsai, Innovative Computing Laboratory, "
        "UTK       \n");
    printf(
        "======================================================================"
        "==========\n");
    printf("\n");
    printf(
        "This is a reference implementation with the matrix generator, an "
        "example\n");
    printf(
        "mixed-precision solver with LU factorization in single and GMRES in "
        "double,\n");
    printf("as well as the scaled residual check.\n");
    printf(
        "Please visit http://www.icl.utk.edu/research/hpl-ai for more "
        "details.\n");
    printf("\n");

    // Convert A and b to single.
    time_convert = get_wtime();
    time_total = time_convert;
    convert_double_to_float(A, lda, sA, lda, n, n);
    convert_double_to_float(b, n, sb, n, n, 1);
    time_convert = get_wtime() - time_convert;
    printf("Time spent in conversion to single: %12.3f second\n", time_convert);

    // LU factorization without pivoting.
    time_factor = get_wtime();
    time_total = time_factor;
    sgetrf_nopiv(n, n, sA, lda);
    time_factor = get_wtime() - time_factor;
    printf("Time spent in factorization       : %12.3f second\n", time_factor);

    // Forward and backward substitution.
    time_solve = get_wtime();
    strsm('L', 'L', 'N', 'U', n, 1, 1.0, sA, lda, sb, n);
    strsm('L', 'U', 'N', 'N', n, 1, 1.0, sA, lda, sb, n);
    time_solve = get_wtime() - time_solve;
    printf("Time spent in solve               : %12.3f second\n", time_solve);

    // Convert result back to double.
    time_convert = get_wtime();
    convert_float_to_double(sA, lda, LU, lda, n, n);
    convert_float_to_double(sb, n, x, n, n, 1);
    time_convert = get_wtime() - time_convert;
    printf("Time spent in conversion to double: %12.3f second\n", time_convert);

    // Using GMRES without restart.
    time_gmres = get_wtime();
    // GMRES is checking preconditioned residual so the tolerance is smaller.
    double tol = DBL_EPSILON / 2.0 / ((double)n / 4.0);
    gmres(n, A, lda, x, b, LU, lda, max_it, 1, tol);
    time_gmres = get_wtime() - time_gmres;
    time_total = get_wtime() - time_total;
    printf("Time spent in GMRES               : %12.3f second\n", time_gmres);
    printf("Total time                        : %12.3f second\n", time_total);

    double ops = 2.0 / 3.0 * n * n * n + 3.0 / 2.0 * n * n;
    printf("Effective operation per sec       : %12f GFLOPs\n",
           1e-9 * ops / time_total);

    // Check final backward error.
    double norm_A = dlange('I', n, n, A, lda);
    double norm_x = dlange('I', n, 1, x, n);
    double norm_b = dlange('I', n, 1, b, n);
    dgemv('N', n, n, 1.0, A, lda, x, 1, -1.0, b, 1);
    double threshold = 16.0;
    double eps = DBL_EPSILON / 2;
    double error =
        dlange('I', n, 1, b, n) / (norm_A * norm_x + norm_b) / n / eps;
    printf("The following scaled residual check will be computed:\n");
    printf(
        "||Ax-b||_oo / ( eps * ( || x ||_oo * || A ||_oo + || b ||_oo ) * N "
        ")\n");
    printf("The relative machine precision (eps) is taken to be: %e\n", eps);
    printf("Computational tests pass if scaled residuals are less than %.1f\n",
           threshold);
    printf("||Ax-b||_oo/(eps*(||A||_oo*||x||_oo+||b||_oo)*N)= %f ...", error);
    if (error < threshold) {
        printf("PASSED\n");
    } else {
        printf("FAILED\n");
    }

    return 0;
}
