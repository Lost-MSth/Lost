#include <omp.h>

#include <algorithm>
#include <cstdlib>
#include <vector>

typedef int element_t;

inline int min3(int a, int b, int c) { return std::min(std::min(a, b), c); }

size_t lcs_n(size_t N, element_t* s1, element_t* s2) {
    std::vector<std::vector<size_t>> dp(3, std::vector<size_t>(N + 1, 0));
    for (int sum = 2; sum <= N + N; ++sum) {
        int cur_sum = sum % 3;
        int prev_sum = (cur_sum + 2) % 3;
        int prev_prev_sum = (cur_sum + 1) % 3;
        int start = 1, finish = sum - 1;
        if (sum > N) {
            start = sum - N;
            finish = N;
        }
#pragma omp parallel for schedule(static)
        for (int i = start; i <= finish; ++i) {
            int j = sum - i;
            if (s1[i - 1] == s2[j - 1]) {
                dp[cur_sum][i] = dp[prev_prev_sum][i - 1] + 1;
            } else {
                dp[cur_sum][i] = std::max(dp[prev_sum][i - 1], dp[prev_sum][i]);
            }
        }
    }

    return dp[(N + N) % 3][N];
}

size_t lcs(element_t* arr_1, element_t* arr_2, size_t len_1, size_t len_2) {
    if (len_1 == len_2) {
        return lcs_n(len_1, arr_1, arr_2);
    }
    // len_2 >= len_1

    // int rows = len_1 + 1;
    // int cols = len_2 + 1;
    int rows = len_2 + 1;
    int cols = len_1 + 1;

    std::vector<std::vector<size_t>> dp(3, std::vector<size_t>(cols));

    for (int line = 1; line < rows + cols; line++) {
        int curr_line = line % 3;
        int prev_line = (line - 1) % 3;
        int prev_prev_line = (line - 2) % 3;

        int start_col = std::max(0, line - rows);
        int count = min3(line, (cols - start_col), rows);

#pragma omp parallel for schedule(static)
        for (int j = 0; j < count; j++) {
            int row = std::min(rows, line) - j - 1;
            int col = start_col + j;

            if (row == 0 || col == 0) {
                dp[curr_line][col] = 0;
                // } else if (arr_1[row - 1] == arr_2[col - 1]) {
            } else if (arr_2[row - 1] == arr_1[col - 1]) {
                int upper_left = dp[prev_prev_line][col - 1];
                dp[curr_line][col] = upper_left + 1;
            } else {
                int left = dp[prev_line][col - 1];
                int up = dp[prev_line][col];
                dp[curr_line][col] = std::max(left, up);
            }
        }
    }

    return dp[(rows + cols - 1) % 3][cols - 1];
}
