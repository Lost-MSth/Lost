#include <chrono>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <utility>

#include <cuda_runtime.h>

__constant__ int N2;
__constant__ int Nm;
__constant__ int N1;
__constant__ int R;

__global__ void evolve_kernel(uint8_t *cell_arr, uint8_t *out_arr) {

    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;

    int x = idx & Nm;
    int y = (idx >> R) & Nm;
    int z = (idx >> R) >> R;

    int lz = ((z + N1 - 1) & Nm) * N2;
    int mz = z * N2;
    int rz = ((z + 1) & Nm) * N2;

    int ly = ((y + N1 - 1) & Nm) * N1;
    int my = y * N1;
    int ry = ((y + 1) & Nm) * N1;

    int lx = (x + N1 - 1) & Nm;
    int mx = x;
    int rx = (x + 1) & Nm;

    int alive_count = cell_arr[lx + ly + lz] + cell_arr[lx + ly + mz] +
                      cell_arr[lx + ly + rz] + cell_arr[lx + my + lz] +
                      cell_arr[lx + my + mz] + cell_arr[lx + my + rz] +
                      cell_arr[lx + ry + lz] + cell_arr[lx + ry + mz] +
                      cell_arr[lx + ry + rz] + cell_arr[mx + ly + lz] +
                      cell_arr[mx + ly + mz] + cell_arr[mx + ly + rz] +
                      cell_arr[mx + my + lz] + cell_arr[mx + my + rz] +
                      cell_arr[mx + ry + lz] + cell_arr[mx + ry + mz] +
                      cell_arr[mx + ry + rz] + cell_arr[rx + ly + lz] +
                      cell_arr[rx + ly + mz] + cell_arr[rx + ly + rz] +
                      cell_arr[rx + my + lz] + cell_arr[rx + my + mz] +
                      cell_arr[rx + my + rz] + cell_arr[rx + ry + lz] +
                      cell_arr[rx + ry + mz] + cell_arr[rx + ry + rz];

    uint8_t alive = cell_arr[idx];

    out_arr[idx] = !((alive == 1 && (alive_count < 5 || alive_count > 7)) ||
                     (alive == 0 && alive_count ^ 6));
}

void evolve(uint8_t *cell_arr, uint8_t *out_arr, int n, int t) {
    uint8_t *_in, *_out;
    

    int N2_ptr = n * n;
    int Nm_ptr = n - 1;
    int n_ptr = n;

    size_t num_elem = n * N2_ptr;

    int r;
    if (n == 256) {
        r = 8;
    } else if (n == 512) {
        r = 9;
    } else if (n == 1024) {
        r = 10;
    } else {
        r = 11;
    }

    cudaMemcpyToSymbol(N2, &N2_ptr, sizeof(int));
    cudaMemcpyToSymbol(Nm, &Nm_ptr, sizeof(int));
    cudaMemcpyToSymbol(N1, &n_ptr, sizeof(int));
    cudaMemcpyToSymbol(R, &r, sizeof(int));

    cudaMallocManaged(&_in, num_elem * sizeof(uint8_t));
    cudaMallocManaged(&_out, num_elem * sizeof(uint8_t));

    cudaMemcpy(_in, cell_arr, num_elem * sizeof(uint8_t), cudaMemcpyHostToDevice);

    int threadsPerBlock = 512;
    int blocks = (num_elem + threadsPerBlock - 1) / threadsPerBlock;

    cudaStream_t stream;
    cudaStreamCreate(&stream);

    for (int i = 0; i < t; i++) {
        evolve_kernel<<<blocks, threadsPerBlock, 0, stream>>>(_in, _out);
        std::swap(_in, _out);
    }

    cudaStreamSynchronize(stream);
    cudaStreamDestroy(stream);

    cudaMemcpy(out_arr, _in, num_elem * sizeof(uint8_t), cudaMemcpyDeviceToHost);

    cudaFree(_in);
    cudaFree(_out);
}


// void evolve(uint8_t *cell_arr, uint8_t *out_arr, int n, int t) {
//     uint8_t *_in, *_out;
//     size_t num_elem;

//     num_elem = n * n * n;

//     int r;
//     if (n == 256) {
//         r = 8;
//     } else if (n == 512) {
//         r = 9;
//     } else if (n == 1024) {
//         r = 10;
//     } else {
//         r = 11;
//     }

//     cudaMallocManaged(&_in, num_elem * sizeof(uint8_t));
//     cudaMallocManaged(&_out, num_elem * sizeof(uint8_t));

//     for (size_t i = 0; i < num_elem; i++) {
//         _in[i] = cell_arr[i];
//     }

//     int threadsPerBlock = 512;
//     int blocks = (num_elem + 1) / threadsPerBlock;

//     for (int i = 0; i < t; i++) {
//         evolve_kernel<<<blocks, threadsPerBlock>>>(_in, _out, n, r);
//         std::swap(_in, _out);
//     }

//     std::swap(_in, _out);

//     cudaDeviceSynchronize();

//     cudaFree(_in);

//     for (size_t i = 0; i < num_elem; i++) {
//         out_arr[i] = _out[i];
//     }

//     cudaFree(_out);
// }

namespace fs = std::filesystem;

int main(int argc, char *argv[]) {
    if (argc < 4) {
        std::cout << "Usage: " << argv[0] << " <input_path> <output_path> <N>"
                  << std::endl;
        return 1;
    }

    auto start = std::chrono::high_resolution_clock::now();

    fs::path input_path = argv[1];
    fs::path output_path = argv[2];
    int N = std::atoi(argv[3]);

    size_t M, T;
    std::ifstream input_file(input_path, std::ios::binary);
    input_file.read(reinterpret_cast<char *>(&M), sizeof(M));
    input_file.read(reinterpret_cast<char *>(&T), sizeof(T));

    uint8_t *curr_space = new uint8_t[M * M * M],
            *next_space = new uint8_t[M * M * M];

    input_file.read(reinterpret_cast<char *>(curr_space), M * M * M);

    evolve(curr_space, next_space, M, N);

    T += N;
    std::ofstream output_file(output_path, std::ios::binary);
    output_file.write(reinterpret_cast<char *>(&M), sizeof(M));
    output_file.write(reinterpret_cast<char *>(&T), sizeof(T));
    output_file.write(reinterpret_cast<char *>(next_space), M * M * M);

    delete[] curr_space;
    delete[] next_space;

    auto end = std::chrono::high_resolution_clock::now();
    printf(
        "Time taken: %f\n",
        std::chrono::duration_cast<std::chrono::duration<double>>(end - start)
            .count());

    return 0;
}
