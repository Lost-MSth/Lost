#ifndef MARKET_H
#define MARKET_H

// ==========================================
// 你可以修改这里的结构体定义，但请保留成员变量名
// ==========================================

struct alignas(64) Candle {
    double high;
    double low;
    double close;
    long long vol;
    long long _pad[4];
};

struct MarketData {
    Candle* candles;
    int num_threads;
    long long total_vol;
    double total_turnover;
};


#endif