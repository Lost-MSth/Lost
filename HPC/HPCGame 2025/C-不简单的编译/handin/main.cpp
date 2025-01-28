#include <bits/stdc++.h>
using namespace std;

extern "C"
{
    void filter_run(double x[113][2700], double wgt[113][1799], int ngrid[113], int is, int ie, int js, int je);
}

double val[113][2700], checksum_weight[113][2700];
double filter[113][1799];
int nfilter[113];
int main()
{
    // 设置随机数种子，评测将会使用另一个种子，编译时请不要试图绕过 main.cpp
    mt19937 random_engine(20241112);
    uniform_real_distribution<double> range01(0.0, 1.0);
    uniform_int_distribution<int> range07(0, 7);
    // 初始化数组
    for(int i = 0; i < 113; i++)
        for(int j = 0; j < 2700; j++){
            val[i][j] = range01(random_engine);
            checksum_weight[i][j] = range01(random_engine);
        }
    // 初始化filter
    for(int j = 0; j < 113; j++){
        nfilter[j] = floor(1799.0 * pow(j + 1.0, -0.8));
        if(nfilter[j] % 2 == 0)
            nfilter[j]++;
        double sum = 0;
        for(int i = 0; i < nfilter[j]; i++)
            sum += (filter[j][i] = range01(random_engine));
        for(int i = 0; i < nfilter[j]; i++)
            filter[j][i] /= sum;
    }
    // 计算卷积
    for(int T = 1; T <= 1000; T++)
        filter_run(val, filter, nfilter,
                   900 + range07(random_engine), 1799 - range07(random_engine),
                   0 + range07(random_engine), 112 - range07(random_engine));
    // 计算校验值
    double checksum = 0.0;
    for(int i = 0; i < 113; i++)
        for(int j = 0; j < 2700; j++)
            checksum += val[i][j] * checksum_weight[i][j];
    printf("%.20le\n", checksum);
}