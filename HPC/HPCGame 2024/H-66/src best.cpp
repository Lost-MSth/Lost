#include <math.h>
#include <stdint.h>

#include <chrono>
#include <unordered_map>
#include <vector>

#ifdef _WIN32
#include <intrin.h>
#include <windows.h>
#define popcnt __popcnt64
#else
#define popcnt __builtin_popcountll
#endif

#include <immintrin.h>
#include <omp.h>

#include <algorithm>
#include <iostream>

typedef std::unordered_map<uint64_t, size_t> map_t;

struct restrict_t {
    int offset, range, minocc, maxocc;
    int occ;
    uint64_t substate;
};

template <typename VT>
struct term_t {
    VT value;
    uint64_t an, cr, signmask, sign;
};


struct sp_csr {
    std::vector<std::vector<size_t>> col;
    std::vector<std::vector<double>> data;
};

static inline int itrest(restrict_t& rest) {
    if (!rest.substate) {
        goto next;
    }
    {
        uint64_t x = rest.substate & (-(int64_t)rest.substate);
        uint64_t y = x + rest.substate;
        rest.substate = y + (y ^ rest.substate) / x / 4;
    }
    if (rest.substate >> rest.range) {
    next:
        if (rest.occ == rest.maxocc) {
            rest.occ = rest.minocc;
            rest.substate = (uint64_t(1) << rest.occ) - 1;
            return 1;
        }
        rest.occ++;
        rest.substate = (uint64_t(1) << rest.occ) - 1;
        return 0;
    }
    return 0;
}

static inline int itrest(std::vector<restrict_t>& rest) {
    for (restrict_t& re : rest) {
        if (!itrest(re)) {
            return 0;
        }
    }
    return 1;
}

static inline uint64_t getstate(const std::vector<restrict_t>& rest) {
    uint64_t state = 0;
    for (const restrict_t& re : rest) {
        state |= re.substate << re.offset;
    }
    return state;
}

static inline int generatetable(std::vector<uint64_t>& table, map_t& map,
                  std::vector<restrict_t>& rest) {
    for (restrict_t& re : rest) {
        re.occ = re.minocc;
        re.substate = (uint64_t(1) << re.occ) - 1;
    }

    size_t index = 0;
    do {
        uint64_t state = getstate(rest);
        table.push_back(state);
        map.insert(std::make_pair(state, index));
        index++;
    } while (!itrest(rest));

    return 0;
}

template <typename VT>
static inline term_t<VT> getterm(VT value, const std::vector<int>& cr,
                   const std::vector<int>& an) {
    term_t<VT> term;
    term.value = value;
    term.an = 0;
    term.cr = 0;
    term.signmask = 0;
    uint64_t signinit = 0;

    for (int x : an) {
        uint64_t mark = uint64_t(1) << x;
        term.signmask ^= (mark - 1) & (~term.an);
        term.an |= mark;
    }
    for (int x : cr) {
        uint64_t mark = uint64_t(1) << x;
        signinit ^= (mark - 1) & term.cr;
        term.signmask ^= (mark - 1) & (~term.an) & (~term.cr);
        term.cr |= mark;
    }
    term.sign = popcnt(signinit ^ (term.signmask & term.an));
    term.signmask = term.signmask & (~term.an) & (~term.cr);

    return term;
}

template <typename VT>
static inline int act(std::vector<std::vector<size_t>>& col,
        std::vector<std::vector<VT>>& data, const std::vector<term_t<VT>>& op,
        const std::vector<uint64_t>& table, const map_t& map) {
    int64_t n = table.size();

#pragma omp parallel for shared(col, data) schedule(static)
    for (int64_t i = 0; i < n; i++) {
        uint64_t srcstate = table[i];

        for (const term_t<VT>& term : op) {
            if ((srcstate & term.an) == term.an) {
                uint64_t dststate = srcstate ^ term.an;
                if ((dststate & term.cr) == 0) {
                    dststate ^= term.cr;

                    auto it = map.find(dststate);
                    if (it != map.end()) {
                        uint64_t sign =
                            term.sign + popcnt(srcstate & term.signmask);
                        VT v = term.value;
                        if (sign & 1) {
                            v = -v;
                        }
                        col[i].push_back(it->second);
                        data[i].push_back(v);
                    }
                }
            }
        }
    }

    return 0;
}

static inline int readss(FILE* fi, std::vector<uint64_t>& table, map_t& map) {
    int n;
    fread(&n, 1, 4, fi);
    std::vector<restrict_t> restv(n);
    for (auto& rest : restv) {
        fread(&rest, 1, 16, fi);
    }
    generatetable(table, map, restv);
    return restv[0].range;
}

static inline int readop(FILE* fi, std::vector<term_t<double>>& op) {
    int n, order;
    fread(&n, 1, 4, fi);
    fread(&order, 1, 4, fi);

    std::vector<double> v(n);
    fread(v.data(), 1, 8 * n, fi);

    std::vector<int> rawterm(order);
    std::vector<int> cr, an;

    for (int i = 0; i < n; i++) {
        fread(rawterm.data(), 1, 4 * order, fi);
        int tn = rawterm[0];

        for (int j = 0; j < tn; j++) {
            int type = rawterm[tn * 2 - 1 - j * 2];
            if (type) {
                cr.push_back(rawterm[tn * 2 - j * 2]);
            } else {
                an.push_back(rawterm[tn * 2 - j * 2]);
            }
        }

        op.push_back(getterm(v[i], cr, an));
        cr.clear();
        an.clear();
    }

    return 0;
}


static inline void mmv(std::vector<double>& out, const sp_csr& m,
         const std::vector<double>& v) {
    const int64_t row_n = m.col.size();

#pragma omp parallel for shared(out) schedule(static)
    for (size_t i = 0; i < row_n; i++) {
        double t = 0;
        size_t j_e = m.col[i].size();
        size_t j_8 = j_e - j_e % 8;

        __m512d t_vec = _mm512_setzero_pd();

        const std::vector<double>& _data = m.data[i];
        const std::vector<size_t>& _col = m.col[i];

        for (size_t j = 0; j < j_8; j += 8) {
            __m512d data = _mm512_loadu_pd(&_data[j]);
            __m512i col = _mm512_loadu_si512(&_col[j]);
            __m512d v512 = _mm512_i64gather_pd(col, &v[0], sizeof(double));
            t_vec = _mm512_fmadd_pd(data, v512, t_vec);
        }

        double t_arr[8];
        _mm512_storeu_pd(t_arr, t_vec);
        for (int k = 0; k < 8; k++) {
            t += t_arr[k];
        }

        for (size_t j = j_8; j < j_e; j++) {
            t += _data[j] * v[_col[j]];
        }

        out[i] = t;
    }
}

// v1'*v2;
static inline double dot(const std::vector<double>& v1, const std::vector<double>& v2) {
    double s = 0;
#pragma omp parallel for reduction(+ : s)
    for (size_t i = 0; i < v1.size(); i++) {
        s += v1[i] * v2[i];
    }
    return s;
}

// v1+=s*v2;
static inline void avv(std::vector<double>& v1, const double s,
         const std::vector<double>& v2) {
    size_t n = v1.size();
    size_t n_8 = n - n % 8;

    __m512d s_512 = _mm512_set1_pd(s);

#pragma omp parallel for
    for (size_t i = 0; i < n_8; i += 8) {
        __m512d v1_512 = _mm512_loadu_pd(&v1[i]);
        __m512d v2_512 = _mm512_loadu_pd(&v2[i]);
        _mm512_storeu_pd(&v1[i], _mm512_fmadd_pd(s_512, v2_512, v1_512));
    }

    for (size_t i = n_8; i < n; i++) {
        v1[i] += s * v2[i];
    }
}

// v*=s;
static inline void msv(const double s, std::vector<double>& v) {
    size_t n = v.size();
    size_t n_8 = n - n % 8;

    __m512d s_512 = _mm512_set1_pd(s);

#pragma omp parallel for
    for (size_t i = 0; i < n_8; i += 8) {
        __m512d v_512 = _mm512_loadu_pd(&v[i]);
        _mm512_storeu_pd(&v[i], _mm512_mul_pd(v_512, s_512));
    }

    for (size_t i = n_8; i < n; i++) {
        v[i] *= s;
    }
}

// v'*v;
static inline double norm2(const std::vector<double>& v) {
    double s = 0;

#pragma omp parallel for reduction(+ : s)
    for (size_t i = 0; i < v.size(); i++) {
        s += v[i] * v[i];
    }

    return s;
}


static inline void getsp(std::vector<double>& out, int itn, const sp_csr m,
           std::vector<double>& v, int N) {

    // auto t1 = std::chrono::steady_clock::now();
    out.resize(itn * 2);
    out[0] = sqrt(norm2(v));
    msv(1.0 / out[0], v);
    // auto t2 = std::chrono::steady_clock::now();
    // printf(
    //     "init time: %d\n",
    //     std::chrono::duration_cast<std::chrono::milliseconds>(t2 -
    //     t1).count());

    // auto mmv_time = std::chrono::milliseconds(0);
    // auto avv_time = std::chrono::milliseconds(0);
    // auto dot_time = std::chrono::milliseconds(0);
    // auto swap_time = std::chrono::milliseconds(0);
    
    
    // t1 = std::chrono::steady_clock::now();
    std::vector<double> a(itn), b(itn - 1);
    std::vector<double> v_(v.size()), v__(v.size());
    // t2 = std::chrono::steady_clock::now();
    // printf(
    //     "vector new time: %d\n",
    //     std::chrono::duration_cast<std::chrono::milliseconds>(t2 -
    //     t1).count());

    // auto t3 = std::chrono::steady_clock::now();
    for (int i = 0; i < itn; i++) {
        // t1 = std::chrono::steady_clock::now();
        v__.swap(v_);
        v_.swap(v);
        // t2 = std::chrono::steady_clock::now();
	// swap_time = std::chrono::duration_cast<std::chrono::milliseconds>(swap_time + t2 - t1);
        // t1 = std::chrono::steady_clock::now();
        mmv(v, m, v_);
	// t2 = std::chrono::steady_clock::now();
	// mmv_time = std::chrono::duration_cast<std::chrono::milliseconds>(mmv_time + t2 - t1);
    
    // t1 = std::chrono::steady_clock::now();
        a[i] = dot(v, v_);
        // t2 = std::chrono::steady_clock::now();
	// dot_time = std::chrono::duration_cast<std::chrono::milliseconds>(dot_time + t2 - t1);

    // t1 = std::chrono::steady_clock::now();
        if (i < itn - 1) {
            avv(v, -a[i], v_);
            if (i != 0) {
                avv(v, -b[i - 1], v__);
            }

            b[i] = sqrt(norm2(v));
            msv(1.0 / b[i], v);
        }
        // t2 = std::chrono::steady_clock::now();
	// avv_time = std::chrono::duration_cast<std::chrono::milliseconds>(avv_time + t2 - t1);
    }
    // auto t4 = std::chrono::steady_clock::now();
    // printf(
    //     "iter time: %d\n",
    //     std::chrono::duration_cast<std::chrono::milliseconds>(t4 -
    //     t3).count());

    // printf("mmv_time: %d\n", mmv_time.count());
    // printf("dot_time: %d\n", dot_time.count());
    // printf("avv_time: %d\n", avv_time.count());
    // printf("swap_time: %d\n", swap_time.count());

    // t1 = std::chrono::steady_clock::now();
    for (int i = 0; i < itn; i++) {
        out[1 + i] = a[i];
    }
    for (int i = 0; i < itn - 1; i++) {
        out[1 + itn + i] = b[i];
    }
    // t2 = std::chrono::steady_clock::now();
    // printf(
    //     "final time: %d\n",
    //     std::chrono::duration_cast<std::chrono::milliseconds>(t2 -
    //     t1).count());
}

int main() {
    FILE* fi;
    std::vector<uint64_t> table;
    map_t map;
    std::vector<term_t<double>> op;

    int N;

    fi = fopen("conf.data", "rb");
    // auto t1 = std::chrono::steady_clock::now();
    N = readss(fi, table, map);
    // auto t2 = std::chrono::steady_clock::now();
    readop(fi, op);

    sp_csr opm;
    opm.col.resize(table.size());
    opm.data.resize(table.size());

    // sparse_t opm;
    act(opm.col, opm.data, op, table, map);
    // auto t3 = std::chrono::steady_clock::now();

    int itn;
    fread(&itn, 1, 4, fi);

    std::vector<double> v(table.size());
    fread(v.data(), 1, table.size() * 8, fi);

    fclose(fi);

    // auto t5 = std::chrono::steady_clock::now();

    std::vector<double> result;
    getsp(result, itn, opm, v, N);

    // auto t4 = std::chrono::steady_clock::now();
    fi = fopen("out.data", "wb");
    fwrite(result.data(), 1, 16 * itn, fi);
    fclose(fi);

//     int d1 =
//         std::chrono::duration_cast<std::chrono::milliseconds>(t2 -
//         t1).count();
//     int d2 =
//         std::chrono::duration_cast<std::chrono::milliseconds>(t3 -
//         t2).count();
//     int d3 =
//         std::chrono::duration_cast<std::chrono::milliseconds>(t4 -
//         t3).count();
//     printf("%d,%d,%d\n", d1, d2, d3);
//     std::cout << "Hello World!\n";

//     printf(
//         "%d\n",
//         std::chrono::duration_cast<std::chrono::milliseconds>(t4 -
//         t5).count());
}
