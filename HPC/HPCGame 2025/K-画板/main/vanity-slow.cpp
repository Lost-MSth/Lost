#include <openssl/evp.h>
#include <openssl/sha.h>
#include <pthread.h>
#include <secp256k1.h>

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

inline bool chech_addr(const secp256k1_context* ctx,
                       const uint8_t privateKey[32], uint8_t prefixBytes[32],
                       int prefixLen) {
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
    //     std::chrono::duration_cast<std::chrono::nanoseconds>(t2 - t1).count();
    // secp_duration += duration / 1e6;  // convert to milliseconds

    static thread_local uint8_t hash[EVP_MAX_MD_SIZE];
    auto hashLen =
        sha3256_hash(pubkeySerialized + 1, pubkeySerializedLen - 1, hash);
    // auto hashLen = sha3256_hash(pubkey.data, 64, hash);

    // auto t3 = std::chrono::high_resolution_clock::now();
    // duration =
    //     std::chrono::duration_cast<std::chrono::nanoseconds>(t3 - t2).count();
    // sha3_duration += duration / 1e6;  // convert to milliseconds

    // return "0x" + hash.substr(24);
    for (int i = 0; i < prefixLen; ++i) {
        if (hash[i + 12] != prefixBytes[i]) {
            return false;
        }
    }
    return true;
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

struct MyData {
    int id;
    std::string prefix;
    std::string address;
    std::string privateKey;
};

int main(int argc, char* argv[]) {
    std::ifstream infile("vanity.in");
    std::ofstream outfile("vanity.out");

    std::vector<MyData> data;

    for (int i = 0; i < 10; ++i) {
        std::string prefix;
        infile >> prefix;
        data.push_back({i, prefix, "", ""});
    }

    const int numThreads = 10;
    pthread_t threads[numThreads];

    for (int i = 0; i < numThreads; ++i) {
        pthread_create(
            &threads[i], nullptr,
            [](void* arg) -> void* {
                MyData* data = (MyData*)arg;
                auto vanityPrefix = data->prefix;
                // printf("Thread %d started\n", data->id);
                static thread_local secp256k1_context* ctx =
                    secp256k1_context_create(SECP256K1_CONTEXT_SIGN);

                static thread_local uint8_t privateKey[32];
                std::string address;

                static thread_local uint8_t prefixBytes[32];
                static thread_local int prefixLen = vanityPrefix.size() / 2;
                for (int i = 0; i < prefixLen; ++i) {
                    prefixBytes[i] =
                        byte2int(vanityPrefix[i * 2], vanityPrefix[i * 2 + 1]);
                }

                // double random_t = 0;
                // double hash_t = 0;

                while (true) {
                    // auto t1 = std::chrono::high_resolution_clock::now();
                    generateRandomPrivateKey(privateKey);
                    // auto t2 = std::chrono::high_resolution_clock::now();
                    // auto duration =
                    //     std::chrono::duration_cast<std::chrono::nanoseconds>(
                    //         t2 - t1)
                    //         .count();
                    // random_t += duration / 1e6;  // convert to milliseconds
                    if (chech_addr(ctx, privateKey, prefixBytes, prefixLen)) {
                        address = computeEthereumAddress(ctx, privateKey);
                        break;
                    }
                    // auto t3 = std::chrono::high_resolution_clock::now();
                    // duration =
                    //     std::chrono::duration_cast<std::chrono::nanoseconds>(
                    //         t3 - t2)
                    //         .count();
                    // hash_t += duration / 1e6;  // convert to milliseconds
                    // address = computeEthereumAddress(ctx, privateKey);
                    // if (address.substr(2, vanityPrefix.size()) ==
                    //     vanityPrefix) {
                    //     break;
                    // }
                }
                // outfile << address << std::endl;
                // outfile << toHex(privateKey, 32) << std::endl;
                data->address = address;
                data->privateKey = toHex(privateKey, 32);
                // printf("Thread %d finished\n", data->id);
                // printf("Address: %s\n", data->address.c_str());
                // // printf("Private key: %s\n", data->privateKey.c_str());
                // printf("Random time: %f\n", random_t);
                // printf("Hash time: %f\n", hash_t);

                // printf("Secp time: %f\n", secp_duration);
                // printf("Sha3 time: %f\n", sha3_duration);

                secp256k1_context_destroy(ctx);

                pthread_exit(nullptr);
                return nullptr;
            },
            &data[i]);
    }

    for (int i = 0; i < numThreads; ++i) {
        pthread_join(threads[i], nullptr);
    }

    for (const auto& d : data) {
        outfile << d.address << std::endl;
        outfile << d.privateKey << std::endl;
    }

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
    return 0;
}