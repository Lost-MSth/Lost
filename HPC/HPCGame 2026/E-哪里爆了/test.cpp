/**
 * test.cpp - CBLAS 测试程序
 * 
 * 用法: ./test <input> <output>
 * 
 * 例如: ./test input.bin output.bin
 */

#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <chrono>
#include <cblas.h>

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

int main(int argc, char** argv) {
    if (argc != 3) {
        fprintf(stderr, "用法: %s <input> <output>\n", argv[0]);
        fprintf(stderr, "例如: %s input.bin output.bin\n", argv[0]);
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

    printf("CBLAS 测试程序\n");
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

    // 转换参数
    CBLAS_UPLO cblas_uplo = (header.uplo == 0) ? CblasUpper : CblasLower;
    CBLAS_TRANSPOSE cblas_trans = (header.trans == 0) ? CblasNoTrans : CblasTrans;

    // 执行 CBLAS 操作
    printf("运行 CBLAS 实现...\n");
    auto t1 = std::chrono::high_resolution_clock::now();

    if (header.op_type == 0) {
        cblas_ssyrk(CblasColMajor, cblas_uplo, cblas_trans,
                    n, k, header.alpha, A, lda, header.beta, C, ldc);
    } else {
        cblas_ssyr2k(CblasColMajor, cblas_uplo, cblas_trans,
                     n, k, header.alpha, A, lda, B, ldb, header.beta, C, ldc);
    }

    auto t2 = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t2 - t1).count();
    fprintf(stderr, "Time: %.6f seconds\n", elapsed);

    // 计算 GFLOPS
    double flops;
    if (header.op_type == 0) {
        // SSYRK: n*(n+1)/2 * 2*k FLOPs
        flops = (double)n * (n + 1) / 2.0 * 2.0 * k;
    } else {
        // SSYR2K: n*(n+1)/2 * 4*k FLOPs
        flops = (double)n * (n + 1) / 2.0 * 4.0 * k;
    }
    double gflops = flops / (elapsed * 1e9);
    printf("  耗时: %.6f 秒\n", elapsed);
    printf("  性能: %.2f GFLOPS\n", gflops);

    // 写入输出文件（只写结果矩阵 C）
    printf("写入结果: %s\n", output_file);
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
