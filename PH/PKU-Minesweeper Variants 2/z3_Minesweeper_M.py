from z3 import *

N = 8
M = 8

# M 多雷：奇数位格子中的雷视为两个雷

MINE_AMOUNT = 24
MINE_NUMBERS = {
    (0, 0): 3, (0, 7): 2,
    (1, 2): 7, (1, 3): 6, (1, 5): 5,
    (2, 1): 4, (2, 4): 7, (2, 6): 5,
    (3, 2): 6, (3, 6): 6,
    (4, 1): 5, (4, 5): 4,
    (5, 1): 4, (5, 3): 7, (5, 6): 4,
    (6, 2): 4, (6, 4): 6, (6, 5): 7,
    (7, 0): 2, (7, 7): 2,
}
NOT_MINES = []

DOUBLE_MINES = [(i, j) for i in range(N) for j in range(M) if (i + j) % 2 == 1]

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
        s.add(mine_counters[i][j] >= 0, mine_counters[i][j] <= 8*2)

        counter = 0
        for dx, dy in EIGHT_DIRS:
            x, y = i + dx, j + dy
            if in_bound(x, y):
                v = 2 if (x, y) in DOUBLE_MINES else 1
                counter += If(mine_flags[x][y], v, 0)
        s.add(mine_counters[i][j] == counter)

        mine_counter += If(mine_flags[i][j], 1, 0)

        if (i, j) in MINE_NUMBERS:
            s.add(mine_counters[i][j] == MINE_NUMBERS[(i, j)])
            s.add(mine_flags[i][j] == False)  # has number, so not mine

s.add(mine_counter == MINE_AMOUNT)

for x, y in NOT_MINES:
    s.add(mine_flags[x][y] == False)

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
