#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>

#define _DWORD int

__int64 __fastcall f(char **a1, __int64 a2, int a3) {
    char *v3;     // r10
    int v7;       // r11d
    char *v8;     // rcx
    __int64 v9;   // rcx
    int v10;      // r8d
    __int64 v11;  // rbp
    __int64 v12;  // rbx
    __int64 v13;  // rbp
    __int64 v14;  // r8
    int v15;      // edi
    __int64 v16;  // r9
    __int64 v17;  // rbx
    __int64 v18;  // rbp
    __int64 v19;  // r8
    int v20;      // r9d
    __int64 v21;  // rbx
    __int64 v22;  // r8
    __int64 v23;  // rdi
    int i;        // r9d
    __int64 v25;  // rdi
    __int64 v26;  // r13
    __int64 v27;  // r9
    __int64 v28;  // r10
    int j;        // ebx
    __int64 v31;  // rbx

    v3 = *a1;
    v7 = *((_DWORD *)*a1 - 2);
    v8 = *a1;
    if (v7 < 0) {
        v10 = *v3 % 32;
        if (!(*v3 % 32)) {
            v31 = (a2 + 1) % 1000000007;
            v13 = v31;
            v14 = v31 + 3;
            v15 = v3[1] % 32;
            if (!(v3[1] % 32)) {
                v17 = (v31 + 1) % 1000000007;
            LABEL_39:
                v19 = v17 + 5;
                v20 = v3[2] % 32;
                if (!(v3[2] % 32)) {
                    v21 = (v17 + 1) % 1000000007;
                    goto LABEL_22;
                }
                goto LABEL_16;
            }
            goto LABEL_10;
        }
    } else {
        // std::string::_M_leak_hard((std::string *)a1);
        v3 = *a1;
        v9 = 1LL;
        v7 = *((_DWORD *)*a1 - 2);
        v10 = **a1 % 32;
        if (!(**a1 % 32)) goto LABEL_7;
    }
    v11 = 2LL;
    v9 = 1LL;
    do {
        if ((v10 & 1) != 0) v9 = v11 * v9 % 1000000007;
        v10 >>= 1;
        v11 = v11 * v11 % 1000000007;
    } while (v10);
LABEL_7:
    v12 = (v9 + a2) % 1000000007;
    v13 = v12;
    if (v7 >= 0) {
        // std::string::_M_leak_hard((std::string *)a1);
        v3 = *a1;
    }
    v8 = v3;
    v7 = *((_DWORD *)v3 - 2);
    v14 = v12 + 3;
    v15 = v3[1] % 32;
    if (!(v3[1] % 32)) {
        v16 = 1LL;
        goto LABEL_14;
    }
LABEL_10:
    v16 = 1LL;
    do {
        if ((v15 & 1) != 0) v16 = v14 * v16 % 1000000007;
        v15 >>= 1;
        v14 = v14 * v14 % 1000000007;
    } while (v15);
LABEL_14:
    v17 = (v13 + v16) % 1000000007;
    if (v7 < 0) goto LABEL_39;
    v18 = 1LL;
    // std::string::_M_leak_hard((std::string *)a1);
    v3 = *a1;
    v19 = v17 + 5;
    v7 = *((_DWORD *)*a1 - 2);
    v20 = (*a1)[2] % 32;
    if ((*a1)[2] % 32) {
    LABEL_16:
        v18 = 1LL;
        do {
            if ((v20 & 1) != 0) v18 = v19 * v18 % 1000000007;
            v20 >>= 1;
            v19 = v19 * v19 % 1000000007;
        } while (v20);
    }
    v21 = (v17 + v18) % 1000000007;
    v8 = v3;
    if (v7 >= 0) {
        // std::string::_M_leak_hard((std::string *)a1);
        v8 = *a1;
    }
LABEL_22:
    v22 = v21 + 7;
    v23 = 1LL;
    for (i = v8[3] % 32; i; v22 = v22 * v22 % 1000000007) {
        if ((i & 1) != 0) v23 = v22 * v23 % 1000000007;
        i >>= 1;
    }
    v25 = (v23 + v21) % 1000000007;
    if (a3 > 0) {
        v26 = 1LL;
        do {
            if (*((int *)v8 - 2) >= 0) {
                // std::string::_M_leak_hard((std::string *)a1);
                v8 = *a1;
            }
            v27 = v26 + v25;
            v28 = 1LL;
            for (j = (int)v25 % (int)v26 + v8[v26 & 3] % 32; j;
                 v27 = v27 * v27 % 1000000007) {
                if ((j & 1) != 0) v28 = v27 * v28 % 1000000007;
                j >>= 1;
            }
            ++v26;
            v25 = (v25 + v28) % 1000000007;
        } while (a3 >= (int)v26);
    }
    return (v25 % 1000000007 + 1000000007) % 1000000007;
}

int main() {
    char *data = new char[4]{71, 79, 76, 68};  // Example data
    char **a1 = &data;
    __int64 a2 = 0;    // Example value
    int a3 = 6000000;  // Example count

    __int64 TARGET = 0x2430EE24;
    // __int64 result = f(a1, a2, a3);
    // std::cout << "Result: " << result << std::endl;

    // 从 seed.txt 中读取 four char words
    std::ifstream infile("seed.txt");
    if (!infile) {
        std::cerr << "Failed to open seed.txt" << std::endl;
        return 1;
    }
    std::string line;
    while (std::getline(infile, line)) {
        if (line.size() >= 4) {
            char *data = new char[4];
            std::memcpy(data, line.c_str(), 4);
            char *a1_local = data;
            char **a1_ptr = &a1_local;
            __int64 result = f(a1_ptr, a2, a3);
            std::cout << "Word: " << std::string(data, 4)
                      << " Result: " << result << std::endl;

            if (result == TARGET) {
                std::cout << "Found target: " << std::string(data, 4)
                          << std::endl;
                return 0;  // Exit if target is found
            }
        }
    }

    delete[] data;
    // delete[] data; // Clean up allocated memory (already deleted in the loop
    // if used)
    return 0;
}