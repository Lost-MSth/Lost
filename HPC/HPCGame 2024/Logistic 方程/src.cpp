#include <immintrin.h>
#include <omp.h>

#include <chrono>
#include <iostream>

// void itv(double r, double* x, int64_t n, int64_t itn) {
//     const __m512d r_vec = _mm512_set1_pd(r);
//     const __m512d one_vec = _mm512_set1_pd(1.0);
//     __m512d x_vec;

// #pragma omp parallel for
//     for (int64_t i = 0; i < n; i += 8) {
//         x_vec = _mm512_load_pd(&x[i]);

//         for (int64_t j = 0; j < itn; j++) {
//             x_vec = _mm512_mul_pd(_mm512_mul_pd(r_vec, x_vec),
//                                   _mm512_sub_pd(one_vec, x_vec));
//         }
//         _mm512_store_pd(&x[i], x_vec);
//     }
// }

// double it(double r, double x, int64_t itn) {
//     for (int64_t i = 0; i < itn; i++) {
//         x = r * x * (1.0 - x);
//     }
//     return x;
// }

// void itv(double r, double* x, int64_t n, int64_t itn) {
//     for (int64_t i = 0; i < n; i++) {
//         x[i] = it(r, x[i], itn);
//     }
// }

void itv(double r, double* x, int64_t n, int64_t itn) {
    const __m512d r_vec = _mm512_set1_pd(r);
    const __m512d one_vec = _mm512_set1_pd(1.0);
    __m512d x_vec, y_vec, z_vec, w_vec, a_vec, b_vec, c_vec, d_vec;


#pragma omp parallel for schedule(dynamic, 64)
    for (int64_t i = 0; i < n; i += 64) {
        x_vec = _mm512_load_pd(&x[i]);
        y_vec = _mm512_load_pd(&x[i+8]);
        z_vec = _mm512_load_pd(&x[i+16]);
        w_vec = _mm512_load_pd(&x[i+24]);
        a_vec = _mm512_load_pd(&x[i+32]);
        b_vec = _mm512_load_pd(&x[i+40]);
        c_vec = _mm512_load_pd(&x[i+48]);
        d_vec = _mm512_load_pd(&x[i+56]);

        for (int64_t j = 0; j < itn; j++) {
            x_vec = _mm512_mul_pd(_mm512_mul_pd(x_vec, r_vec),
                                  _mm512_sub_pd(one_vec, x_vec));
            y_vec = _mm512_mul_pd(_mm512_mul_pd(y_vec, r_vec),
                                  _mm512_sub_pd(one_vec, y_vec));
            z_vec = _mm512_mul_pd(_mm512_mul_pd(z_vec, r_vec),
                                  _mm512_sub_pd(one_vec, z_vec));
            w_vec = _mm512_mul_pd(_mm512_mul_pd(w_vec, r_vec),
                                  _mm512_sub_pd(one_vec, w_vec));
            a_vec = _mm512_mul_pd(_mm512_mul_pd(a_vec, r_vec),
                                  _mm512_sub_pd(one_vec, a_vec));
            b_vec = _mm512_mul_pd(_mm512_mul_pd(b_vec, r_vec),
                                  _mm512_sub_pd(one_vec, b_vec));
            c_vec = _mm512_mul_pd(_mm512_mul_pd(c_vec, r_vec),
                                  _mm512_sub_pd(one_vec, c_vec));
            d_vec = _mm512_mul_pd(_mm512_mul_pd(d_vec, r_vec),
                                  _mm512_sub_pd(one_vec, d_vec));
        }
        _mm512_store_pd(&x[i], x_vec);
        _mm512_store_pd(&x[i+8], y_vec);
        _mm512_store_pd(&x[i+16], z_vec);
        _mm512_store_pd(&x[i+24], w_vec);
        _mm512_store_pd(&x[i+32], a_vec);
        _mm512_store_pd(&x[i+40], b_vec);
        _mm512_store_pd(&x[i+48], c_vec);
        _mm512_store_pd(&x[i+56], d_vec);
    }
}

int main() {
    FILE* fi;
    fi = fopen("conf.data", "rb");

    int64_t itn;
    double r;
    int64_t n;
    double* x;

    fread(&itn, 1, 8, fi);
    fread(&r, 1, 8, fi);
    fread(&n, 1, 8, fi);
    x = (double*)_mm_malloc(n * 8, 64);
    fread(x, 1, n * 8, fi);
    fclose(fi);

    // auto t1 = std::chrono::steady_clock::now();
    itv(r, x, n, itn);
    // auto t2 = std::chrono::steady_clock::now();
    // int d1 = std::chrono::duration_cast<std::chrono::milliseconds>(t2 -
    // t1).count(); printf("%d\n", d1);

    fi = fopen("out.data", "wb");
    fwrite(x, 1, n * 8, fi);
    fclose(fi);

    return 0;
}