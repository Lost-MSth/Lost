/**
 * gen.cpp - 数据生成器
 * 
 * 用法: ./gen <op_type> <n> <k> <alpha> <beta> <uplo> <trans> <seed> <output>
 *   op_type: ssyrk 或 ssyr2k
 *   uplo: upper 或 lower
 *   trans: notrans 或 trans
 * 
 * 例如: ./gen ssyrk 31 2 1.0 0.0 upper notrans 12345 input.bin
 */

#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <random>
#include <fstream>

// 操作类型
enum OpType { OP_SSYRK = 0, OP_SSYR2K = 1 };

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

void init_random_matrix(float* M, int rows, int cols, int ld, unsigned seed) {
    std::mt19937 gen(seed);
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
    
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            M[i + j * ld] = dist(gen);
        }
    }
}

void print_usage(const char* prog) {
    fprintf(stderr, "用法: %s <op_type> <n> <k> <alpha> <beta> <uplo> <trans> <seed> <output>\n", prog);
    fprintf(stderr, "  op_type: ssyrk 或 ssyr2k\n");
    fprintf(stderr, "  uplo: upper 或 lower\n");
    fprintf(stderr, "  trans: notrans 或 trans\n");
    fprintf(stderr, "例如: %s ssyrk 31 2 1.0 0.0 upper notrans 12345 input.bin\n", prog);
}

int main(int argc, char** argv) {
    if (argc != 10) {
        print_usage(argv[0]);
        return 1;
    }

    // 解析参数
    OpType op_type;
    if (strcmp(argv[1], "ssyrk") == 0) {
        op_type = OP_SSYRK;
    } else if (strcmp(argv[1], "ssyr2k") == 0) {
        op_type = OP_SSYR2K;
    } else {
        fprintf(stderr, "错误: 未知的操作类型 '%s'\n", argv[1]);
        return 1;
    }

    int n = atoi(argv[2]);
    int k = atoi(argv[3]);
    float alpha = atof(argv[4]);
    float beta = atof(argv[5]);

    int uplo;
    if (strcmp(argv[6], "upper") == 0) {
        uplo = 0;  // Upper
    } else if (strcmp(argv[6], "lower") == 0) {
        uplo = 1;  // Lower
    } else {
        fprintf(stderr, "错误: uplo 必须是 'upper' 或 'lower'\n");
        return 1;
    }

    int trans;
    if (strcmp(argv[7], "notrans") == 0) {
        trans = 0;  // NoTrans
    } else if (strcmp(argv[7], "trans") == 0) {
        trans = 1;  // Trans
    } else {
        fprintf(stderr, "错误: trans 必须是 'notrans' 或 'trans'\n");
        return 1;
    }

    unsigned seed = atoi(argv[8]);
    const char* output_file = argv[9];

    // 计算矩阵维度
    int lda = (trans == 0) ? n + 1 : k + 1;  // NoTrans: n+1, Trans: k+1
    int ldb = (trans == 0) ? n + 1 : k + 1;
    int ldc = n + 1;

    int rows_a = (trans == 0) ? n : k;
    int cols_a = (trans == 0) ? k : n;

    // 准备文件头
    Header header;
    header.op_type = op_type;
    header.uplo = uplo;
    header.trans = trans;
    header.n = n;
    header.k = k;
    header.lda = lda;
    header.ldb = (op_type == OP_SSYR2K) ? ldb : 0;
    header.ldc = ldc;
    header.alpha = alpha;
    header.beta = beta;

    // 计算内存大小
    size_t size_A = (size_t)lda * cols_a;
    size_t size_B = (op_type == OP_SSYR2K) ? (size_t)ldb * cols_a : 0;
    size_t size_C = (size_t)ldc * n;

    printf("生成数据:\n");
    printf("  操作: %s\n", op_type == OP_SSYRK ? "SSYRK" : "SSYR2K");
    printf("  参数: N=%d, K=%d, alpha=%.1f, beta=%.1f\n", n, k, alpha, beta);
    printf("  uplo=%s, trans=%s\n", uplo == 0 ? "Upper" : "Lower", trans == 0 ? "NoTrans" : "Trans");
    printf("  lda=%d, ldb=%d, ldc=%d\n", lda, header.ldb, ldc);
    printf("  矩阵 A: %d x %d (%.2f MB)\n", rows_a, cols_a, size_A * sizeof(float) / 1024.0 / 1024.0);
    if (op_type == OP_SSYR2K) {
        printf("  矩阵 B: %d x %d (%.2f MB)\n", rows_a, cols_a, size_B * sizeof(float) / 1024.0 / 1024.0);
    }
    printf("  矩阵 C: %d x %d (%.2f MB)\n", n, n, size_C * sizeof(float) / 1024.0 / 1024.0);

    // 分配内存
    float* A = new float[size_A];
    float* B = (op_type == OP_SSYR2K) ? new float[size_B] : nullptr;
    float* C = new float[size_C];

    // 生成随机数据
    printf("生成随机矩阵...\n");
    init_random_matrix(A, rows_a, cols_a, lda, seed);
    if (op_type == OP_SSYR2K) {
        init_random_matrix(B, rows_a, cols_a, ldb, seed + 10000);
    }
    init_random_matrix(C, n, n, ldc, seed + 20000);

    // 写入文件
    printf("写入文件: %s\n", output_file);
    std::ofstream out(output_file, std::ios::binary);
    if (!out) {
        fprintf(stderr, "错误: 无法打开输出文件 '%s'\n", output_file);
        return 1;
    }

    out.write(reinterpret_cast<const char*>(&header), sizeof(Header));
    out.write(reinterpret_cast<const char*>(A), size_A * sizeof(float));
    if (op_type == OP_SSYR2K) {
        out.write(reinterpret_cast<const char*>(B), size_B * sizeof(float));
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
