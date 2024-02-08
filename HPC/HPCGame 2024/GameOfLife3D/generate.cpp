#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>

namespace fs = std::filesystem;

int main(int argc, char *argv[]) {
  if (argc < 4) {
    std::cout << "Usage: " << argv[0] << " <M> <output_path> <density>"
              << std::endl;
    return 1;
  }

  size_t M = std::atoi(argv[1]), T = 0;
  fs::path output_path = argv[2];
  int density = std::atoi(argv[3]);

  if (!(density > 0 && density < 100)) {
    std::cout << "Invalid density: " << density << std::endl;
    return 1;
  }

  std::ofstream output_file(output_path, std::ios::binary);
  output_file.write(reinterpret_cast<char *>(&M), sizeof(M));
  output_file.write(reinterpret_cast<char *>(&T), sizeof(T));

  uint8_t *data = new uint8_t[M * M * M];
  std::random_device rd;
  std::default_random_engine el(rd());
  std::uniform_int_distribution<uint8_t> dist(0, 99);

  for (int i = 0; i < M * M * M; i++) {
    if (dist(el) < density) {
      data[i] = 1;
    } else {
      data[i] = 0;
    }
  }

  output_file.write(reinterpret_cast<char *>(data), M * M * M);

  delete[] data;

  return 0;
}
