#include <iostream>
#include <vector>
#include <cstdint>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <cstring>
#include <chrono>
#include <algorithm>
#include <sys/socket.h>
#include <arpa/inet.h>

/* Some Helper Functions */
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

const int PATTERN_LEN = 64;

int main(int argc, char** argv) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <text_file> <pattern_file> <output_file>" << std::endl;
        return 1;
    }

    fix_cpu_affinity(); // MAYBE IMPORTANT: Adjust CPU affinity based on cgroup settings
    init_power_client("127.0.0.1", 19937);

    MappedFile f_pat(argv[2]);
    const uint8_t* p_ptr = (const uint8_t*)f_pat.data;
    uint32_t K = *(uint32_t*)p_ptr; 
    p_ptr += 4; 

    std::vector<const uint8_t*> patterns;
    patterns.reserve(K);
    for (uint32_t k = 0; k < K; ++k) {
        patterns.push_back(p_ptr + k * PATTERN_LEN);
    }

    MappedFile f_text(argv[1]);
    const uint8_t* t_ptr = (const uint8_t*)f_text.data;
    uint64_t N = *(uint64_t*)t_ptr; 
    const uint8_t* text = t_ptr + 8;

    auto start_time = std::chrono::high_resolution_clock::now();

    uint64_t total_matches = 0;

    if (N >= PATTERN_LEN) {
        for (uint64_t i = 0; i <= N - PATTERN_LEN; ++i) {
            const uint8_t* current_text_window = text + i;
            
            for (uint32_t k = 0; k < K; ++k) {
                const uint8_t* current_pat = patterns[k];
                int mismatch_count = 0;

                for (int j = 0; j < PATTERN_LEN; ++j) {
                    if (current_text_window[j] != current_pat[j]) {
                        if (mismatch_count > 1) {
                            break;
                        }
                        mismatch_count++;
                    }
                }

                if (mismatch_count <= 1) {
                    total_matches++;
                }
            }
        }
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    double duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count() / 1000.0;

    int out_fd = open(argv[3], O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (out_fd >= 0) {
        write(out_fd, &total_matches, sizeof(total_matches));
        close(out_fd);
    } else {
        perror("Output file open failed");
    }

    std::cout << "Time: " << duration << "s" << std::endl;
    if (g_sock >= 0) close(g_sock);

    return 0;
}