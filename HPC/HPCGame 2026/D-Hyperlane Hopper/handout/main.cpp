#include <iostream>
#include <fstream>
#include <random>
#include <chrono>
#include <cstring>
#include <cstdint>

const uint64_t MAX_WEIGHT = 1e7;
const uint64_t INF = 1e18;

void calculate(uint32_t, uint32_t, uint32_t *, uint64_t *);

void random_edges(uint32_t n, uint32_t m, uint32_t seed, std::vector<uint32_t> &edges)
{
    std::mt19937_64 gen(seed);
    std::uniform_int_distribution<uint32_t> gen_node(0, n - 1);
    std::uniform_int_distribution<uint32_t> gen_weight(1, MAX_WEIGHT);

    for (uint32_t i = 0; i < n - 1; ++i)
    {
        uint32_t u = std::uniform_int_distribution<size_t>(0, i)(gen);
        uint32_t v = i + 1;
        uint32_t w = gen_weight(gen);
        edges[i * 3] = u;
        edges[i * 3 + 1] = v;
        edges[i * 3 + 2] = w;
    }

    for (uint32_t i = n - 1; i < m; ++i)
    {
        uint32_t u = gen_node(gen);
        uint32_t v = gen_node(gen);
        uint32_t w = gen_weight(gen);
        edges[i * 3] = u;
        edges[i * 3 + 1] = v;
        edges[i * 3 + 2] = w;
    }
}

int main(int argc, char *argv[])
{
    if (argc != 5)
    {
        std::cerr << "Usage: ./sssp <n> <m> <seed> <output>\n";
        exit(1);
    }

    uint32_t n, m, seed;
    n = std::atoll(argv[1]);
    m = std::atoll(argv[2]);
    seed = std::atoll(argv[3]);

    std::mt19937_64 gen(seed);
    std::uniform_int_distribution<uint32_t> gen_node(0, n - 1);
    std::uniform_int_distribution<uint32_t> gen_weight(1, MAX_WEIGHT);

    std::vector<uint32_t> edges(m * 3);
    std::vector<uint64_t> dis(n, INF);
    dis[0] = 0;

    random_edges(n, m, seed, edges);

    auto start = std::chrono::high_resolution_clock::now();

    calculate(n, m, edges.data(), dis.data());

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    fprintf(stderr, "Time: %.6f seconds\n", elapsed.count());

    std::ofstream out(argv[4], std::ios::out | std::ios::binary);
    if (!out)
    {
        fprintf(stderr, "Error: cannot open output file for writing.\n");
        exit(1);
    }
    out.write(reinterpret_cast<const char *>(dis.data()), n * sizeof(uint64_t));
    out.close();

    return 0;
}