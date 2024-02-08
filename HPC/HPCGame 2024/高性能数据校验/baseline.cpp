#include <algorithm>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <mpi.h>
#include <openssl/evp.h>
#include <openssl/sha.h>

namespace fs = std::filesystem;

constexpr size_t BLOCK_SIZE = 1024 * 1024;

void checksum_0(uint8_t *data, size_t len, uint8_t *obuf);
void print_checksum(std::ostream &os, uint8_t *md, size_t len);

int main(int argc, char *argv[]) {

  MPI_Init(&argc, &argv);

  int rank, nprocs;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &nprocs);

  if (rank == 0) {
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

    uint8_t *buffer = nullptr;
    if (file_size != 0) {
      buffer = new uint8_t[file_size];

      // read the file content in binary format
      std::ifstream istrm(input_path, std::ios::binary);
      istrm.read(reinterpret_cast<char *>(buffer), file_size);
    }

    // record begin time
    auto begin_time = std::chrono::high_resolution_clock::now();

    // calculate the checksum
    uint8_t obuf[SHA512_DIGEST_LENGTH];
    checksum_0(buffer, file_size, obuf);

    // record end time
    auto end_time = std::chrono::high_resolution_clock::now();

    // print debug information
    std::cout << "checksum: ";
    print_checksum(std::cout, obuf, SHA512_DIGEST_LENGTH);
    std::cout << std::endl;

    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        end_time - begin_time);

    std::cout << "checksum time cost: " << std::dec << duration.count() << "ms"
              << std::endl;

    // write checksum to output file
    std::ofstream output_file(output_path);

    print_checksum(output_file, obuf, SHA512_DIGEST_LENGTH);

    delete[] buffer;

    auto total_end_time = std::chrono::high_resolution_clock::now();

    auto total_duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        total_end_time - total_begin_time);

    std::cout << "total time cost: " << total_duration.count() << "ms"
              << std::endl;
  }

  MPI_Finalize();

  return 0;
}

void checksum_0(uint8_t *data, size_t len, uint8_t *obuf) {
  int num_block = (len + BLOCK_SIZE - 1) / BLOCK_SIZE;
  uint8_t prev_md[SHA512_DIGEST_LENGTH];

  EVP_MD_CTX *ctx = EVP_MD_CTX_new();
  EVP_MD *sha512 = EVP_MD_fetch(nullptr, "SHA512", nullptr);

  SHA512(nullptr, 0, prev_md);
  for (int i = 0; i < num_block; i++) {
    uint8_t buffer[BLOCK_SIZE]{};
    EVP_DigestInit_ex(ctx, sha512, nullptr);
    std::memcpy(buffer, data + i * BLOCK_SIZE,
                std::min(BLOCK_SIZE, len - i * BLOCK_SIZE));
    EVP_DigestUpdate(ctx, buffer, BLOCK_SIZE);
    EVP_DigestUpdate(ctx, prev_md, SHA512_DIGEST_LENGTH);

    unsigned int len = 0;
    EVP_DigestFinal_ex(ctx, prev_md, &len);
  }

  std::memcpy(obuf, prev_md, SHA512_DIGEST_LENGTH);
  EVP_MD_CTX_free(ctx);
  EVP_MD_free(sha512);
}

void print_checksum(std::ostream &os, uint8_t *md, size_t len) {
  for (int i = 0; i < len; i++) {
    os << std::setw(2) << std::setfill('0') << std::hex
       << static_cast<int>(md[i]);
  }
}