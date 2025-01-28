# 本脚本接受三个参数：n ts filename
# n 对应题目描述文档中的 n，即为森林的尺寸
# ts 对应题目描述文档中的 t，即为需要模拟的总时间步数
# filename 对应生成的输入文件的名字
# 
# 用法例如： python3 gencase.py 1024 100 forest.in
# 
# 注意，在用本脚本生成输入文件时，不需要输入题目描述文档中的 m（即魔法事件的个数）
# 这是因为魔法事件的个数是在本脚本中被硬编码的。具体而言：
# 有 50% 的时间步会发生“妙手回春”事件
# 有 30% 的时间步会发生“天降惊雷”事件
# 两个事件的发生次数相加即可得到魔法事件的总个数（也就是输入文件中的 m）

# 初始地图生成：
# 15% 的点是空地（状态0），83% 的点是树木（状态1），2%的点是燃烧（状态2），没有点是灰烬（状态3）

import random
import sys

def generate(n, ts, filename):
    # 15% 的点是空地（状态0），83% 的点是树木（状态1），2%的点是燃烧（状态2），没有点是灰烬（状态3）
    grid = [[random.choices([0, 1, 2], weights=[15, 83, 2])[0] for _ in range(n)] for _ in range(n)]

    events = []
    event_types = []
    num_miao = int(0.5 * ts)  # 有 50% 的时间步会发生“妙手回春”事件
    num_tian = int(0.3 * ts)  # 有 30% 的时间步会发生“天降惊雷”事件
    num_none = ts - num_miao - num_tian

    for _ in range(num_miao):
        event_types.append(2)
    for _ in range(num_tian):
        event_types.append(1)
    for _ in range(num_none):
        event_types.append(0)

    random.shuffle(event_types)

    for i in range(ts):
        event_type = event_types[i]
        time_step = i + 1

        if event_type == 2:
            # 妙手回春，生成矩形区域[sx, sy, ex, ey]
            # 生成dx和dy，使用高斯分布，让矩形区域的覆盖范围以比较大的概率是一个比较大的范围
            dx = int(random.gauss(n / 2, n / 4))
            if dx < 1:
                dx = 1
            elif dx > n - 1:
                dx = n - 1
            sx = random.randint(0, n - dx)
            ex = sx + dx - 1
            
            dy = int(random.gauss(n / 2, n / 4))
            if dy < 1:
                dy = 1
            elif dy > n - 1:
                dy = n - 1
            sy = random.randint(0, n - dy)
            ey = sy + dy - 1

            assert 0 <= sx <= ex <= n-1 and 0 <= sy <= ey <= n-1
            events.append((time_step, event_type, sx, sy, ex, ey))
        elif event_type == 1:
            # 天降惊雷，生成坐标(x, y)
            x = random.randint(0, n-1)
            y = random.randint(0, n-1)
            events.append((time_step, event_type, x, y))
        # 无效事件不生成具体参数
    
    # 按顺序输出事件
    events.sort(key=lambda x: x[0])

    # 写入文件
    with open(filename, 'w') as f:
        f.write(f"{n} {num_miao + num_tian} {ts}\n")
        for row in grid:
            f.write(' '.join(map(str, row)) + '\n')
        for event in events:
            if event[1] == 2:
                assert 1 <= event[0] <= ts
                f.write(f"{event[0]} 2 {event[2]} {event[3]} {event[4]} {event[5]}\n")
            elif event[1] == 1:
                assert 1 <= event[0] <= ts
                f.write(f"{event[0]} 1 {event[2]} {event[3]}\n")
            # 无效事件不写入文件
    

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python gencase.py n ts filename")
        sys.exit(1)

    n = int(sys.argv[1])
    ts = int(sys.argv[2])
    filename = sys.argv[3]

    generate(n, ts, filename)
