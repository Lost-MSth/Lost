#include <iostream>
#include <vector>
#include <iomanip>
#include <omp.h>

#include "market.h"

struct FastRNG {
    unsigned long long state;
    FastRNG(unsigned long long seed) : state(seed) {}
    
    inline unsigned long long next() {
        unsigned long long x = state;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        return state = x;
    }

    inline double nextPrice(double base) {
        return base + ((long long)(next() % 2000) - 1000) / 100.0;
    }

    inline int nextVol() {
        return (next() % 10) + 1;
    }
};

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    long long N;
    int seed_input;
    if (!(std::cin >> N >> seed_input)) return 0;

    const int num_threads = omp_get_max_threads();
    Candle* candles = new Candle[num_threads];
    
    for (int i = 0; i < num_threads; i++) {
        double base = 100.0 + i * 10.0;
        candles[i].high  = base;
        candles[i].low   = base;
        candles[i].close = base;
        candles[i].vol   = 0;
    }

    double total_turnover = 0.0;

    double start = omp_get_wtime();

    #pragma omp parallel for reduction(+:total_turnover)
    for (int tid = 0; tid < num_threads; tid++) {
        FastRNG rng(seed_input + tid * 10007);
        double base = 100.0 + tid * 10.0;
        double local_turnover = 0.0;

        for (long long i = 0; i < N; i++) {
            double price = rng.nextPrice(base);
            int volume = rng.nextVol();

            if (price > candles[tid].high) candles[tid].high = price;
            if (price < candles[tid].low)  candles[tid].low  = price;
            candles[tid].close = price;
            candles[tid].vol += volume;
            local_turnover += price * volume;
        }

        total_turnover += local_turnover;
    }

    double end = omp_get_wtime();
    std::cerr << "Elapsed: " << end - start << "s" << std::endl;

    long long total_vol = 0;
    double total_weighted_close = 0.0;
    for (int i = 0; i < num_threads; i++) {
        total_vol += candles[i].vol;
        total_weighted_close += (candles[i].high + candles[i].low + 2.0 * candles[i].close) / 4.0;
    }

    std::cout << std::fixed << std::setprecision(2) << total_turnover << std::endl;
    std::cout << std::fixed << std::setprecision(4) << (total_turnover / total_vol) << std::endl;
    std::cout << std::fixed << std::setprecision(4) << total_weighted_close << std::endl;

    return 0;
}