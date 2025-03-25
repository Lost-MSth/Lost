from z3 import *

N = 8
M = 8

# 普通扫雷

MINE_AMOUNT = 24
MINE_NUMBERS = {
    (0, 0): 2, (0, 3): 2, (0, 4): 1, (0, 7): 3,
    (1, 1): 5,
    (2, 2): 4,
    (3, 1): 5, (3, 3): 3, (3, 4): 3,
    (4, 3): 2, (4, 4): 2, (4, 6): 2,
    (5, 0): 2, (5, 2): 4, (5, 5): 4,
    (6, 6): 5,
    (7, 0): 2, (7, 3): 1, (7, 4): 2, (7, 7): 2,
}
NOT_MINES = [(2, 5), (2, 7)]

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
