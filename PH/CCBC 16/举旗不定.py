from z3 import *

N = 9
M = 9

# 普通扫雷 For CCBC 16


CLUES = [
    [1, 1, -1, 0, -1, 1, 2, -1, 1],
    [-1, -1, -1, 1, -1, 2, -1, -1, 1],
    [1, -1, 1, -1, -1, -1, -1, -1, 1],
    [-1, -1, -1, -1, 1, -1, 2, -1, 2],
    [-1, -1, -1, 4, -1, 3, -1, 3, -1],
    [3, 6, -1, -1, -1, -1, -1, -1, 3],
    [-1, -1, -1, -1, 4, -1, 3, -1, -1],
    [1, -1, 4, -1, -1, -1, -1, 2, -1],
    [-1, -1, 1, -1, 1, 0, -1, -1, 0],
]

MINE_NUMBERS = {}

for i in range(N):
    for j in range(M):
        if CLUES[i][j] != -1:
            MINE_NUMBERS[(i, j)] = CLUES[i][j]


def is_unique(solver, lists) -> bool:
    model = solver.model()
    or_terms = []
    for row in lists:
        for cell in row:
            or_terms.append(cell != model.eval(cell).as_long())
    solver.add(Or(*or_terms))
    result = solver.check()
    return result == unsat


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


def print_grid():
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
        print()


if s.check() == sat:
    m = s.model()
    print_grid()
    print()

    while not is_unique(s, mine_counters):
        m = s.model()
        print_grid()
        print()

else:
    print('no solution')
