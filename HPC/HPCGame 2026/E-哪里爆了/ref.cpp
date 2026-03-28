/**
 * ref.cpp - 参考答案生成器（使用 naive 实现）
 * 
 * 用法: ./ref <input> <output>
 * 
 * 例如: ./ref input.bin ref.bin
 */

#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <chrono>

// 文件头结构
struct Header {
    int32_t op_type;    // 0=ssyrk, 1=ssyr2k
    int32_t uplo;       // 0=Upper, 1=Lower
    int32_t trans;      // 0=NoTrans, 1=Trans
    int32_t n;
    int32_t k;
    int32_t lda;
    int32_t ldb;        // 仅 ssyr2k 使用，ssyrk 时为0
    int32_t ldc;
    float alpha;
    float beta;
};

// Naive SSYRK 实现
void naive_ssyrk(int uplo, int trans,
                 int n, int k, float alpha,
                 const float* A, int lda,
                 float beta, float* C, int ldc) {
    // 先乘以 beta
    for (int j = 0; j < n; j++) {
        int i_start = (uplo == 0) ? 0 : j;      // Upper: 0, Lower: j
        int i_end = (uplo == 0) ? j + 1 : n;    // Upper: j+1, Lower: n
        for (int i = i_start; i < i_end; i++) {
            C[i + j * ldc] *= beta;
        }
    }

    // 计算 alpha * A * A^T 或 alpha * A^T * A
    if (trans == 0) {  // NoTrans: C += alpha * A * A^T
        for (int j = 0; j < n; j++) {
            int i_start = (uplo == 0) ? 0 : j;
            int i_end = (uplo == 0) ? j + 1 : n;
            for (int i = i_start; i < i_end; i++) {
                float sum = 0.0f;
                for (int p = 0; p < k; p++) {
                    sum += A[i + p * lda] * A[j + p * lda];
                }
                C[i + j * ldc] += alpha * sum;
            }
        }
    } else {  // Trans: C += alpha * A^T * A
        for (int j = 0; j < n; j++) {
            int i_start = (uplo == 0) ? 0 : j;
            int i_end = (uplo == 0) ? j + 1 : n;
            for (int i = i_start; i < i_end; i++) {
                float sum = 0.0f;
                for (int p = 0; p < k; p++) {
                    sum += A[p + i * lda] * A[p + j * lda];
                }
                C[i + j * ldc] += alpha * sum;
            }
        }
    }
}

// Naive SSYR2K 实现
void naive_ssyr2k(int uplo, int trans,
                  int n, int k, float alpha,
                  const float* A, int lda,
                  const float* B, int ldb,
                  float beta, float* C, int ldc) {
    // 先乘以 beta
    for (int j = 0; j < n; j++) {
        int i_start = (uplo == 0) ? 0 : j;
        int i_end = (uplo == 0) ? j + 1 : n;
        for (int i = i_start; i < i_end; i++) {
            C[i + j * ldc] *= beta;
        }
    }

    // 计算 alpha * (A * B^T + B * A^T) 或 alpha * (A^T * B + B^T * A)
    if (trans == 0) {  // NoTrans
        for (int j = 0; j < n; j++) {
            int i_start = (uplo == 0) ? 0 : j;
            int i_end = (uplo == 0) ? j + 1 : n;
            for (int i = i_start; i < i_end; i++) {
                float sum = 0.0f;
                for (int p = 0; p < k; p++) {
                    sum += A[i + p * lda] * B[j + p * ldb];
                    sum += B[i + p * ldb] * A[j + p * lda];
                }
                C[i + j * ldc] += alpha * sum;
            }
        }
    } else {  // Trans
        for (int j = 0; j < n; j++) {
            int i_start = (uplo == 0) ? 0 : j;
            int i_end = (uplo == 0) ? j + 1 : n;
            for (int i = i_start; i < i_end; i++) {
                float sum = 0.0f;
                for (int p = 0; p < k; p++) {
                    sum += A[p + i * lda] * B[p + j * ldb];
                    sum += B[p + i * ldb] * A[p + j * lda];
                }
                C[i + j * ldc] += alpha * sum;
            }
        }
    }
}

int main(int argc, char** argv) {
    if (argc != 3) {
        fprintf(stderr, "用法: %s <input> <output>\n", argv[0]);
        fprintf(stderr, "例如: %s input.bin ref.bin\n", argv[0]);
        return 1;
    }

    const char* input_file = argv[1];
    const char* output_file = argv[2];

    // 读取输入文件
    std::ifstream in(input_file, std::ios::binary);
    if (!in) {
        fprintf(stderr, "错误: 无法打开输入文件 '%s'\n", input_file);
        return 1;
    }

    // 读取文件头
    Header header;
    in.read(reinterpret_cast<char*>(&header), sizeof(Header));

    printf("参考答案生成器 (Naive 实现)\n");
    printf("  操作: %s\n", header.op_type == 0 ? "SSYRK" : "SSYR2K");
    printf("  参数: N=%d, K=%d, alpha=%.1f, beta=%.1f\n", 
           header.n, header.k, header.alpha, header.beta);
    printf("  uplo=%s, trans=%s\n", 
           header.uplo == 0 ? "Upper" : "Lower",
           header.trans == 0 ? "NoTrans" : "Trans");

    int n = header.n;
    int k = header.k;
    int lda = header.lda;
    int ldb = header.ldb;
    int ldc = header.ldc;
    
    int cols_a = (header.trans == 0) ? k : n;
    
    size_t size_A = (size_t)lda * cols_a;
    size_t size_B = (header.op_type == 1) ? (size_t)ldb * cols_a : 0;
    size_t size_C = (size_t)ldc * n;

    // 分配内存
    float* A = new float[size_A];
    float* B = (header.op_type == 1) ? new float[size_B] : nullptr;
    float* C = new float[size_C];

    // 读取矩阵数据
    in.read(reinterpret_cast<char*>(A), size_A * sizeof(float));
    if (header.op_type == 1) {
        in.read(reinterpret_cast<char*>(B), size_B * sizeof(float));
    }
    in.read(reinterpret_cast<char*>(C), size_C * sizeof(float));
    in.close();

    // 执行计算
    printf("运行 naive 实现...\n");
    auto t1 = std::chrono::high_resolution_clock::now();

    if (header.op_type == 0) {
        naive_ssyrk(header.uplo, header.trans, n, k, header.alpha,
                    A, lda, header.beta, C, ldc);
    } else {
        naive_ssyr2k(header.uplo, header.trans, n, k, header.alpha,
                     A, lda, B, ldb, header.beta, C, ldc);
    }

    auto t2 = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t2 - t1).count();
    fprintf(stderr, "Time: %.6f seconds\n", elapsed);

    // 写入输出文件（只写结果矩阵 C）
    printf("写入参考答案: %s\n", output_file);
    std::ofstream out(output_file, std::ios::binary);
    if (!out) {
        fprintf(stderr, "错误: 无法打开输出文件 '%s'\n", output_file);
        return 1;
    }
    out.write(reinterpret_cast<const char*>(C), size_C * sizeof(float));
    out.close();

    printf("完成!\n");

    // 清理
    delete[] A;
    delete[] B;
    delete[] C;

    return 0;
}
