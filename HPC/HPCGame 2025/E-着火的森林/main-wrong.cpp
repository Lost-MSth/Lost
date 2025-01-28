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

    if (rank == 0) {

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
    }

    fin.close();

    // 模拟

    int event_idx = 0;
    for (int ts = 1; ts <= t; ts++) {
        if (rank == 0) {
            if (event_idx < m && events[event_idx].ts == ts) {
                // 处理事件
                const Event &e = events[event_idx];
                if (e.type == 1) {
                    all_forest[idx(e.x1, e.y1, n)] = FIRE;
                } else if (e.type == 2) {
                    for (int x = e.x1; x <= e.x2; x++) {
                        for (int y = e.y1; y <= e.y2; y++) {
                            if (all_forest[idx(x, y, n)] == ASH) {
                                all_forest[idx(x, y, n)] = TREE;
                            }
                        }
                    }
                }
                event_idx++;
            }
        }

        // 广播森林状态到所有节点
        // 反正这个数据量不大，直接广播了
        // MPI_Bcast(all_forest.data(), n2, MPI_BYTE, 0, MPI_COMM_WORLD);
        // 不能直接广播，传输量太大，会导致超时
        if (rank == 0) {
            for (int i = 1; i < size; i++) {
                size_t offset = i * my_n * n - n;
                size_t count = my_n * n + n * 2;
                // 多传输上下各一行，以便计算
                if (i == size - 1) {
                    count = my_n * n + n;
                    // 最后一个节点不用传输下一行
                }
                MPI_Send(all_forest.data() + offset, count, MPI_BYTE, i, 0,
                         MPI_COMM_WORLD);
            }
        } else {
            size_t offset = rank * my_n * n - n;
            size_t count = my_n * n + n * 2;
            if (rank == size - 1) {
                count = my_n * n + n;
            }
            MPI_Recv(all_forest.data() + offset, count, MPI_BYTE, 0, 0,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
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
                    new_forest[idx(x % my_n, y, n)] =
                        all_forest[idx(x, y, n)];
                }
            }
        }

        if (rank == 0) {
            // 收集各个节点的森林状态
            std::vector<char> new_all_forest(n2);
            for (int i = 0; i < my_n; i++) {
                for (int j = 0; j < n; j++) {
                    new_all_forest[idx(i, j, n)] = new_forest[idx(i, j, n)];
                }
            }
            for (int i = 1; i < size; i++) {
                MPI_Recv(new_all_forest.data() + i * my_n * n, my_n * n,
                         MPI_BYTE, i, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            }
            all_forest.swap(new_all_forest);
        } else {
            MPI_Send(new_forest.data(), my_n * n, MPI_BYTE, 0, 1,
                     MPI_COMM_WORLD);
        }
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