#include <openssl/evp.h>
#include <openssl/sha.h>
#include <pthread.h>
#include <secp256k1.h>
#include <semaphore.h>

#include <chrono>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vector>

std::string toHex(const uint8_t* data, size_t size) {
    std::ostringstream oss;
    for (size_t i = 0; i < size; ++i) {
        oss << std::hex << std::setfill('0') << std::setw(2) << (int)data[i];
    }
    return oss.str();
}

int byte2int(char high, char low) {
    int res = 0;
    if (high >= '0' && high <= '9') {
        res += high - '0';
    } else {
        res += high - 'a' + 10;
    }
    res <<= 4;
    if (low >= '0' && low <= '9') {
        res += low - '0';
    } else {
        res += low - 'a' + 10;
    }
    return res;
}

std::string sha3256(const uint8_t* data, size_t size) {
    EVP_MD_CTX* context = EVP_MD_CTX_new();
    const EVP_MD* md = EVP_get_digestbyname("sha3-256");
    EVP_DigestInit_ex(context, md, nullptr);
    EVP_DigestUpdate(context, data, size);

    uint8_t hash[EVP_MAX_MD_SIZE];
    unsigned int hashLen;
    EVP_DigestFinal_ex(context, hash, &hashLen);
    EVP_MD_CTX_free(context);

    return toHex(hash, hashLen);
}

inline unsigned int sha3256_hash(const uint8_t* data, size_t size,
                                 uint8_t* hash) {
    static thread_local EVP_MD_CTX* context = EVP_MD_CTX_new();
    static const EVP_MD* md = EVP_get_digestbyname("sha3-256");
    EVP_DigestInit_ex(context, md, nullptr);
    EVP_DigestUpdate(context, data, size);

    unsigned int hashLen;
    EVP_DigestFinal_ex(context, hash, &hashLen);
    // EVP_MD_CTX_free(context);
    return hashLen;
}

// static thread_local double secp_duration = 0;
// static thread_local double sha3_duration = 0;

inline void get_hash_prefix(const secp256k1_context* ctx,
                            const uint8_t privateKey[32], uint8_t output[32]) {
    // auto t1 = std::chrono::high_resolution_clock::now();
    static thread_local secp256k1_pubkey pubkey;
    if (secp256k1_ec_pubkey_create(ctx, &pubkey, privateKey) != 1) {
        std::cerr << "Error creating public key" << std::endl;
        pthread_exit(nullptr);
    }
    static thread_local uint8_t pubkeySerialized[65];
    size_t pubkeySerializedLen = 65;
    // static thread_local uint8_t pubkeySerialized[64];
    // size_t pubkeySerializedLen = 64;
    // memset(pubkeySerialized, 0, 64);

    secp256k1_ec_pubkey_serialize(ctx, pubkeySerialized, &pubkeySerializedLen,
                                  &pubkey, SECP256K1_EC_UNCOMPRESSED);

    // auto t2 = std::chrono::high_resolution_clock::now();
    // auto duration =
    //     std::chrono::duration_cast<std::chrono::nanoseconds>(t2 -
    //     t1).count();
    // secp_duration += duration / 1e6;  // convert to milliseconds

    static thread_local uint8_t hash[EVP_MAX_MD_SIZE];
    auto hashLen =
        sha3256_hash(pubkeySerialized + 1, pubkeySerializedLen - 1, hash);
    // auto hashLen = sha3256_hash(pubkey.data, 64, hash);

    // auto t3 = std::chrono::high_resolution_clock::now();
    // duration =
    //     std::chrono::duration_cast<std::chrono::nanoseconds>(t3 -
    //     t2).count();
    // sha3_duration += duration / 1e6;  // convert to milliseconds

    // return "0x" + hash.substr(24);
    for (int i = 0; i < hashLen - 12; ++i) {
        output[i] = hash[i + 12];
        // if (hash[i + 12] != prefixBytes[i]) {
        //     return false;
        // }
    }
}

#include <random>

inline void generateRandomPrivateKey(uint8_t privateKey[32]) {
    static thread_local std::random_device rd;
    static thread_local std::mt19937 gen(rd());
    static thread_local std::uniform_int_distribution<uint8_t> dis(0, 255);
    for (int i = 0; i < 32; ++i) {
        privateKey[i] = dis(gen);
    }
}

// void generateRandomPrivateKey(uint8_t privateKey[32]) {
//     FILE* urandom = fopen("/dev/urandom", "rb");
//     int res = fread(privateKey, 1, 32, urandom);
//     if (res != 32) {
//         std::cerr << "Failed to read random data" << std::endl;
//         exit(1);
//     }
//     fclose(urandom);
// }

std::string computeEthereumAddress(const secp256k1_context* ctx,
                                   const uint8_t privateKey[32]) {
    secp256k1_pubkey pubkey;
    if (secp256k1_ec_pubkey_create(ctx, &pubkey, privateKey) != 1) {
        std::cerr << "Error creating public key" << std::endl;
        pthread_exit(nullptr);
    }
    uint8_t pubkeySerialized[65];
    size_t pubkeySerializedLen = 65;
    secp256k1_ec_pubkey_serialize(ctx, pubkeySerialized, &pubkeySerializedLen,
                                  &pubkey, SECP256K1_EC_UNCOMPRESSED);

    std::string hash = sha3256(pubkeySerialized + 1, pubkeySerializedLen - 1);

    return "0x" + hash.substr(24);
}

#define NUM_ONE_TIMES 1024
#define numThreads 8

struct MyData {
    int id;
    std::vector<std::string> prefixes;
    std::ofstream* outfile;
};

struct SharedData {
    std::array<std::array<std::array<uint8_t, 32>, NUM_ONE_TIMES>,
               numThreads - 1>
        hashes;
    std::array<std::array<std::array<uint8_t, 32>, NUM_ONE_TIMES>,
               numThreads - 1>
        privateKeys;
    bool done = false;
    sem_t empty[numThreads - 1];
    sem_t full[numThreads - 1];
};

SharedData thread_shared_data;

void* put_thread(void* arg) {
    auto data = *(MyData*)arg;
    int thread_id = data.id;
    printf("Thread %d started\n", thread_id);
    if (thread_id >= numThreads - 1) {
        printf("Invalid thread id\n");
    }
    static thread_local secp256k1_context* ctx =
        secp256k1_context_create(SECP256K1_CONTEXT_SIGN);

    static thread_local uint8_t privateKey[32];

    while (true) {
        if (thread_shared_data.done) {
            break;
        }
        sem_wait(&thread_shared_data.empty[thread_id]);

        for (int i = 0; i < NUM_ONE_TIMES; ++i) {
            generateRandomPrivateKey(privateKey);
            memcpy(thread_shared_data.privateKeys[thread_id][i].data(),
                   privateKey, 32);
            get_hash_prefix(ctx, privateKey,
                            thread_shared_data.hashes[thread_id][i].data());
        }

        if (thread_shared_data.done) {
            break;
        }
        sem_post(&thread_shared_data.full[thread_id]);
    }

    secp256k1_context_destroy(ctx);

    pthread_exit(nullptr);
    return nullptr;
}

void* check_thread(void* arg) {
    auto data = *(MyData*)arg;
    printf("Last Thread %d started\n", data.id);

    auto prefixes = data.prefixes;

    std::vector<std::vector<uint8_t>> prefixBytes;

    std::vector<std::string> addresses;
    std::vector<std::string> privateKeys;
    std::vector<bool> found;

    for (const auto& prefix : prefixes) {
        std::vector<uint8_t> prefixByte;
        for (int i = 0; i < prefix.size() / 2; ++i) {
            prefixByte.push_back(byte2int(prefix[i * 2], prefix[i * 2 + 1]));
        }
        prefixBytes.push_back(prefixByte);
        addresses.push_back("");
        privateKeys.push_back("");
        found.push_back(false);
    }

    static thread_local secp256k1_context* ctx =
        secp256k1_context_create(SECP256K1_CONTEXT_SIGN);

    while (true) {
        for (int thread_id = 0; thread_id < numThreads - 1; ++thread_id) {
            sem_wait(&thread_shared_data.full[thread_id]);

            for (int idx = 0; idx < prefixes.size(); ++idx) {
                if (found[idx]) {
                    continue;
                }
                for (int j = 0; j < NUM_ONE_TIMES; ++j) {
                    auto prefixByte = prefixBytes[idx];
                    if (memcmp(thread_shared_data.hashes[thread_id][j].data(),
                               prefixByte.data(), prefixByte.size()) == 0) {
                        auto private_key =
                            thread_shared_data.privateKeys[thread_id][j];
                        printf("Private key %s\n",
                               toHex(private_key.data(), 32).c_str());
                        auto address =
                            computeEthereumAddress(ctx, private_key.data());

                        printf("Found address %s\n", address.c_str());

                        addresses[idx] = address;
                        privateKeys[idx] = toHex(private_key.data(), 32);
                        found[idx] = true;
                    }
                }
            }
            auto all_done = true;
            for (auto f : found) {
                all_done &= f;
            }
            if (all_done) {
                thread_shared_data.done = true;
            }

            sem_post(&thread_shared_data.empty[thread_id]);
            if (thread_shared_data.done) {
                printf("All done\n");
                auto outfile = data.outfile;
                for (int i = 0; i < prefixes.size(); ++i) {
                    *outfile << addresses[i] << std::endl;
                    *outfile << privateKeys[i] << std::endl;
                }
                printf("Output done\n");
                secp256k1_context_destroy(ctx);
                exit(0);
                pthread_exit(nullptr);
                return nullptr;
            }
        }
    }
    secp256k1_context_destroy(ctx);
    pthread_exit(nullptr);
    return nullptr;
}

int main(int argc, char* argv[]) {
    std::ifstream infile("vanity.in");
    std::ofstream outfile("vanity.out");

    std::vector<std::string> prefixes;

    for (int i = 0; i < 10; ++i) {
        std::string prefix;
        infile >> prefix;
        prefixes.push_back(prefix);
    }

    pthread_t threads[numThreads];
    std::array<MyData, numThreads> data;

    for (int i = 0; i < numThreads - 1; ++i) {
        sem_init(&thread_shared_data.empty[i], 0, 1);
        sem_init(&thread_shared_data.full[i], 0, 0);
        // 7 个线程生成数据
        data[i].id = i;
        pthread_create(&threads[i], nullptr, put_thread, &data[i]);
    }

    // 1 个线程检查数据
    data[numThreads - 1].id = numThreads - 1;
    data[numThreads - 1].prefixes = prefixes;
    data[numThreads - 1].outfile = &outfile;
    pthread_create(&threads[numThreads - 1], nullptr, check_thread,
                   &data[numThreads - 1]);

    // for (int i = 0; i < numThreads; ++i) {
    //     pthread_create(
    //         &threads[i], nullptr,
    //         [](void* arg) -> void* {
    //             MyData* data = (MyData*)arg;
    //             auto vanityPrefix = data->prefix;
    //             // printf("Thread %d started\n", data->id);
    //             static thread_local secp256k1_context* ctx =
    //                 secp256k1_context_create(SECP256K1_CONTEXT_SIGN);

    //             static thread_local uint8_t privateKey[32];
    //             std::string address;

    //             static thread_local uint8_t prefixBytes[32];
    //             static thread_local int prefixLen = vanityPrefix.size() /
    //             2; for (int i = 0; i < prefixLen; ++i) {
    //                 prefixBytes[i] =
    //                     byte2int(vanityPrefix[i * 2], vanityPrefix[i * 2
    //                     + 1]);
    //             }

    //             while (true) {
    //                 generateRandomPrivateKey(privateKey);
    //                 if (chech_addr(ctx, privateKey, prefixBytes,
    //                 prefixLen)) {
    //                     address = computeEthereumAddress(ctx,
    //                     privateKey); break;
    //                 }

    //             }
    //             // outfile << address << std::endl;
    //             // outfile << toHex(privateKey, 32) << std::endl;
    //             data->address = address;
    //             data->privateKey = toHex(privateKey, 32);

    //             secp256k1_context_destroy(ctx);

    //             pthread_exit(nullptr);
    //             return nullptr;
    //         },
    //         &data[i]);
    // }

    for (int i = 0; i < numThreads; ++i) {
        pthread_join(threads[i], nullptr);
    }

    // for (const auto& d : data) {
    //     outfile << d.address << std::endl;
    //     outfile << d.privateKey << std::endl;
    // }

    // for(int i = 0; i < 10; ++i){
    //     secp256k1_context* ctx =
    //     secp256k1_context_create(SECP256K1_CONTEXT_SIGN); std::string
    //     vanityPrefix; infile >> vanityPrefix; uint8_t privateKey[32];
    //     std::string address;
    //     while (true) {
    //         generateRandomPrivateKey(privateKey);
    //         address = computeEthereumAddress(ctx, privateKey);
    //         if (address.substr(2, vanityPrefix.size()) == vanityPrefix) {
    //             break;
    //         }
    //     }
    //     outfile << address << std::endl;
    //     outfile << toHex(privateKey, 32) << std::endl;
    //     secp256k1_context_destroy(ctx);
    // }
    for (int i = 0; i < numThreads - 1; ++i) {
        sem_destroy(&thread_shared_data.empty[i]);
        sem_destroy(&thread_shared_data.full[i]);
    }
    return 0;
}