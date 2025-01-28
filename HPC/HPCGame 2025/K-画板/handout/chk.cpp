#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <openssl/evp.h>
#include <openssl/sha.h>
#include <secp256k1.h>
#include <iomanip>
#include <sstream>

std::string computeEthereumAddress(const secp256k1_context* ctx, const std::string& privateKeyHex) {
    uint8_t privateKey[32];
    for(int i = 0; i < 32; ++i){
        std::string byteString = privateKeyHex.substr(2*i, 2);
        privateKey[i] = static_cast<uint8_t>(std::stoul(byteString, nullptr, 16));
    }

    secp256k1_pubkey pubkey;
    if(!secp256k1_ec_pubkey_create(ctx, &pubkey, privateKey)){
        return "";
    }

    std::vector<uint8_t> pubkeySerialized(65);
    size_t pubkeyLen = 65;
    secp256k1_ec_pubkey_serialize(ctx, pubkeySerialized.data(), &pubkeyLen, &pubkey, SECP256K1_EC_UNCOMPRESSED);

    EVP_MD_CTX* context = EVP_MD_CTX_new();
    const EVP_MD* md = EVP_get_digestbyname("sha3-256");
    EVP_DigestInit_ex(context, md, nullptr);
    EVP_DigestUpdate(context, pubkeySerialized.data() + 1, pubkeyLen -1);

    uint8_t hash[EVP_MAX_MD_SIZE];
    unsigned int hashLen;
    EVP_DigestFinal_ex(context, hash, &hashLen);
    EVP_MD_CTX_free(context);

    std::ostringstream oss;
    for(unsigned int i = 0; i < hashLen; ++i){
        oss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }
    std::string hashHex = oss.str();

    return "0x" + hashHex.substr(24);
}

int main() {
    std::ifstream infile("vanity.in");
    std::ifstream outfile("vanity.out");
    std::vector<std::string> prefixes;
    std::vector<std::pair<std::string, std::string>> addressKeyPairs;
    std::string line;

    while(std::getline(infile, line)){
        if(!line.empty()){
            prefixes.push_back(line);
        }
    }

    while(std::getline(outfile, line)){
        if(!line.empty()){
            std::string address = line;
            if(std::getline(outfile, line)){
                std::string privateKey = line;
                addressKeyPairs.emplace_back(address, privateKey);
            }
        }
    }

    secp256k1_context* ctx = secp256k1_context_create(SECP256K1_CONTEXT_SIGN);

    // print to result.txt
    std::ofstream result("result.txt");
    for(size_t i = 0; i < addressKeyPairs.size(); ++i){
        const auto& pair = addressKeyPairs[i];
        std::string expectedPrefix = (i < prefixes.size()) ? prefixes[i] : "";
        bool prefixMatch = pair.first.find(expectedPrefix) == 2;
        std::string generatedAddress = computeEthereumAddress(ctx, pair.second);
        bool addressMatch = (generatedAddress == pair.first);
        if((!prefixMatch) || (!addressMatch)){
            result << "WRONG" << std::endl;
            return 0;
        }
    }
    secp256k1_context_destroy(ctx);
    result << "CORRECT" << std::endl;
    return 0;
}