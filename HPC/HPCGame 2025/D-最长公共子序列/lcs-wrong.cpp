#include <omp.h>

#include <algorithm>
#include <cstdlib>
#include <vector>

typedef int element_t;
typedef int int_t;

#define ALPHABET_LENGTH 0xffff + 1
#define max(x, y) std::max(x, y)

int get_index_of_character(element_t *str, element_t x, int len) {
    for (int i = 0; i < len; i++) {
        if (str[i] == x) {
            return i;
        }
    }
    return -1;  // not found the character x in str
}

void calc_P_matrix_v2(int_t **P, element_t *b, int len_b, element_t *c,
                      int len_c) {
#pragma omp parallel for
    for (int i = 0; i < len_c; i++) {
        for (int j = 1; j < len_b + 1; j++) {
            if (b[j - 1] == c[i]) {
                P[i][j] = j;
            } else {
                P[i][j] = P[i][j - 1];
            }
        }
    }
}

int lcs_yang_v2(int_t *DP, int_t *prev_row, int_t **P, element_t *A,
                element_t *B, element_t *C, int m, int n, int u) {
    for (int i = 1; i < m + 1; i++) {
        int c_i = get_index_of_character(C, A[i - 1], u);
        int t, s;

#pragma omp parallel for private(t, s) schedule(static)
        for (int j = 0; j < n + 1; j++) {
            t = (0 - P[c_i][j]) < 0;
            s = (0 - (prev_row[j] - (t * prev_row[P[c_i][j] - 1])));
            DP[j] = ((t ^ 1) || (s ^ 0)) * (prev_row[j]) +
                    (!((t ^ 1) || (s ^ 0))) * (prev_row[P[c_i][j] - 1] + 1);
        }

#pragma omp parallel for schedule(static)
        for (int j = 0; j < n + 1; j++) {
            prev_row[j] = DP[j];
        }
    }
    return DP[n];
}

int lcs(int_t *DP, int_t *prev_row, element_t *A, element_t *B, int m, int n) {
    for (int i = 1; i < (m + 1); i++) {
        for (int j = 1; j < (n + 1); j++) {
            if (A[i - 1] == B[j - 1]) {
                DP[j] = prev_row[j - 1] + 1;
            } else {
                DP[j] = max(prev_row[j], DP[j - 1]);
            }
        }

        for (int j = 0; j < n + 1; j++) {
            prev_row[j] = DP[j];
        }
    }

    return DP[n];
}

size_t lcs(element_t *string_A, element_t *string_B, size_t len_a,
           size_t len_b) {
    if (len_a < len_b) {
        return lcs(string_B, string_A, len_b, len_a);
    }

    const int c_len = ALPHABET_LENGTH;
    element_t *unique_chars_C =
        (element_t *)malloc((c_len + 1) * sizeof(element_t *));
    for (int i = 0; i < c_len; i++) {
        unique_chars_C[i] = i;
    }

    int_t *DP_Results = (int_t *)malloc((len_b + 1) * sizeof(int_t));
    int_t *dp_prev_row = (int_t *)malloc((len_b + 1) * sizeof(int_t));

    // allocate memory for P_Matrix array
    int_t **P_Matrix = (int_t **)malloc(c_len * sizeof(int_t *));
    for (int k = 0; k < c_len; k++) {
        P_Matrix[k] = (int_t *)calloc((len_b + 1), sizeof(int_t));
    }

    calc_P_matrix_v2(P_Matrix, string_B, len_b, unique_chars_C, c_len);
    // printf("P_Matrix calculated\n");

    size_t res = lcs_yang_v2(DP_Results, dp_prev_row, P_Matrix, string_A,
                             string_B, unique_chars_C, len_a, len_b, c_len);

    free(P_Matrix);
    free(DP_Results);

    return res;
}
