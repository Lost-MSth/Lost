from z3 import *

N = 8
M = 8

# 扫雷，特殊规则：对偶，所有的雷构成若干 1*2 的矩形，矩形之间不在四方向上相邻

MINE_AMOUNT = 22
MINE_NUMBERS = {
    (0, 0): 2, (0, 7): 1,
    (1, 4): 3,
    (2, 3): 3, (2, 5): 3,
    (3, 2): 3, (3, 6): 3,
    (4, 0): 2, (4, 3): 4, (4, 5): 3,
    (5, 4): 3,
    (6, 1): 2,
    (7, 3): 2,
}
NOT_MINES = [(7, 0), (7, 7)]


assert MINE_AMOUNT % 2 == 0, 'MINE_AMOUNT must be even'


mine_flags = [BoolVector('mine_flag_%d' % i, M) for i in range(N)]
mine_counters = [IntVector('mine_counter_%d' % i, M) for i in range(N)]


s = Solver()

EIGHT_DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0),
              (1, 1), (1, -1), (-1, 1), (-1, -1)]


def in_bound(x, y):
    return x >= 0 and x < N and y >= 0 and y < M


mine_counter = 0
for i in range(N):
    for j in range(M):
        s.add(mine_counters[i][j] >= 0, mine_counters[i][j] <= 8)

        counter = 0
        for dx, dy in EIGHT_DIRS:
            x, y = i + dx, j + dy
            if in_bound(x, y):
                counter += If(mine_flags[x][y], 1, 0)
        s.add(mine_counters[i][j] == counter)

        mine_counter += If(mine_flags[i][j], 1, 0)

        if (i, j) in MINE_NUMBERS:
            s.add(mine_counters[i][j] == MINE_NUMBERS[(i, j)])
            s.add(mine_flags[i][j] == False)  # has number, so not mine

s.add(mine_counter == MINE_AMOUNT)

for x, y in NOT_MINES:
    s.add(mine_flags[x][y] == False)


def special_rule():

    FOUR_DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    # 竖向 2*1
    for i in range(N-1):
        for j in range(M):
            f = False
            for di in range(0, 2):
                for dx, dy in FOUR_DIRS:
                    x, y = i + dx + di, j + dy
                    if in_bound(x, y) and not (x == i and y == j) and not (x == i+1 and y == j):
                        f = Or(f, mine_flags[x][y])
            s.add(
                Implies(
                    And(mine_flags[i][j], mine_flags[i+1][j]),
                    Not(f)
                )
            )

    # 横向 1*2
    for i in range(N):
        for j in range(M-1):
            f = False
            for dj in range(0, 2):
                for dx, dy in FOUR_DIRS:
                    x, y = i + dx, j + dy + dj
                    if in_bound(x, y) and not (x == i and y == j) and not (x == i and y == j+1):
                        f = Or(f, mine_flags[x][y])
            s.add(
                Implies(
                    And(mine_flags[i][j], mine_flags[i][j+1]),
                    Not(f)
                )
            )

    # 要求雷不独立
    for i in range(N):
        for j in range(M):
            f = False
            for dx, dy in FOUR_DIRS:
                x, y = i + dx, j + dy
                if in_bound(x, y):
                    f = Or(f, mine_flags[x][y])
            s.add(
                Implies(
                    mine_flags[i][j],
                    f
                )
            )


special_rule()

if s.check() == sat:
    m = s.model()
    for i in range(N):
        row_s = 0
        for j in range(M):
            if is_true(m[mine_flags[i][j]]):
                row_s += 1
                print('x', end=' ')
            elif (i, j) in MINE_NUMBERS:
                print(m[mine_counters[i][j]], end=' ')
            else:
                print('.', end=' ')
        print(f'| mines: {row_s}')
else:
    print('no solution')
