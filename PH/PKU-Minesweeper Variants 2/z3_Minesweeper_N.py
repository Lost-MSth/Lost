from z3 import *

N = 8
M = 8

# N 负雷：线索提示相邻染色与非染色的雷数之差。

MINE_AMOUNT = 25
MINE_NUMBERS = {
    (0, 5): 0, (0, 7): 0,
    (1, 0): 2, (1, 1): 2, (1, 3): 3,
    (2, 5): 2, (2, 7): 1,
    (3, 0): 1, (3, 2): 1, (3, 4): 1,
    (4, 3): 0, (4, 6): 0,
    (5, 1): 0, (5, 4): 2,
    (6, 2): 1, (6, 6): 3,
    (7, 0): 0, (7, 4): 0, (7, 6): 1,
}
NOT_MINES = []

# print the puzzle
for i in range(N):
    for j in range(M):
        if (i, j) in MINE_NUMBERS:
            print(MINE_NUMBERS[(i, j)], end=' ')
        else:
            print('.', end=' ')
    print()
print()

mine_flags = [BoolVector('mine_flag_%d' % i, M) for i in range(N)]
mine_counters = [IntVector('mine_counter_%d' % i, M) for i in range(N)]

s = Solver()

# EIGHT_DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0),
#               (1, 1), (1, -1), (-1, 1), (-1, -1)]
FOUR_DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
FOUR_DIAG_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]


def in_bound(x, y):
    return x >= 0 and x < N and y >= 0 and y < M


mine_counter = 0
for i in range(N):
    for j in range(M):
        # s.add(mine_counters[i][j] >= 0, mine_counters[i][j] <= 8)
        s.add(mine_counters[i][j] >= -4, mine_counters[i][j] <= 4)

        counter = 0
        for dx, dy in FOUR_DIRS:
            x, y = i + dx, j + dy
            if in_bound(x, y):
                counter += If(mine_flags[x][y], 1, 0)
        for dx, dy in FOUR_DIAG_DIRS:
            x, y = i + dx, j + dy
            if in_bound(x, y):
                counter += If(mine_flags[x][y], -1, 0)
        s.add(mine_counters[i][j] == counter)

        mine_counter += If(mine_flags[i][j], 1, 0)

        if (i, j) in MINE_NUMBERS:
            # s.add(mine_counters[i][j] == MINE_NUMBERS[(i, j)])
            s.add(Or(mine_counters[i][j] == MINE_NUMBERS[(i, j)],
                     mine_counters[i][j] == -MINE_NUMBERS[(i, j)]))
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
                x = m[mine_counters[i][j]]
                print(abs(x.as_long()), end=' ')
            else:
                print('.', end=' ')
        print(f'| mines: {row_s}')
else:
    print('no solution')
