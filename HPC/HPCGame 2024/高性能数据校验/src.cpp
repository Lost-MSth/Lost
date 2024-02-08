#include <mpi.h>
#include <openssl/evp.h>
#include <openssl/sha.h>

#include <algorithm>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace fs = std::filesystem;

constexpr size_t BLOCK_SIZE = 1024 * 1024;
const int CORE_NUM = 8;
// const int BLOCK_NUM = 1;  // 连续读取的块数

void print_checksum(std::ostream &os, uint8_t *md, size_t len);

int get_checksum(int rank, const size_t file_size, fs::path input_path,
                 uint8_t *obuf) {
    constexpr size_t BUFFER_SIZE = BLOCK_SIZE;  // 读取的缓冲区大小
    int num_block = file_size / BLOCK_SIZE;     // 总块数，向下取整
    int all_num = num_block / CORE_NUM;         // 总大循环个数
    int end_rank = num_block - all_num * CORE_NUM;  // 余数，最后结果在的进程号
    // int end_rank;  //
    // if (end_rank == 0) {
    //     end_rank = CORE_NUM - 1;
    // } else {
    //     end_rank = end_rank - 1;
    // }

    uint8_t prev_md[SHA512_DIGEST_LENGTH];  // 上一次的 sha512 结果
    std::ifstream istrm(input_path, std::ios::binary);  // 读取文件

    if (rank == 0) {
        SHA512(nullptr, 0, prev_md);
    }

    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_MD *sha512 = EVP_MD_fetch(nullptr, "SHA512", nullptr);

    for (int i = 0; i < all_num + 1; i++) {
        if (rank >= end_rank && i == all_num) {
            // 最后一个进程的最后一次循环
            // 最后一块不跑，可能不满一块
            break;
        }
        uint8_t buffer[BUFFER_SIZE]{};
        istrm.seekg((rank + CORE_NUM * i) * BUFFER_SIZE);
        istrm.read(reinterpret_cast<char *>(buffer), BUFFER_SIZE);
        EVP_DigestInit_ex(ctx, sha512, nullptr);
        EVP_DigestUpdate(ctx, buffer, BUFFER_SIZE);
        if (rank != 0) {
            // 从前一个进程获取 prev_md
            MPI_Recv(&prev_md, SHA512_DIGEST_LENGTH, MPI_BYTE, rank - 1,
                     rank + CORE_NUM * i - 1, MPI_COMM_WORLD,
                     MPI_STATUS_IGNORE);

            EVP_DigestUpdate(ctx, prev_md, SHA512_DIGEST_LENGTH);
            unsigned int len = 0;
            EVP_DigestFinal_ex(ctx, prev_md, &len);

            // 发送 prev_md 到下一个进程
            int next_rank = rank + 1;
            if (next_rank == CORE_NUM) {
                next_rank = 0;
            }
            MPI_Send(&prev_md, SHA512_DIGEST_LENGTH, MPI_BYTE, next_rank,
                     rank + CORE_NUM * i, MPI_COMM_WORLD);
        } else {
            if (i != 0) {
                // 从最后一个进程获取 prev_md
                MPI_Recv(&prev_md, SHA512_DIGEST_LENGTH, MPI_BYTE, CORE_NUM - 1,
                         rank + CORE_NUM * i - 1, MPI_COMM_WORLD,
                         MPI_STATUS_IGNORE);
            }
            EVP_DigestUpdate(ctx, prev_md, SHA512_DIGEST_LENGTH);
            unsigned int len = 0;
            EVP_DigestFinal_ex(ctx, prev_md, &len);

            // 发送 prev_md 到下一个进程
            MPI_Send(&prev_md, SHA512_DIGEST_LENGTH, MPI_BYTE, 1, CORE_NUM * i,
                     MPI_COMM_WORLD);
        }
    }

    if (rank == end_rank) {
        // 最后一个进程处理剩余数据

        int pre_rank = rank - 1;
        if (pre_rank == -1) {
            pre_rank = CORE_NUM - 1;
        }
        MPI_Recv(&prev_md, SHA512_DIGEST_LENGTH, MPI_BYTE, pre_rank,
                 rank - 1 + CORE_NUM * all_num, MPI_COMM_WORLD,
                 MPI_STATUS_IGNORE);

        size_t offset = num_block * BLOCK_SIZE;
        if ((file_size - offset) != 0) {
            uint8_t data[file_size - offset]{};
            istrm.seekg(offset);
            istrm.read(reinterpret_cast<char *>(data), file_size - offset);

            uint8_t buffer[BLOCK_SIZE]{};

            EVP_DigestInit_ex(ctx, sha512, nullptr);

            std::memcpy(buffer, data, file_size - offset);

            EVP_DigestUpdate(ctx, buffer, BLOCK_SIZE);
            EVP_DigestUpdate(ctx, prev_md, SHA512_DIGEST_LENGTH);

            unsigned int len = 0;
            EVP_DigestFinal_ex(ctx, prev_md, &len);
        }
        std::memcpy(obuf, prev_md, SHA512_DIGEST_LENGTH);
    }
    EVP_MD_CTX_free(ctx);
    EVP_MD_free(sha512);

    return end_rank;
}

int main(int argc, char *argv[]) {
    MPI_Init(&argc, &argv);

    int rank, nprocs;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &nprocs);

    if (argc < 3) {
        std::cout << "Usage: " << argv[0] << " <input_file> <output_file>"
                  << std::endl;
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    fs::path input_path = argv[1];
    fs::path output_path = argv[2];

    auto total_begin_time = std::chrono::high_resolution_clock::now();

    auto file_size = fs::file_size(input_path);
    std::cout << input_path << " size: " << file_size << std::endl;

    uint8_t obuf[SHA512_DIGEST_LENGTH];

    auto begin_time = std::chrono::high_resolution_clock::now();
    int end_rank = get_checksum(rank, file_size, input_path, obuf);
    auto end_time = std::chrono::high_resolution_clock::now();

    if (rank == end_rank) {
        // 最后一个进程输出结果
        std::cout << "checksum: ";
        print_checksum(std::cout, obuf, SHA512_DIGEST_LENGTH);
        std::cout << std::endl;

        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
            end_time - begin_time);

        std::cout << "checksum time cost: " << std::dec << duration.count()
                  << "ms" << std::endl;

        // write checksum to output file
        std::ofstream output_file(output_path);

        print_checksum(output_file, obuf, SHA512_DIGEST_LENGTH);

        auto total_end_time = std::chrono::high_resolution_clock::now();

        auto total_duration =
            std::chrono::duration_cast<std::chrono::milliseconds>(
                total_end_time - total_begin_time);

        std::cout << "total time cost: " << total_duration.count() << "ms"
                  << std::endl;
    }

    MPI_Finalize();

    return 0;
}

void print_checksum(std::ostream &os, uint8_t *md, size_t len) {
    for (int i = 0; i < len; i++) {
        os << std::setw(2) << std::setfill('0') << std::hex
           << static_cast<int>(md[i]);
    }
}

// void checksum_0(uint8_t *data, size_t len, uint8_t *obuf) {
//     int num_block = (len + BLOCK_SIZE - 1) / BLOCK_SIZE;
//     uint8_t prev_md[SHA512_DIGEST_LENGTH];

//     EVP_MD_CTX *ctx = EVP_MD_CTX_new();
//     EVP_MD *sha512 = EVP_MD_fetch(nullptr, "SHA512", nullptr);

//     SHA512(nullptr, 0, prev_md);
//     for (int i = 0; i < num_block; i++) {
//         uint8_t buffer[BLOCK_SIZE]{};
//         EVP_DigestInit_ex(ctx, sha512, nullptr);
//         std::memcpy(buffer, data + i * BLOCK_SIZE,
//                     std::min(BLOCK_SIZE, len - i * BLOCK_SIZE));
//         EVP_DigestUpdate(ctx, buffer, BLOCK_SIZE);
//         EVP_DigestUpdate(ctx, prev_md, SHA512_DIGEST_LENGTH);

//         unsigned int len = 0;
//         EVP_DigestFinal_ex(ctx, prev_md, &len);
//     }

//     std::memcpy(obuf, prev_md, SHA512_DIGEST_LENGTH);
//     EVP_MD_CTX_free(ctx);
//     EVP_MD_free(sha512);
// }
