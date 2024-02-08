#include <cuda_runtime.h>

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <utility>

__constant__ int N2;
__constant__ int Nm;
__constant__ int N1;
__constant__ int R;

__device__ inline int get_idx(int x, int y, int z) {
    int xx = (x + N1) & Nm;
    int yy = (y + N1) & Nm;
    int zz = (z + N1) & Nm;
    return zz * N2 + yy * N1 + xx;
}

__global__ void evolve_kernel(uint8_t *cell_arr, uint8_t *out_arr) {
    // size_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    // N2 = N * N

    int thx = threadIdx.x;
    int thy = threadIdx.y;
    int thz = threadIdx.z;

    int x = blockIdx.x * 8 + thx - 1;
    int y = blockIdx.y * 8 + thy - 1;
    int z = blockIdx.z * 8 + thz - 1;
    // size_t idx = x * N2 + y * N1 + z;
    size_t idx = get_idx(x, y, z);

    __shared__ uint8_t cell_arr_shared[1000];
    uint8_t alive = cell_arr[idx];
    int mx = thx + 1;
    int my = (thy + 1) * 10;
    int mz = (thz + 1) * 100;

    cell_arr_shared[mx + my + mz] = alive;

    __syncthreads();

    int lx = thx;
    int rx = thx + 2;
    int ly = my - 10;
    int ry = my + 10;
    int lz = mz - 100;
    int rz = mz + 100;

    if (thx >= 1 && thx <= 8 && thy >= 1 && thy <= 8 && thz >= 1 && thz <= 8) {
        int alive_count =
            cell_arr_shared[lx + ly + lz] + cell_arr_shared[lx + ly + mz] +
            cell_arr_shared[lx + ly + rz] + cell_arr_shared[lx + my + lz] +
            cell_arr_shared[lx + my + mz] + cell_arr_shared[lx + my + rz] +
            cell_arr_shared[lx + ry + lz] + cell_arr_shared[lx + ry + mz] +
            cell_arr_shared[lx + ry + rz] + cell_arr_shared[mx + ly + lz] +
            cell_arr_shared[mx + ly + mz] + cell_arr_shared[mx + ly + rz] +
            cell_arr_shared[mx + my + lz] + cell_arr_shared[mx + my + rz] +
            cell_arr_shared[mx + ry + lz] + cell_arr_shared[mx + ry + mz] +
            cell_arr_shared[mx + ry + rz] + cell_arr_shared[rx + ly + lz] +
            cell_arr_shared[rx + ly + mz] + cell_arr_shared[rx + ly + rz] +
            cell_arr_shared[rx + my + lz] + cell_arr_shared[rx + my + mz] +
            cell_arr_shared[rx + my + rz] + cell_arr_shared[rx + ry + lz] +
            cell_arr_shared[rx + ry + mz] + cell_arr_shared[rx + ry + rz];

        out_arr[idx] = !((alive == 1 && (alive_count < 5 || alive_count > 7)) ||
                         (alive == 0 && alive_count ^ 6));
    }
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

    cudaMemcpy(_in, cell_arr, num_elem * sizeof(uint8_t),
               cudaMemcpyHostToDevice);

    dim3 threadsPerBlock(10, 10, 10);
    dim3 blocks(n / 8, n / 8, n / 8);

    // int threadsPerBlock = 512;
    // int blocks = (num_elem + threadsPerBlock - 1) / threadsPerBlock;

    size_t shared_mem = sizeof(uint8_t) * 1000;

    cudaStream_t stream;
    cudaStreamCreate(&stream);

    for (int i = 0; i < t; i++) {
        evolve_kernel<<<blocks, threadsPerBlock, shared_mem, stream>>>(_in,
                                                                       _out);
        std::swap(_in, _out);
    }

    cudaStreamSynchronize(stream);
    cudaStreamDestroy(stream);

    cudaMemcpy(out_arr, _in, num_elem * sizeof(uint8_t),
               cudaMemcpyDeviceToHost);

    cudaFree(_in);
    cudaFree(_out);
}

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
