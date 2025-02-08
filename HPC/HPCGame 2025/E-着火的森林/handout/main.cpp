#include <iostream>
#include <fstream>
#include <mpi.h>
#include <vector>

const int TREE = 1;
const int FIRE = 2;
const int ASH = 3;
const int EMPTY = 0;

struct Event {
    int ts;         // 事件触发的时间步
    int type;       // 事件类型：1（天降惊雷），2（妙手回春）
    int x1, y1;     // 事件的坐标或区域范围
    int x2, y2;     // 仅用于“妙手回春”事件
};

int main(int argc, char **argv) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <input_file> <output_file>" << std::endl;
        return 1;
    }
    const char *input_file = argv[1];
    const char *output_file = argv[2];

    
    return 0;
}