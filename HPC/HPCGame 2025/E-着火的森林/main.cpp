#include <mpi.h>

#include <fstream>
#include <iostream>
#include <vector>

const int TREE = 1;
const int FIRE = 2;
const int ASH = 3;
const int EMPTY = 0;

struct Event {
    int ts;      // 事件触发的时间步
    int type;    // 事件类型：1（天降惊雷），2（妙手回春）
    int x1, y1;  // 事件的坐标或区域范围
    int x2, y2;  // 仅用于“妙手回春”事件
};

inline size_t idx(int x, int y, int col_num) { return x * col_num + y; }

inline bool is_in_my_range(int x, int my_n, int rank) {
    return x >= rank * my_n && x < (rank + 1) * my_n;
}

inline bool is_in_my_big_range(int x, int my_n, int rank) {
    return x >= rank * my_n - 1 && x < (rank + 1) * my_n + 1;
}

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc < 3) {
        if (rank == 0) {
            std::cerr << "Usage: " << argv[0] << " <input_file> <output_file>"
                      << std::endl;

            MPI_Finalize();
            return 1;
        }
    }
    const char *input_file = argv[1];
    const char *output_file = argv[2];

    int n, m, t;

    // 读入输入

    std::ifstream fin(input_file);
    fin >> n >> m >> t;

    size_t n2 = n * n;
    size_t my_n = n / size;

    std::vector<char> all_forest(n2);
    std::vector<Event> events;

    for (size_t i = 0; i < n2; i++) {
        int tmp;
        fin >> tmp;
        all_forest[i] = tmp;
    }

    for (int i = 0; i < m; i++) {
        Event e;
        fin >> e.ts >> e.type >> e.x1 >> e.y1;
        if (e.type == 2) {
            fin >> e.x2 >> e.y2;
        }
        events.push_back(e);
    }

    fin.close();

    // 模拟

    int event_idx = 0;
    for (int ts = 1; ts <= t; ts++) {
        if (event_idx < m && events[event_idx].ts == ts) {
            // 处理事件
            const Event &e = events[event_idx];
            if (e.type == 1) {
                if (is_in_my_big_range(e.x1, my_n, rank)){
                    if (all_forest[idx(e.x1, e.y1, n)] == TREE) {
                        all_forest[idx(e.x1, e.y1, n)] = FIRE;
                    }
                }
            } else if (e.type == 2) {
                for (int x = e.x1; x <= e.x2; x++) {
                    if (!is_in_my_big_range(x, my_n, rank)) continue;
                    for (int y = e.y1; y <= e.y2; y++) {
                        if (all_forest[idx(x, y, n)] == ASH) {
                            all_forest[idx(x, y, n)] = TREE;
                        }
                    }
                }
            }
            event_idx++;
        }

        std::vector<char> new_forest(my_n * n);

        int x_start = rank * my_n;
        int x_end = x_start + my_n;

        for (int x = x_start; x < x_end; x++) {
            for (int y = 0; y < n; y++) {
                if (all_forest[idx(x, y, n)] == FIRE) {
                    new_forest[idx(x % my_n, y, n)] = ASH;
                } else if (all_forest[idx(x, y, n)] == TREE) {
                    if (x > 0 && all_forest[idx(x - 1, y, n)] == FIRE ||
                        x < n - 1 && all_forest[idx(x + 1, y, n)] == FIRE ||
                        y > 0 && all_forest[idx(x, y - 1, n)] == FIRE ||
                        y < n - 1 && all_forest[idx(x, y + 1, n)] == FIRE) {
                        new_forest[idx(x % my_n, y, n)] = FIRE;
                    } else {
                        new_forest[idx(x % my_n, y, n)] = TREE;
                    }
                } else {
                    new_forest[idx(x % my_n, y, n)] = all_forest[idx(x, y, n)];
                }
            }
        }

        // 覆盖 all_forest
        for (int x = x_start; x < x_end; x++) {
            for (int y = 0; y < n; y++) {
                all_forest[idx(x, y, n)] = new_forest[idx(x % my_n, y, n)];
            }
        }

        // 通信，交换边界

        // 第一步，向后传递
        if (rank < size - 1) {
            MPI_Send(new_forest.data() + (my_n - 1) * n, n, MPI_BYTE, rank + 1,
                     0, MPI_COMM_WORLD);
        }
        if (rank > 0) {
            MPI_Recv(all_forest.data() + (rank * my_n - 1) * n, n, MPI_BYTE,
                     rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }

        // 第二步，向前传递
        if (rank > 0) {
            MPI_Send(new_forest.data(), n, MPI_BYTE, rank - 1, 1,
                     MPI_COMM_WORLD);
        }
        if (rank < size - 1) {
            MPI_Recv(all_forest.data() + (rank + 1) * my_n * n, n, MPI_BYTE,
                     rank + 1, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }

        MPI_Barrier(MPI_COMM_WORLD);
    }

    // 收集结果
    if (rank == 0) {
        for (int i = 1; i < size; i++) {
            MPI_Recv(all_forest.data() + i * my_n * n, my_n * n, MPI_BYTE, i, 2,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
    } else {
        MPI_Send(all_forest.data() + rank * my_n * n, my_n * n, MPI_BYTE, 0, 2,
                 MPI_COMM_WORLD);
    }

    if (rank == 0) {
        // 输出
        std::ofstream fout(output_file);
        for (int x = 0; x < n; x++) {
            for (int y = 0; y < n; y++) {
                fout << (int)all_forest[idx(x, y, n)] << " ";
            }
            fout << std::endl;
        }
        fout.close();
    }

    MPI_Finalize();
    return 0;
}