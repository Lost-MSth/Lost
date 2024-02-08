#include <vector>
#include <unordered_map>
#include <stdint.h>
#include <math.h>
#include <chrono>

#ifdef _WIN32
#include <windows.h>
#define popcnt __popcnt64
#else
#define popcnt __builtin_popcountll
#endif

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

struct sparse_t {
    std::vector<size_t> row;
    std::vector<size_t> col;
    std::vector<double> data;
};

int itrest(restrict_t& rest) {
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

int itrest(std::vector<restrict_t>& rest) {
    for (restrict_t& re : rest) {
        if (!itrest(re)) {
            return 0;
        }
    }
    return 1;
}

uint64_t getstate(const std::vector<restrict_t>& rest) {
    uint64_t state = 0;
    for (const restrict_t& re : rest) {
        state |= re.substate << re.offset;
    }
    return state;
}

int generatetable(std::vector<uint64_t>& table, map_t& map, std::vector<restrict_t>& rest) {
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
term_t<VT> getterm(VT value, const std::vector<int>& cr, const std::vector<int>& an) {
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
int act(std::vector<size_t>& row, std::vector<size_t>& col, std::vector<VT>& data, const std::vector<term_t<VT>>& op, const std::vector<uint64_t>& table, const map_t& map) {
    int64_t n = table.size();

    for (int64_t i = 0; i < n; i++) {
        uint64_t srcstate = table[i];

        for (const term_t<VT>& term : op) {
            if ((srcstate & term.an) == term.an) {
                uint64_t dststate = srcstate ^ term.an;
                if ((dststate & term.cr) == 0) {
                    dststate ^= term.cr;

                    auto it = map.find(dststate);
                    if (it != map.end()) {
                        uint64_t sign = term.sign + popcnt(srcstate & term.signmask);
                        VT v = term.value;
                        if (sign & 1) {
                            v = -v;
                        }
                        data.push_back(v);
                        col.push_back(i);
                        row.push_back(it->second);
                    }
                }
            }
        }
    }

    return 0;
}

int readss(FILE* fi, std::vector<uint64_t>& table, map_t& map) {
    int n;
    fread(&n, 1, 4, fi);
    std::vector<restrict_t> restv(n);
    for (auto& rest : restv) {
        fread(&rest, 1, 16, fi);
    }
    generatetable(table, map, restv);
    return 0;
}

int readop(FILE* fi, std::vector<term_t<double>>& op) {
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
            }
            else {
                an.push_back(rawterm[tn * 2 - j * 2]);
            }
        }

        op.push_back(getterm(v[i], cr, an));
        cr.clear();
        an.clear();
    }

    return 0;
}

//out=m*v;
void mmv(std::vector<double>& out, const sparse_t& m, const std::vector<double>& v) {
    for (auto& x : out) {
        x = 0;
    }

    for (size_t i = 0; i < m.data.size(); i++) {
        out[m.row[i]] += m.data[i] * v[m.col[i]];
    }
}

//v1'*v2;
double dot(const std::vector<double>& v1, const std::vector<double>& v2) {
    double s = 0;
    for (size_t i = 0; i < v1.size(); i++) {
        s += v1[i] * v2[i];
    }
    return s;
}

//v1+=s*v2;
void avv(std::vector<double>& v1, const double s, const std::vector<double>& v2) {
    for (size_t i = 0; i < v1.size(); i++) {
        v1[i] += s * v2[i];
    }
}

//v*=s;
void msv(const double s, std::vector<double>& v) {
    for (auto& x : v) {
        x *= s;
    }
}

//v'*v;
double norm2(const std::vector<double>& v) {
    double s = 0;
    for (auto& x : v) {
        s += x * x;
    }
    return s;
}

void getsp(std::vector<double>& out, int itn, const sparse_t m, std::vector<double>& v) {
    out.resize(itn * 2);
    out[0] = sqrt(norm2(v));
    msv(1.0 / out[0], v);

    std::vector<double> a(itn), b(itn - 1);

    std::vector<double> v_(v.size()), v__(v.size());
    for (int i = 0; i < itn; i++) {
        v__.swap(v_);
        v_.swap(v);
        mmv(v, m, v_);
        a[i] = dot(v, v_);

        if (i < itn - 1) {
            if (i == 0) {
                avv(v, -a[i], v_);
            }
            else {
                avv(v, -a[i], v_);
                avv(v, -b[i - 1], v__);
            }

            b[i] = sqrt(norm2(v));
            msv(1.0 / b[i], v);
        }
    }

    for (int i = 0; i < itn; i++) {
        out[1 + i] = a[i];
    }
    for (int i = 0; i < itn - 1; i++) {
        out[1 + itn + i] = b[i];
    }
}

int main()
{
    FILE* fi;
    std::vector<uint64_t> table;
    map_t map;
    std::vector<term_t<double>> op;

    fi = fopen("conf.data", "rb");
    auto t1 = std::chrono::steady_clock::now();
    readss(fi, table, map);
    auto t2 = std::chrono::steady_clock::now();
    readop(fi, op);

    sparse_t opm;
    act(opm.row, opm.col, opm.data, op, table, map);
    auto t3 = std::chrono::steady_clock::now();

    int itn;
    fread(&itn, 1, 4, fi);

    std::vector<double> v(table.size());
    fread(v.data(), 1, table.size() * 8, fi);

    fclose(fi);

    std::vector<double> result;
    getsp(result, itn, opm, v);

    auto t4 = std::chrono::steady_clock::now();
    fi = fopen("out.data", "wb");
    fwrite(result.data(), 1, 16 * itn, fi);
    fclose(fi);

    int d1 = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
    int d2 = std::chrono::duration_cast<std::chrono::milliseconds>(t3 - t2).count();
    int d3 = std::chrono::duration_cast<std::chrono::milliseconds>(t4 - t3).count();
    printf("%d,%d,%d\n", d1, d2, d3);
    std::cout << "Hello World!\n";
}
