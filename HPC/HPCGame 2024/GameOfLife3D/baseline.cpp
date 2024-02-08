#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <utility>

namespace fs = std::filesystem;

int main(int argc, char *argv[]) {
  if (argc < 4) {
    std::cout << "Usage: " << argv[0] << " <input_path> <output_path> <N>"
              << std::endl;
    return 1;
  }

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

  auto count_neighbor = [&](int x, int y, int z) {
    size_t lx = ((x + M - 1) % M) * M * M;
    size_t mx = x * M * M;
    size_t rx = ((x + 1) % M) * M * M;

    size_t ly = ((y + M - 1) % M) * M;
    size_t my = y * M;
    size_t ry = ((y + 1) % M) * M;

    size_t lz = (z + M - 1) % M;
    size_t mz = z;
    size_t rz = (z + 1) % M;

    return curr_space[lx + ly + lz] + curr_space[lx + ly + mz] +
           curr_space[lx + ly + rz] + curr_space[lx + my + lz] +
           curr_space[lx + my + mz] + curr_space[lx + my + rz] +
           curr_space[lx + ry + lz] + curr_space[lx + ry + mz] +
           curr_space[lx + ry + rz] + curr_space[mx + ly + lz] +
           curr_space[mx + ly + mz] + curr_space[mx + ly + rz] +
           curr_space[mx + my + lz] + curr_space[mx + my + rz] +
           curr_space[mx + ry + lz] + curr_space[mx + ry + mz] +
           curr_space[mx + ry + rz] + curr_space[rx + ly + lz] +
           curr_space[rx + ly + mz] + curr_space[rx + ly + rz] +
           curr_space[rx + my + lz] + curr_space[rx + my + mz] +
           curr_space[rx + my + rz] + curr_space[rx + ry + lz] +
           curr_space[rx + ry + mz] + curr_space[rx + ry + rz];
  };

  auto update_state = [&](int x, int y, int z) {
    int neighbor_count = count_neighbor(x, y, z);
    uint8_t curr_state = curr_space[x * M * M + y * M + z];
    uint8_t &next_state = next_space[x * M * M + y * M + z];

    if (curr_state == 1) {
      if (neighbor_count < 5 || neighbor_count > 7)
        next_state = 0;
      else
        next_state = 1;
    } else {
      if (neighbor_count == 6) {
        next_state = 1;
      } else {
        next_state = 0;
      }
    }
  };

  for (int t = 0; t < N; t++) {
    for (int x = 0; x < M; x++) {
      for (int y = 0; y < M; y++) {
        for (int z = 0; z < M; z++) {
          update_state(x, y, z);
        }
      }
    }
    std::swap(curr_space, next_space);
  }

  T += N;
  std::ofstream output_file(output_path, std::ios::binary);
  output_file.write(reinterpret_cast<char *>(&M), sizeof(M));
  output_file.write(reinterpret_cast<char *>(&T), sizeof(T));
  output_file.write(reinterpret_cast<char *>(curr_space), M * M * M);

  delete[] curr_space;
  delete[] next_space;

  return 0;
}
