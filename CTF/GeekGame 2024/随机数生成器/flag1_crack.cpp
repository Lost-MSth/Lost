#include <cstdint>
#include <iostream>

unsigned int target = 1157373170 - 102;

int main() {
    for (unsigned int seed = 0; seed < 0xFFFFFFFF; seed++) {
        srand(seed);
        if (rand() == target) {
            std::cout << "seed = " << seed << std::endl;
            // break;
        }
    }
    return 0;
}
