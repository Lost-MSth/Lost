#include <iostream>
#include <vector>
#include <fstream>
#include <random>
#include <cstdint>
#include <cstring>
#include <algorithm>

const size_t TEXT_SIZE_GB = 1;         
const size_t PATTERN_COUNT = 8;      
const size_t PATTERN_LEN = 64;         
const size_t CHUNK_SIZE = 64 * 1024 * 1024; 
const size_t INJECTION_RATE = 2000;     

struct RandomGen {
    std::mt19937_64 rng;
    RandomGen() : rng(std::random_device{}()) {}
    
    void fill_buffer(uint8_t* buf, size_t size) {
        for (size_t i = 0; i < size; i++) {
            buf[i] = static_cast<uint8_t>('a' + (rng() % 26));
        }
    }

    size_t next_int(size_t min, size_t max) {
        std::uniform_int_distribution<size_t> dist(min, max);
        return dist(rng);
    }
};

int main() {
    RandomGen gen;
    std::cout << "Starting generation..." << std::endl;

    std::vector<std::vector<uint8_t>> patterns(PATTERN_COUNT, std::vector<uint8_t>(PATTERN_LEN));
    
    FILE* fp_pat = fopen("patterns.bin", "wb");
    if (!fp_pat) { perror("Failed to open patterns.bin"); return 1; }

    uint32_t k_val = PATTERN_COUNT;
    fwrite(&k_val, sizeof(uint32_t), 1, fp_pat);

    for (size_t i = 0; i < PATTERN_COUNT; ++i) {
        gen.fill_buffer(patterns[i].data(), PATTERN_LEN);
        fwrite(patterns[i].data(), 1, PATTERN_LEN, fp_pat);
    }
    fclose(fp_pat);
    std::cout << "-> patterns.bin generated (" << PATTERN_COUNT << " patterns)" << std::endl;

    FILE* fp_text = fopen("text.bin", "wb");
    if (!fp_text) { perror("Failed to open text.bin"); return 1; }

    size_t total_size = TEXT_SIZE_GB * 1024 * 1024 * 1024;
    fwrite(&total_size, sizeof(uint64_t), 1, fp_text);

    std::vector<uint8_t> buffer(CHUNK_SIZE);
    size_t bytes_written = 0;

    std::cout << "-> Generating text data (" << TEXT_SIZE_GB << " GB)..." << std::endl;

    while (bytes_written < total_size) {
        size_t current_chunk = std::min(CHUNK_SIZE, total_size - bytes_written);
        
        gen.fill_buffer(buffer.data(), current_chunk);

        size_t injections = (current_chunk / (1024 * 1024)) * INJECTION_RATE;
        for (size_t i = 0; i < injections; ++i) {
            int pid = gen.next_int(0, PATTERN_COUNT - 1);
            if (current_chunk > PATTERN_LEN) {
                size_t offset = gen.next_int(0, current_chunk - PATTERN_LEN);
                memcpy(buffer.data() + offset, patterns[pid].data(), PATTERN_LEN);
            }
        }

        fwrite(buffer.data(), 1, current_chunk, fp_text);
        
        bytes_written += current_chunk;
        printf("\r   Progress: %lu / %lu bytes", bytes_written, total_size);
        fflush(stdout);
    }

    fclose(fp_text);
    std::cout << "\n-> text.bin generated." << std::endl;
    std::cout << "Done." << std::endl;

    return 0;
}