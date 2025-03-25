from z3 import *

N = 8
M = 8

# 扫雷，特殊规则：无方，任意 2*2 区域内必须有一个雷

MINE_AMOUNT = 23
MINE_NUMBERS = {
    (0, 0): 2, (0, 2): 2, (0, 4): 2, (0, 6): 2,
    (1, 5): 3,
    (2, 1): 3, (2, 3): 3, (2, 5): 3,
    (3, 5): 3,
    (4, 0): 3, (4, 2): 3,
    (5, 2): 3, (5, 4): 6, (5, 6): 3,
    (6, 2): 3,
    (7, 1): 3, (7, 3): 3, (7, 5): 3,
}
NOT_MINES = [(3, 7), (7, 7)]


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
    FOUR_DIRS = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for i in range(N - 1):
        for j in range(M - 1):
            mines = 0
            for dx, dy in FOUR_DIRS:
                mines += If(mine_flags[i + dx][j + dy], 1, 0)
            s.add(mines >= 1)


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
