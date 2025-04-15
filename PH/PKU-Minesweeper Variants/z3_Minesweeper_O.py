from z3 import *

N = 8
M = 8

# 扫雷，特殊规则：所有非雷区域四方向连通，所有雷格四方向连通到外部。

MINE_AMOUNT = 24
MINE_NUMBERS = {
    (0, 0): 2, (0, 7): 1,
    (1, 3): 3, (1, 6): 2,
    (2, 1): 5, (2, 4): 3, (2, 6): 3,
    (3, 2): 2, (3, 5): 3,
    (4, 0): 3, (4, 3): 2, (4, 6): 5,
    (5, 2): 3, (5, 4): 4,
    (6, 1): 2, (6, 5): 4,
    (7, 0): 1, (7, 7): 2,
}
NOT_MINES = []


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

    connectivity = {
        ((x1, y1), (x2, y2)): Int(f"conn_({x1},{y1})->({x2}_{y2})")
        for x1 in range(N+2)
        for y1 in range(M+2)
        for x2 in range(N+2)
        for y2 in range(M+2)
        if (y2 > y1 or (y2 == y1 and x2 > x1))
    }

    def get_conn_index(c1, c2):
        if c2[1] > c1[1] or (c2[1] == c1[1] and c2[0] > c1[0]):
            return (c1, c2)
        return (c2, c1)

    def is_boundary(c):
        return c[0] == 0 or c[0] == N+1 or c[1] == 0 or c[1] == M+1

    def in_bound_special(c):
        return c[0] >= 0 and c[0] < N+2 and c[1] >= 0 and c[1] < M+2

    def is_mine_or_boundary(c):
        if is_boundary(c):
            return True
        return mine_flags[c[0]-1][c[1]-1]

    def not_mine(c):
        if is_boundary(c):
            return False
        return Not(mine_flags[c[0]-1][c[1]-1])

    for (c1, c2), conn in connectivity.items():

        both_mine_or_boundary = And(
            is_mine_or_boundary(c1), is_mine_or_boundary(c2))
        both_ok = And(not_mine(c1), not_mine(c2))
        one_ok_one_not = Or(
            And(is_mine_or_boundary(c1), not_mine(c2)),
            And(not_mine(c1), is_mine_or_boundary(c2))
        )

        s.add((one_ok_one_not) == (conn == -1))

        distance = abs(c2[0] - c1[0]) + abs(c2[1] - c1[1])
        assert distance > 0

        if distance == 1:
            s.add(Or(both_mine_or_boundary, both_ok) == (conn == 1))
        elif distance > 1:
            s.add(Or(both_mine_or_boundary, both_ok) == (conn > 1))
            neighbors = []
            for dx, dy in FOUR_DIRS:
                x, y = c2[0] + dx, c2[1] + dy
                if in_bound_special((x, y)):
                    neighbors.append(
                        connectivity[get_conn_index(c1, (x, y))])
            assert len(neighbors) >= 2
            s.add(
                Implies(conn > 1, Or([x == conn - 1 for x in neighbors]))
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
