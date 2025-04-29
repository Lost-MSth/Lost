from z3 import *

N = 8
M = 8

# 扫雷，特殊规则：蛇，所有雷组成一条蛇形，身体不能和自身接触

MINE_AMOUNT = 25
MINE_NUMBERS = {
    (1, 1): 5, (1, 5): 2,
    (2, 2): 3, (2, 6): 2,
    (3, 3): 3,
    (4, 4): 3,
    (5, 5): 3, (5, 1): 3,
    (6, 6): 4, (6, 2): 4,
}
NOT_MINES = [(0, 7), (7, 0)]


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

    # 在四连通的基础下，增加头尾部的限制，增加中部周围必须有两个相邻的限制

    FOUR_DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    is_margin = [BoolVector('snake_margin_flag_%d' % i, M) for i in range(N)]
    connectivity = {
        ((x1, y1), (x2, y2)): Int(f"conn_({x1},{y1})->({x2}_{y2})")
        for x1 in range(N)
        for y1 in range(M)
        for x2 in range(N)
        for y2 in range(M)
        if (y2 > y1 or (y2 == y1 and x2 > x1))
    }

    def get_conn_index(c1, c2):
        if c2[1] > c1[1] or (c2[1] == c1[1] and c2[0] > c1[0]):
            return (c1, c2)
        return (c2, c1)

    for (c1, c2), conn in connectivity.items():

        c1_c2_both = And(mine_flags[c1[0]][c1[1]], mine_flags[c2[0]][c2[1]])
        s.add(Not(c1_c2_both) == (conn == -1))

        if abs(c2[0] - c1[0]) <= 1 and abs(c2[1] - c1[1]) <= 1:
            s.add((c1_c2_both) == (conn == 1))
        else:
            s.add((c1_c2_both) == (conn > 1))
            neighbors = []
            for dx, dy in FOUR_DIRS:
                x, y = c2[0] + dx, c2[1] + dy
                if in_bound(x, y):
                    neighbors.append(
                        connectivity[get_conn_index(c1, (x, y))])
            s.add(
                Implies(conn > 1, Or([x == conn - 1 for x in neighbors]))
            )

    margin_sum = 0
    for i in range(N):
        for j in range(M):
            margin_sum += If(is_margin[i][j], 1, 0)
            s.add(Implies(is_margin[i][j], mine_flags[i][j]))

            nn_mines = 0
            for dx, dy in FOUR_DIRS:
                x, y = i + dx, j + dy
                if in_bound(x, y):
                    nn_mines += If(mine_flags[x][y], 1, 0)
            s.add(Implies(is_margin[i][j], nn_mines == 1))
            s.add(Implies(
                And(Not(is_margin[i][j]), mine_flags[i][j]),
                nn_mines == 2
            ))

    s.add(margin_sum == 2)


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
