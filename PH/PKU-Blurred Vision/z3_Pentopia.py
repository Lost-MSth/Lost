# time elapsed ~ 320s

import time

from z3 import *

N = 13
M = 13

BLOCK_NUM = 12

a = [[Int('a_%d_%d' % (i, j)) for j in range(M)] for i in range(N)]


s = Solver()

for i in range(N):
    for j in range(M):
        # 0 用来表示空白
        s.add(And(a[i][j] >= 0, a[i][j] <= BLOCK_NUM))

FOUR_DIRS = [(0, 1), (-1, 0), (0, -1), (1, 0)]
EIGHT_DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0),
              (1, 1), (1, -1), (-1, 1), (-1, -1)]


def check_range(x, y):
    return x >= 0 and x < N and y >= 0 and y < M


# area = 5
for num in range(1, BLOCK_NUM+1):
    sums = 0
    for i in range(N):
        for j in range(M):
            sums += If(a[i][j] == num, 1, 0)
    s.add(sums == 5)

# connected blocks
for i in range(N):
    for j in range(M):
        # 异色不可连通，八个方向必须无异色
        for dx, dy in EIGHT_DIRS:
            x, y = i + dx, j + dy
            if check_range(x, y):
                s.add(Implies(
                    a[i][j] != 0,
                    Or(a[x][y] == 0, a[i][j] == a[x][y])
                ))

        # 同色连通，四个方向必须有一个相同
        f = False
        nearest_count = 0
        for dx, dy in FOUR_DIRS:
            x, y = i + dx, j + dy
            if check_range(x, y):
                nearest_count += If(a[x][y] == a[i][j], 1, 0)
                f = Or(f, a[i][j] == a[x][y])
        s.add(Implies(a[i][j] != 0, f))

        # 判断只有一个同色连通块，注意只会出现 2+3，所以排除 2 即可
        f = False
        for dx, dy in FOUR_DIRS:
            x, y = i + dx, j + dy
            if not check_range(x, y):
                continue
            next_nearest_count = 0
            for ddx, ddy in FOUR_DIRS:
                xx, yy = x + ddx, y + ddy
                if check_range(xx, yy):
                    next_nearest_count += If(And(a[xx][yy] == a[x][y],
                                                 a[x][y] == a[i][j]), 1, 0)
            f = Or(f, Or(
                next_nearest_count == 2,
                next_nearest_count == 3,
                next_nearest_count == 4,
            ))
        s.add(Implies(And(a[i][j] != 0, nearest_count == 1), f))

# 黑色垂直箭头
black_arrow = {
    (0, 0), (0, 4),
    (1, 1), (1, 2), (1, 7),
    (2, 1), (2, 2),
    (3, 3), (3, 8),
    (4, 4),
    (5, 5), (5, 6),
    (6, 6), (6, 5), (6, 3),
    (7, 7),
    (8, 8), (8, 12),
    (9, 9), (9, 10),
    (10, 10), (10, 9), (10, 6),
    (11, 11),
    (12, 12), (12, 8),
}

# 白色相对箭头
white_arrow = {
    (1, 11), (1, 12),
    (10, 0), (10, 1),
}

MAX_DIST = max(N, M) // 3  # 只是猜测


def all_zero(lst):
    if not lst:
        return True
    return And([x == 0 for x in lst])


def white_arrow_check(lst):
    return Or([
        And(
            lst[i] == 2,
            lst[(i+1) % 2] == 0,
        )
        for i in range(2)
    ])


def black_arrow_check(lst):
    return Or(
        [
            And(
                lst[i] == 2,
                lst[(i+2) % 4] == 0,
            )
            for i in range(4)
        ]
    )


def flatten_two(lst):
    return [x for sub in lst for x in sub]


def check_black(near_count):
    # 箭头垂直
    new_count = [[0 for _ in range(4)] for _ in range(MAX_DIST)]
    for d in range(MAX_DIST):
        for i in range(4):
            new_count[d][i] = near_count[d][i] + near_count[d][(i+1) % 4]

    return Or(
        [
            And(
                black_arrow_check(new_count[d]),
                all_zero(flatten_two(new_count[:d]))
            )
            for d in range(MAX_DIST)
        ]
    )


def check_white(near_count):
    # 箭头相对
    new_count = [[0 for _ in range(2)] for _ in range(MAX_DIST)]
    for d in range(MAX_DIST):
        for i in range(2):
            new_count[d][i] = near_count[d][i] + near_count[d][i+2]

    return Or(
        [
            And(
                white_arrow_check(new_count[d]),
                all_zero(flatten_two(new_count[:d]))
            )
            for d in range(MAX_DIST)
        ]
    )


def check_nearest(x, y, color):
    near_count = [[0 for _ in range(4)] for _ in range(MAX_DIST)]
    for d in range(1, MAX_DIST+1):
        for i, (dx, dy) in enumerate(FOUR_DIRS):
            nx, ny = x + dx * d, y + dy * d
            if check_range(nx, ny):
                near_count[d-1][i] = If(a[nx][ny] != 0, 1, 0)

    if color == 'black':
        return check_black(near_count)
    elif color == 'white':
        return check_white(near_count)
    else:
        raise ValueError('color should be black or white')


for x, y in black_arrow:
    s.add(a[x][y] == 0)
    s.add(check_nearest(x, y, 'black'))

for x, y in white_arrow:
    s.add(a[x][y] == 0)
    s.add(check_nearest(x, y, 'white'))


start = time.time()
res = s.check()
print(f'elapsed time: {time.time() - start}')

assert res == sat
m = s.model()


for i in range(N):
    for j in range(M):
        x = m[a[i][j]].as_long()
        if x == 0:
            if (i, j) in black_arrow:
                x = 'B'
            elif (i, j) in white_arrow:
                x = 'W'
            else:
                x = '.'
        print(str(x).rjust(2), end=' ')
    print()
