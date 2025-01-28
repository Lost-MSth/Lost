#include <iostream>
#include <fstream>
#include <random>
#include <vector>

using std::cerr, std::endl;
constexpr int LIMIT = 1000000000ull;

typedef int element_t;

int main(int argc, char** argv) {
    if (argc < 4) {
        cerr << "Usage: " << argv[0] << " <length_1> <length_2> <output_file>" << endl;
        exit(-1);
    }

    size_t len_1 = atoi(argv[1]);
    size_t len_2 = atoi(argv[2]);
    if (len_1 > LIMIT || len_2 > LIMIT) {
        cerr << "Array size exceeded the limit " << LIMIT << endl;
        exit(-1);
    }

    std::ofstream file(argv[3], std::ios::out | std::ios::binary);
    if (!file) {
        cerr << "Cannot write size_to file " << argv[3] << endl;
        exit(-1);
    }
    file.write((const char*)&len_1, sizeof(len_1));
    file.write((const char*)&len_2, sizeof(len_2));

    std::mt19937 generator;
    std::vector<element_t> buffer(len_1 + len_2);
    for (size_t i = 0; i < len_1 + len_2; i++) {
        buffer[i] = generator() & 0xffff;
    }
    file.write((const char*)buffer.data(), buffer.size() * sizeof(element_t));

    return 0;
}
