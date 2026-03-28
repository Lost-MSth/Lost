/**
 * checker.cpp - 浮点数误差检查器
 * 
 * 用法: ./checker <input> <reference> <output> [tolerance]
 *   input: 输入文件（包含参数信息）
 *   reference: 参考答案文件
 *   output: 待检查的输出文件
 *   tolerance: 误差容限（默认 1e-4）
 * 
 * 例如: ./checker input.bin ref.bin output.bin 1e-4
 */

#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cmath>
#include <fstream>

// 文件头结构（用于读取参数）
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

bool verify_result(const float* C_ref, const float* C_test, 
                   int uplo, int n, int ldc, float tol) {
    float max_diff = 0.0f;
    float max_rel_diff = 0.0f;
    int max_i = 0, max_j = 0;
    bool passed = true;
    int error_count = 0;

    for (int j = 0; j < n; j++) {
        int i_start = (uplo == 0) ? 0 : j;      // Upper: 0, Lower: j
        int i_end = (uplo == 0) ? j + 1 : n;    // Upper: j+1, Lower: n
        for (int i = i_start; i < i_end; i++) {
            float ref_val = C_ref[i + j * ldc];
            float test_val = C_test[i + j * ldc];
            float diff = fabsf(ref_val - test_val);
            float rel_diff = diff / (fabsf(ref_val) + 1e-10f);
            
            if (rel_diff > tol || diff > tol) {
                error_count++;
                if (diff > max_diff) {
                    max_diff = diff;
                    max_rel_diff = rel_diff;
                    max_i = i;
                    max_j = j;
                }
                passed = false;
            }
        }
    }

    if (!passed) {
        printf("验证失败!\n");
        printf("  错误元素数量: %d\n", error_count);
        printf("  最大差异在 C[%d,%d]:\n", max_i, max_j);
        printf("    ref  = %e\n", C_ref[max_i + max_j * ldc]);
        printf("    test = %e\n", C_test[max_i + max_j * ldc]);
        printf("    diff = %e\n", max_diff);
        printf("    rel_diff = %e\n", max_rel_diff);
    } else {
        printf("验证通过!\n");
        printf("  所有元素差异 < %e\n", tol);
    }

    return passed;
}

int main(int argc, char** argv) {
    if (argc < 4 || argc > 5) {
        fprintf(stderr, "用法: %s <input> <reference> <output> [tolerance]\n", argv[0]);
        fprintf(stderr, "  input: 输入文件（包含参数信息）\n");
        fprintf(stderr, "  reference: 参考答案文件\n");
        fprintf(stderr, "  output: 待检查的输出文件\n");
        fprintf(stderr, "  tolerance: 误差容限（默认 1e-4）\n");
        fprintf(stderr, "例如: %s input.bin ref.bin output.bin 1e-4\n", argv[0]);
        return 1;
    }

    const char* input_file = argv[1];
    const char* ref_file = argv[2];
    const char* output_file = argv[3];
    float tolerance = (argc >= 5) ? atof(argv[4]) : 1e-4f;

    // 读取输入文件头以获取参数
    std::ifstream in(input_file, std::ios::binary);
    if (!in) {
        fprintf(stderr, "错误: 无法打开输入文件 '%s'\n", input_file);
        return 1;
    }

    Header header;
    in.read(reinterpret_cast<char*>(&header), sizeof(Header));
    in.close();

    printf("误差检查器\n");
    printf("  操作: %s\n", header.op_type == 0 ? "SSYRK" : "SSYR2K");
    printf("  参数: N=%d, K=%d, ldc=%d\n", header.n, header.k, header.ldc);
    printf("  uplo=%s\n", header.uplo == 0 ? "Upper" : "Lower");
    printf("  误差容限: %e\n", tolerance);

    int n = header.n;
    int ldc = header.ldc;
    int uplo = header.uplo;
    size_t size_C = (size_t)ldc * n;

    // 分配内存
    float* C_ref = new float[size_C];
    float* C_test = new float[size_C];

    // 读取参考答案
    std::ifstream ref_in(ref_file, std::ios::binary);
    if (!ref_in) {
        fprintf(stderr, "错误: 无法打开参考答案文件 '%s'\n", ref_file);
        return 1;
    }
    ref_in.read(reinterpret_cast<char*>(C_ref), size_C * sizeof(float));
    ref_in.close();

    // 读取待检查的输出
    std::ifstream out_in(output_file, std::ios::binary);
    if (!out_in) {
        fprintf(stderr, "错误: 无法打开输出文件 '%s'\n", output_file);
        return 1;
    }
    out_in.read(reinterpret_cast<char*>(C_test), size_C * sizeof(float));
    out_in.close();

    // 验证结果
    printf("\n比较 %s vs %s\n", ref_file, output_file);
    bool passed = verify_result(C_ref, C_test, uplo, n, ldc, tolerance);

    // 清理
    delete[] C_ref;
    delete[] C_test;

    return passed ? 0 : 1;
}
