void filter_run(double x[restrict 113][2700], double wgt[restrict 113][1799],
                int ngrid[restrict 113], int is, int ie, int js, int je) {
    double tmp[ie - is + 1];

    for (int j = js; j <= je; j++) {
        int n = ngrid[j];
        int hn = (n - 1) >> 1;

        double* restrict xxx = wgt[j];
        double* restrict yyy = x[j];

        for (int i = is; i <= ie; i++) {
            tmp[i - is] = 0;
            for (int p = 0; p < n; p++) tmp[i - is] += xxx[p] * yyy[i - hn + p];
        }
        for (int i = is; i <= ie; i++) yyy[i] = tmp[i - is];
    }
}

// 7.65468510748272383353e+04

// real    0m4.249s
// user    0m4.201s
// sys     0m0.001s

// 7.65468510748268163297e+04

// real    0m0.747s
// user    0m0.740s
// sys     0m0.002s