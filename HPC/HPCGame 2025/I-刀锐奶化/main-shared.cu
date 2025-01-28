// #include <math.h>
#include <cuda_runtime.h>
#include <malloc.h>
#include <stdint.h>
#include <stdio.h>

typedef double d_t;
struct d3_t {
    d_t x, y, z;
};

__device__ __host__ inline d_t norm(d3_t x) { 
    // return norm3d(x.x, x.y, x.z);
    return sqrt(x.x * x.x + x.y * x.y + x.z * x.z); 
    }

__device__ __host__ inline d3_t operator-(d3_t a, d3_t b) {
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}


__global__ void compute(d3_t* __restrict__ mir, d3_t* __restrict__ sen, d_t * __restrict__ d_src_mirn_norm, d_t* __restrict__ data, int64_t mirn,
                        int64_t senn) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= senn) return;

    extern __shared__ d3_t shared[1024];

    d3_t sen_i = sen[i];

    d_t a = 0;
    d_t b = 0;
    d_t tmp_sin = 0;
    d_t tmp_cos = 0;

    int times = mirn / blockDim.x;

    for (int t = 0; t < times; ++t) {
        shared[threadIdx.x] = mir[t * blockDim.x + threadIdx.x];
        __syncthreads();

        #pragma unroll
        for (int j = 0; j < blockDim.x; ++j) {
            d_t l = d_src_mirn_norm[t * blockDim.x + j] + norm(shared[j] - sen_i);
            sincospi(4000 * l, &tmp_sin, &tmp_cos);
            a += tmp_cos;
            b += tmp_sin;
        }
        __syncthreads();
    }
    // for (int64_t j = 0; j < mirn; j++) {
    //     // d_t l = norm(mir[j] - src) + norm(mir[j] - sen_i);
    //     d_t l = d_src_mirn_norm[j] + norm(mir[j] - sen_i);
    //     // d_t tmp = 4000 * l;
    //     // a += cospi(tmp);
    //     // b += sinpi(tmp);
        
    //     sincospi(4000 * l, &tmp_sin, &tmp_cos);

    //     // printf("l = %f tmp_sin = %f tmp_cos = %f\n", l, tmp_sin, tmp_cos);

    //     a += tmp_cos;
    //     b += tmp_sin;
    // }
    // data[i] = sqrt(a * a + b * b);
    data[i] = hypot(a, b);
}

#define CONST 602

int main() {
    FILE* fi;
    fi = fopen("in.data", "rb");
    d3_t src;
    int64_t mirn, senn;
    d3_t *mir, *sen;

    fread(&src, 1, sizeof(d3_t), fi);

    fread(&mirn, 1, sizeof(int64_t), fi);
    mir = (d3_t*)malloc(mirn * sizeof(d3_t));
    fread(mir, 1, mirn * sizeof(d3_t), fi);

    fread(&senn, 1, sizeof(int64_t), fi);
    sen = (d3_t*)malloc(senn * sizeof(d3_t));
    fread(sen, 1, senn * sizeof(d3_t), fi);

    fclose(fi);

    d_t* data = (d_t*)malloc(senn * sizeof(d_t));

    d3_t *d_mir, *d_sen;
    d_t* d_data;
    d_t* src_mirn_norm = (d_t*)malloc(mirn * sizeof(d_t));

    for (int64_t i = 0; i < mirn; i++) {
        src_mirn_norm[i] = norm(mir[i] - src) - CONST;
    }

    d_t* d_src_mirn_norm;

    cudaMalloc(&d_mir, mirn * sizeof(d3_t));
    cudaMalloc(&d_sen, senn * sizeof(d3_t));
    cudaMalloc(&d_data, senn * sizeof(d_t));
    cudaMalloc(&d_src_mirn_norm, mirn * sizeof(d_t));

    cudaMemcpy(d_mir, mir, mirn * sizeof(d3_t), cudaMemcpyHostToDevice);
    cudaMemcpy(d_sen, sen, senn * sizeof(d3_t), cudaMemcpyHostToDevice);
    cudaMemcpy(d_src_mirn_norm, src_mirn_norm, mirn * sizeof(d_t), cudaMemcpyHostToDevice);
 

    int blockSize = 1024;
    int numBlocks = (senn + blockSize - 1) / blockSize;

    fprintf(stderr, "numBlocks = %d\n", numBlocks);
    fprintf(stderr, "blockSize = %d\n", blockSize);

    compute<<<numBlocks, blockSize, 1024 * sizeof(d3_t)>>>(d_mir, d_sen, d_src_mirn_norm, d_data, mirn, senn);

    cudaMemcpy(data, d_data, senn * sizeof(d_t), cudaMemcpyDeviceToHost);

    cudaFree(d_mir);
    cudaFree(d_sen);
    cudaFree(d_data);
    cudaFree(d_src_mirn_norm);

    fi = fopen("out.data", "wb");
    fwrite(data, 1, senn * sizeof(d_t), fi);
    fclose(fi);

    free(mir);
    free(sen);
    free(data);
    free(src_mirn_norm);

    return 0;
}