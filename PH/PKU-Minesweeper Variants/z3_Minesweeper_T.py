from z3 import *

N = 8
M = 8

# 扫雷，特殊规则：无三连，横向、纵向和斜向都不能有三个连在一起的雷

MINE_AMOUNT = 24
MINE_NUMBERS = {
    (0, 5): 3, (0, 7): 2,
    (1, 0): 2, (1, 2): 4, (1, 4): 4,
    (3, 3): 3, (3, 4): 2, (3, 6): 4,
    (4, 1): 5, (4, 3): 2, (4, 4): 3,
    (6, 3): 3, (6, 5): 4, (6, 7): 1,
    (7, 2): 1,
}
NOT_MINES = [(7, 0)]


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
    # 禁止横向
    for i in range(N):
        for j in range(M - 2):
            s.add(
                Not(And(mine_flags[i][j], mine_flags[i][j + 1], mine_flags[i][j + 2])))

    # 禁止纵向
    for i in range(N - 2):
        for j in range(M):
            s.add(
                Not(And(mine_flags[i][j], mine_flags[i + 1][j], mine_flags[i + 2][j])))

    # 禁止正对角
    for i in range(N - 2):
        for j in range(M - 2):
            s.add(
                Not(And(mine_flags[i][j], mine_flags[i + 1][j + 1], mine_flags[i + 2][j + 2])))

    # 禁止反对角
    for i in range(2, N):
        for j in range(M - 2):
            s.add(
                Not(And(mine_flags[i][j], mine_flags[i - 1][j + 1], mine_flags[i - 2][j + 2])))


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
