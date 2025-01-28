void filter_run(double x[113][2700], double wgt[113][1799], int ngrid[113], int is, int ie, int js, int je)
{
    double tmp[ie - is + 1];
    for(int j = js; j <= je; j++){
        int n = ngrid[j];
        int hn = (n - 1) >> 1;
        for(int i = is; i <= ie; i++){
            tmp[i - is] = 0;
            for(int p = 0; p < n; p++)
                tmp[i - is] += wgt[j][p] * x[j][i - hn + p];
        }
        for(int i = is; i <= ie; i++)
            x[j][i] = tmp[i - is];
    }
}