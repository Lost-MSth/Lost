#include <iostream>
#include <vector>
#include <array>
#include <cstdint>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <cstring>
#include <algorithm>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <atomic>
#include <thread>
#include <immintrin.h>
#include <omp.h>
#ifdef __x86_64__
#include <x86intrin.h>
#endif

/* ====== Baseline-required power client + affinity (COPY AS-IS) ====== */
int g_sock = -1;

void init_power_client(const char* ip, int port) {
    if ((g_sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("Socket creation error");
        exit(1);
    }

    struct sockaddr_in serv_addr;
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);

    if (inet_pton(AF_INET, ip, &serv_addr.sin_addr) <= 0) {
        perror("Invalid address/ Address not supported");
        exit(1);
    }

    if (connect(g_sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        perror("Connection Failed");
        exit(1);
    }
}

std::pair<double, double> get_remote_power() {
    if (g_sock < 0) return {0.0, 0.0};

    const char* msg = "GET\n";
    send(g_sock, msg, strlen(msg), 0);

    char buffer[128] = {0};
    int valread = read(g_sock, buffer, 128);

    if (valread > 0) {
        double cpu, gpu;
        sscanf(buffer, "%lf %lf", &cpu, &gpu);
        return {cpu, gpu};
    }
    return {0.0, 0.0};
}

struct MappedFile {
    int fd; void* data; size_t size;
    MappedFile(const char* fn) {
        fd = open(fn, O_RDONLY);
        if (fd < 0) { perror("open"); exit(1); }
        struct stat sb; fstat(fd, &sb); size = sb.st_size;
        data = mmap(NULL, size, PROT_READ, MAP_PRIVATE | MAP_POPULATE, fd, 0);
        if (data == MAP_FAILED) { perror("mmap"); exit(1); }
    }
    ~MappedFile() { munmap(data, size); close(fd); }
};

std::vector<int> parse_cpu_range(const std::string& s) {
    std::vector<int> cpus;
    size_t start = 0;
    while (start < s.size()) {
        size_t comma = s.find(',', start);
        if (comma == std::string::npos) comma = s.size();
        std::string part = s.substr(start, comma - start);

        size_t dash = part.find('-');
        if (dash != std::string::npos) {
            int a = std::stoi(part.substr(0, dash));
            int b = std::stoi(part.substr(dash + 1));
            for (int i = a; i <= b; ++i) cpus.push_back(i);
        } else {
            cpus.push_back(std::stoi(part));
        }
        start = comma + 1;
    }
    return cpus;
}

void fix_cpu_affinity() {
    FILE* f = fopen("/sys/fs/cgroup/cpuset.cpus", "r");
    if (!f) f = fopen("/sys/fs/cgroup/cpuset.cpus.effective", "r");
    if (!f) f = fopen("/sys/fs/cgroup/cpuset/cpuset.cpus", "r");

    if (!f) {
        fprintf(stderr, "[AFFINITY] Cannot read cgroup cpuset\n");
        return;
    }

    char buf[256];
    if (!fgets(buf, sizeof(buf), f)) {
        fclose(f);
        fprintf(stderr, "[AFFINITY] Cannot read cpuset content\n");
        return;
    }
    fclose(f);
    size_t len = strlen(buf);
    if (len > 0 && buf[len-1] == '\n') buf[len-1] = '\0';

    fprintf(stderr, "[AFFINITY] Cgroup cpuset: %s\n", buf);

    std::vector<int> cpus = parse_cpu_range(buf);
    fprintf(stderr, "[AFFINITY] Parsed %zu CPUs\n", cpus.size());

    if (cpus.empty()) return;

    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    for (int cpu : cpus) {
        CPU_SET(cpu, &cpuset);
    }

    if (sched_setaffinity(0, sizeof(cpuset), &cpuset) == 0) {
        fprintf(stderr, "[AFFINITY] Successfully set affinity to %zu CPUs\n", cpus.size());
    } else {
        perror("[AFFINITY] sched_setaffinity failed");
    }
}

/* ====== Fast rolling hash (buzhash, window length = 64) ====== */
static inline uint64_t rotl1(uint64_t x) { return (x << 1) | (x >> 63); }

static inline uint64_t splitmix64(uint64_t &x) {
    uint64_t z = (x += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

static inline uint64_t fmix64(uint64_t k) {
    k ^= k >> 33;
    k *= 0xff51afd7ed558ccdULL;
    k ^= k >> 33;
    k *= 0xc4ceb9fe1a85ec53ULL;
    k ^= k >> 33;
    return k;
}

static inline bool equal64(const uint8_t* a, const uint8_t* b) {
#if defined(__AVX512F__)
    __m512i va = _mm512_loadu_si512((const void*)a);
    __m512i vb = _mm512_loadu_si512((const void*)b);
    __mmask64 m = _mm512_cmpeq_epi8_mask(va, vb);
    return m == (__mmask64)~0ULL;
#else
    return std::memcmp(a, b, 64) == 0;
#endif
}

/* ====== Variant hash table (open addressing) ====== */
struct Entry {
    uint64_t h;        // 0 == empty
    uint32_t cnt;
    uint32_t idx;      // index into keys[]
};

struct VariantTable {
    std::vector<Entry> tab;
    std::vector<std::array<uint8_t,64>> keys;
    uint64_t mask;

    VariantTable(size_t cap_pow2 = 1 << 21) {
        size_t cap = 1;
        while (cap < cap_pow2) cap <<= 1;
        tab.assign(cap, Entry{0,0,0});
        mask = (uint64_t)(cap - 1);
        keys.reserve(900000);
    }

    inline void insert(const uint8_t* key, uint64_t h, uint32_t add) {
        if (h == 0) h = 1; // keep 0 as empty
        uint64_t pos = fmix64(h) & mask;
        for (;;) {
            Entry &e = tab[(size_t)pos];
            if (e.h == 0) {
                std::array<uint8_t,64> arr;
                std::memcpy(arr.data(), key, 64);
                uint32_t id = (uint32_t)keys.size();
                keys.push_back(arr);
                e.h = h;
                e.cnt = add;
                e.idx = id;
                return;
            }
            if (e.h == h) {
                if (equal64(key, keys[e.idx].data())) {
                    e.cnt += add;
                    return;
                }
            }
            pos = (pos + 1) & mask;
        }
    }

    inline uint32_t lookup(const uint8_t* window, uint64_t h) const {
        if (h == 0) h = 1;
        uint64_t pos = fmix64(h) & mask;
        for (;;) {
            const Entry &e = tab[(size_t)pos];
            if (e.h == 0) return 0;
            if (e.h == h) {
                if (equal64(window, keys[e.idx].data())) return e.cnt;
            }
            pos = (pos + 1) & mask;
        }
    }
};

/* ====== Power limiter (simple controller) ====== */
static std::atomic<uint32_t> g_pause_cycles{0};
static std::atomic<bool> g_stop_monitor{false};

static inline void do_pause_cycles(uint32_t cyc) {
#if defined(__x86_64__)
    if (cyc == 0) return;
    uint64_t start = __rdtsc();
    while ((uint64_t)(__rdtsc() - start) < cyc) {
        _mm_pause();
    }
#else
    (void)cyc;
#endif
}

static void power_monitor_thread(double limit_watts) {
    double ema = 0.0;
    while (!g_stop_monitor.load(std::memory_order_relaxed)) {
        auto pw = get_remote_power();
        double total = pw.first + pw.second;
        ema = 0.8 * ema + 0.2 * total;

        double over = ema - limit_watts;
        uint32_t cyc = 0;
        if (over > 0.0) {
            double scale = 20000.0; // cycles per watt overshoot
            double base  = 20000.0; // base cycles once over
            double v = base + over * scale;
            if (v > 120000.0) v = 120000.0;
            cyc = (uint32_t)v;
        }
        g_pause_cycles.store(cyc, std::memory_order_relaxed);

        struct timespec ts; ts.tv_sec = 0; ts.tv_nsec = 2 * 1000 * 1000;
        nanosleep(&ts, nullptr);
    }
}

/* ====== Main ====== */
static constexpr int PATTERN_LEN = 64;

int main(int argc, char** argv) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <text_file> <pattern_file> <output_file>\n";
        return 1;
    }

    fix_cpu_affinity();                 // 原样照抄
    init_power_client("127.0.0.1", 19937); // 原样照抄

    MappedFile f_pat(argv[2]);
    const uint8_t* p_ptr = (const uint8_t*)f_pat.data;
    uint32_t K = *(const uint32_t*)p_ptr;
    p_ptr += 4;
    std::vector<const uint8_t*> patterns;
    patterns.reserve(K);
    for (uint32_t k = 0; k < K; ++k) patterns.push_back(p_ptr + (size_t)k * PATTERN_LEN);

    MappedFile f_text(argv[1]);
    const uint8_t* t_ptr = (const uint8_t*)f_text.data;
    uint64_t N = *(const uint64_t*)t_ptr;
    const uint8_t* text = t_ptr + 8;

    uint64_t total_matches = 0;
    if (N < PATTERN_LEN || K == 0) {
        int out_fd = open(argv[3], O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (out_fd >= 0) { write(out_fd, &total_matches, sizeof(total_matches)); close(out_fd); }
        if (g_sock >= 0) close(g_sock);
        return 0;
    }

    // randomized buzhash table
    uint64_t seed = 0x123456789abcdef0ULL;
#if defined(__x86_64__)
    seed ^= (uint64_t)__rdtsc();
#endif
    seed ^= (uint64_t)(uintptr_t)&seed;

    uint64_t rnd[256];
    for (int i = 0; i < 256; ++i) rnd[i] = splitmix64(seed);

    auto hash64_bytes = [&](const uint8_t* s) -> uint64_t {
        uint64_t h = 0;
        for (int i = 0; i < 64; ++i) h = rotl1(h) ^ rnd[s[i]];
        return h;
    };

    // build variant dictionary: all strings within Hamming dist <= 1 from patterns
    VariantTable vt(1 << 21); // 2,097,152 slots

    std::array<uint8_t, 64> tmp;
    for (uint32_t k = 0; k < K; ++k) {
        const uint8_t* p = patterns[k];

        std::memcpy(tmp.data(), p, 64);
        vt.insert(tmp.data(), hash64_bytes(tmp.data()), 1);

        for (int j = 0; j < 64; ++j) {
            uint8_t orig = tmp[j];
            for (uint8_t c = (uint8_t)'a'; c <= (uint8_t)'z'; ++c) {
                if (c == orig) continue;
                tmp[j] = c;
                vt.insert(tmp.data(), hash64_bytes(tmp.data()), 1);
            }
            tmp[j] = orig;
        }
    }

    // monitor thread
    std::thread mon;
    if (g_sock >= 0) {
        g_stop_monitor.store(false, std::memory_order_relaxed);
        mon = std::thread(power_monitor_thread, 600.0);
    }

    const uint64_t last = N - PATTERN_LEN; // last window start

#pragma omp parallel reduction(+:total_matches)
    {
        int tid = omp_get_thread_num();
        int nt  = omp_get_num_threads();

        const uint64_t total = last + 1;
        uint64_t begin = total * (uint64_t)tid / (uint64_t)nt;
        uint64_t end_excl = total * (uint64_t)(tid + 1) / (uint64_t)nt;

        if (begin < end_excl) {
            uint64_t end = end_excl - 1;

            uint64_t h = 0;
            const uint8_t* w = text + begin;
            for (int i = 0; i < 64; ++i) h = rotl1(h) ^ rnd[w[i]];

            const uint64_t CHECK_MASK = 0x7FFF; // every 32768 iters
            for (uint64_t i = begin; i <= end; ++i) {
                total_matches += vt.lookup(text + i, h);

                if ((i & CHECK_MASK) == 0) {
                    uint32_t cyc = g_pause_cycles.load(std::memory_order_relaxed);
                    do_pause_cycles(cyc);
                }

                if (i != end) {
                    uint8_t outb = text[i];
                    uint8_t inb  = text[i + 64];
                    // L=64 -> leaving term is just rnd[outb]
                    h = rotl1(h) ^ rnd[outb] ^ rnd[inb];
                }
            }
        }
    }

    if (g_sock >= 0) {
        g_stop_monitor.store(true, std::memory_order_relaxed);
        if (mon.joinable()) mon.join();
    }

    int out_fd = open(argv[3], O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (out_fd >= 0) {
        write(out_fd, &total_matches, sizeof(total_matches));
        close(out_fd);
    } else {
        perror("Output file open failed");
    }

    if (g_sock >= 0) close(g_sock);
    return 0;
}
