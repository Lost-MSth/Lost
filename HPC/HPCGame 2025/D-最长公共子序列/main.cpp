#include <iostream>
#include <chrono>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <omp.h>

typedef int element_t;

size_t lcs(element_t* arr_1, element_t* arr_2, size_t len_1, size_t len_2);

int main() {
    FILE* input_file = fopen("input.dat", "rb");

    size_t len_1;
    size_t len_2;

    fread(&len_1, 1, sizeof(len_1), input_file);
    fread(&len_2, 1, sizeof(len_2), input_file);

    element_t* arr_1 = (element_t*)malloc(sizeof(element_t) * len_1);
    element_t* arr_2 = (element_t*)malloc(sizeof(element_t) * len_2);

    printf("Begin Reading...\n");

    fread(arr_1, 1, sizeof(element_t) * len_1, input_file);
    fread(arr_2, 1, sizeof(element_t) * len_2, input_file);
    fclose(input_file);

    printf("Begin Testing...\n");
    auto start_time = omp_get_wtime();
    size_t result = lcs(arr_1, arr_2, len_1, len_2);
    auto end_time = omp_get_wtime();
    printf("Total Time: %lf seconds\n", end_time - start_time);

    FILE* output_file = fopen("output.txt", "w");
    fprintf(output_file, "%lu\n", result);
    fclose(output_file);

    free(arr_1);
    free(arr_2);

    return 0;
}
