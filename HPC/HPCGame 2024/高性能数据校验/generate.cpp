#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <random>

int main(int argc, char **argv) {
  if (argc < 3) {
    std::cout << "Usage: " << argv[0] << " <file> <size> [<seed>]" << std::endl;
    std::exit(1);
  }
  std::ofstream ostrm(argv[1]);
  std::size_t size = std::atoll(argv[2]);

  uint8_t *content = new uint8_t[size];

  std::random_device r;
  int seed = 0;
  if (argc >= 4) {
    seed = std::atoi(argv[3]);
  } else {
    std::random_device r;
    seed = r();
  }

  size_t block_size = 1024 * 1024 * 16;

#pragma omp parallel for
  for (size_t i = 0; i < (size + block_size - 1) / block_size; i++) {
    std::mt19937 el(seed + i);
    std::uniform_int_distribution<uint8_t> uniform_dist;
    for (int j = 0; j < block_size && i * block_size + j < size; j++) {
      content[i * block_size + j] = uniform_dist(el);
    }
  }

  ostrm.write(reinterpret_cast<char *>(content), size);

  delete[] content;
  return 0;
}