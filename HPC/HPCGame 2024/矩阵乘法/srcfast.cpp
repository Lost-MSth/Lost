#include <immintrin.h>
#include <omp.h>

#include <chrono>
#include <iostream>

#define BLOCKSIZE 256  // 分块大小
#define UNROLL 8      // 循环展开次数

static inline void get_block(uint64_t n1, uint64_t n2, uint64_t n3, uint64_t si,
                             uint64_t sj, uint64_t sk, double *A, double *B,
                             double *C) {
    // for (int i = si; i < si + BLOCKSIZE; i++) {
    //     for (int j = sj; j < sj + BLOCKSIZE; j++) {
    //         double c = C[i * n3 + j];
    //         for (int k = sk; k < sk + BLOCKSIZE; k++) {
    //             c += A[i * n2 + k] * B[k * n3 + j];
    //         }
    //         C[i * n3 + j] = c;
    //     }
    // }
    __m512d c[UNROLL];

    for (int i = si; i < si + BLOCKSIZE; i++) {
        for (int j = sj; j < sj + BLOCKSIZE; j += 8 * UNROLL) {
            for (int k = 0; k < UNROLL; k++) {
                c[k] = _mm512_load_pd(C + i * n3 + j + k * 8);
            }

            for (int k = sk; k < sk + BLOCKSIZE; k++) {
                __m512d a0 = _mm512_set1_pd(A[i * n2 + k]);

                for (int l = 0; l < UNROLL; l++) {
                    c[l] = _mm512_fmadd_pd(
                        a0, _mm512_load_pd(B + k * n3 + j + l * 8), c[l]);
                }
                // c0 = _mm512_fmadd_pd(_mm512_set1_pd(A[i * n2 + k]),
                //                       _mm512_load_pd(B + k * n3 + j), c0);
            }

            for (int k = 0; k < UNROLL; k++) {
                _mm512_store_pd(C + i * n3 + j + k * 8, c[k]);
            }

            // _mm512_store_pd(C + i * n3 + j, c0);
        }
    }
}

void mul(double *a, double *b, double *c, uint64_t n1, uint64_t n2,
         uint64_t n3) {
#pragma omp parallel for
    for (int si = 0; si < n1; si += BLOCKSIZE) {
        for (int sj = 0; sj < n3; sj += BLOCKSIZE) {
            for (int sk = 0; sk < n2; sk += BLOCKSIZE) {
                get_block(n1, n2, n3, si, sj, sk, a, b, c);
            }
        }
    }

    // #pragma omp parallel for
    //     for (int i = 0; i < n1; i++) {
    //         for (int j = 0; j < n2; j++) {
    //             for (int k = 0; k < n3; k++) {
    //                 c[i * n3 + k] += a[i * n2 + j] * b[j * n3 + k];
    //             }
    //         }
    //     }
}

int main() {
    uint64_t n1, n2, n3;
    FILE *fi;

    fi = fopen("conf.data", "rb");
    fread(&n1, 1, 8, fi);
    fread(&n2, 1, 8, fi);
    fread(&n3, 1, 8, fi);

    // n1 = 4096;
    // n2 = 4096;
    // n3 = 4096;

    printf("%llu %llu %llu\n", n1, n2, n3);

    // double *a = (double *)malloc(n1 * n2 * 8);
    // double *b = (double *)malloc(n2 * n3 * 8);
    // double *c = (double *)malloc(n1 * n3 * 8);

    double *a = (double *)_mm_malloc(n1 * n2 * 8, 64);
    double *b = (double *)_mm_malloc(n2 * n3 * 8, 64);
    double *c = (double *)_mm_malloc(n1 * n3 * 8, 64);

    // for (uint64_t i = 0; i < n1; i++) {
    //     for (uint64_t j = 0; j < n2; j++) {
    //         a[i * n2 + j] = rand();
    //     }
    // }

    // for (uint64_t i = 0; i < n2; i++) {
    //     for (uint64_t j = 0; j < n3; j++) {
    //         b[i * n3 + j] = rand();
    //     }
    // }

    fread(a, 1, n1 * n2 * 8, fi);
    fread(b, 1, n2 * n3 * 8, fi);
    fclose(fi);

    std::fill(c, c + n1 * n3, 0);

    // for (uint64_t i = 0; i < n1; i++) {
    //     for (uint64_t k = 0; k < n3; k++) {
    //         c[i * n3 + k] = 0;
    //     }
    // }

    auto t1 = std::chrono::steady_clock::now();
    mul(a, b, c, n1, n2, n3);
    auto t2 = std::chrono::steady_clock::now();
    int d1 =
        std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
    printf("%d\n", d1);

    fi = fopen("out.data", "wb");
    fwrite(c, 1, n1 * n3 * 8, fi);
    fclose(fi);

    return 0;
}