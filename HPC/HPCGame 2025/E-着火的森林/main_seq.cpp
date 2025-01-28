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
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <input_file> <output_file>"
                  << std::endl;
        return 1;
    }
    const char *input_file = argv[1];
    const char *output_file = argv[2];

    int n, m, t;

    // 读入输入

    std::ifstream fin(input_file);
    fin >> n >> m >> t;

    size_t n2 = n * n;

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
                if (all_forest[idx(e.x1, e.y1, n)] == TREE) {
                    all_forest[idx(e.x1, e.y1, n)] = FIRE;
                }
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

        std::vector<char> new_forest(n2);

        for (int x = 0; x < n; x++) {
            for (int y = 0; y < n; y++) {
                if (all_forest[idx(x, y, n)] == FIRE) {
                    new_forest[idx(x, y, n)] = ASH;
                } else if (all_forest[idx(x, y, n)] == TREE) {
                    if (x > 0 && all_forest[idx(x - 1, y, n)] == FIRE ||
                        x < n - 1 && all_forest[idx(x + 1, y, n)] == FIRE ||
                        y > 0 && all_forest[idx(x, y - 1, n)] == FIRE ||
                        y < n - 1 && all_forest[idx(x, y + 1, n)] == FIRE) {
                        new_forest[idx(x, y, n)] = FIRE;
                    } else {
                        new_forest[idx(x, y, n)] = TREE;
                    }
                } else {
                    new_forest[idx(x, y, n)] = all_forest[idx(x, y, n)];
                }
            }
        }

        all_forest.swap(new_forest);
    }

    // 输出
    std::ofstream fout(output_file);
    for (int x = 0; x < n; x++) {
        for (int y = 0; y < n; y++) {
            fout << (int)all_forest[idx(x, y, n)] << " ";
        }
        fout << std::endl;
    }
    fout.close();

    return 0;
}