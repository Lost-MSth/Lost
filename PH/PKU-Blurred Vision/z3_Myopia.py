import time

from z3 import *

NUM = 8
LEN = 70
# LEN = 70 is ok in 600s
# LEN = 66 is ok in 507s

# LEN = 68 unsat in 464s
# LEN = 64 unsat in 437s
# LEN = 62 unsat in 668s
# LEN = 60 unsat in 231s
# LEN = 58 unsat in 560s
# LEN = 56 unsat in 357s
# LEN = 54 unsat in 243s
# LEN = 52 unsat in 137s
# LEN = 50 unsat in 98s

# LEN = 72 unsat in 721s
# LEN = 74 unsat in 761s
# LEN = 76 unsat in 1031s
# LEN = 78 unsat in 742s
# LEN = 80 unsat in 979s
# LEN = 82 unsat in 855s
# LEN = 84 unsat in 1255s
# LEN = 86 unsat in 1691s
# LEN = 88 unsat in 1647s
# LEN = 90 unsat in 1817s
# LEN = 92 unsat in 3862s
# LEN = 94 unsat in 3776s
# LEN = 96 unsat in 5000s
# LEN = 98 unsat in 6770s
# LEN = 100 unsat in 4575s
# LEN = 102 unsat in 6285s


VEC_NUM = NUM + 1

rows = [BoolVector('row_%d' % i, NUM) for i in range(NUM+1)]
cols = [BoolVector('col_%d' % i, NUM+1) for i in range(NUM)]


vecs = IntVector('vec', LEN)


def vec2xy(v):
    return v / VEC_NUM, v % VEC_NUM


def xy2vec(x, y):
    return x * VEC_NUM + y


def is_edge_in_vecs(x0, y0, x1, y1):
    v0 = xy2vec(x0, y0)
    v1 = xy2vec(x1, y1)

    # s = 0
    # for i in range(LEN-1):
    #     s += If(And(vecs[i] == v0, vecs[i+1] == v1), 1, 0)
    #     s += If(And(vecs[i] == v1, vecs[i+1] == v0), 1, 0)
    #     # s += If(Or(And(vecs[i] == v0, vecs[i+1] == v1), And(vecs[i] == v1, vecs[i+1] == v0)), 1, 0)

    # s += If(And(vecs[LEN-1] == v0, vecs[0] == v1), 1, 0)
    # s += If(And(vecs[LEN-1] == v1, vecs[0] == v0), 1, 0)
    # s += If(Or(And(vecs[LEN-1] == v0, vecs[0] == v1), And(vecs[LEN-1] == v1, vecs[0] == v0)), 1, 0)
    s = []
    for i in range(LEN-1):
        s.append(And(vecs[i] == v0, vecs[i+1] == v1))
        s.append(And(vecs[i] == v1, vecs[i+1] == v0))
    s.append(And(vecs[LEN-1] == v0, vecs[0] == v1))
    s.append(And(vecs[LEN-1] == v1, vecs[0] == v0))
    # return s == 1
    return Or(s)


s = Solver()

s.add(Distinct(vecs))


for i in vecs:
    s.add(And(i >= 0, i < VEC_NUM*VEC_NUM))

# path connected
for i in range(LEN-1):
    x0, y0 = vec2xy(vecs[i])
    x1, y1 = vec2xy(vecs[i+1])
    # s.add(Abs(x0 - x1) + Abs(y0 - y1) == 1)
    s.add(Or(
        And(x0 == x1, Or(y0 == y1 + 1, y0 == y1 - 1)),
        And(y0 == y1, Or(x0 == x1 + 1, x0 == x1 - 1))
    ))


x0, y0 = vec2xy(vecs[LEN-1])
x1, y1 = vec2xy(vecs[0])
# s.add(Abs(x0 - x1) + Abs(y0 - y1) == 1)
s.add(Or(
    And(x0 == x1, Or(y0 == y1 + 1, y0 == y1 - 1)),
    And(y0 == y1, Or(x0 == x1 + 1, x0 == x1 - 1))
))

s.add(vecs[0] == 0)
s.add(vecs[1] == 1)
# add some fixed points by human's eyes
s.add(vecs[2] == 10)
s.add(vecs[3] == 11)
s.add(vecs[4] == 2)
s.add(vecs[5] == 3)
s.add(vecs[LEN-1] == 9)
s.add(vecs[LEN-2] == 18)

# link vecs with rows and cols
for i in range(NUM+1):
    for j in range(NUM):
        s.add(
            If(
                is_edge_in_vecs(i, j, i, j+1),
                rows[i][j],
                Not(rows[i][j])
            )
        )

for i in range(NUM):
    for j in range(NUM+1):
        s.add(
            If(
                is_edge_in_vecs(i, j, i+1, j),
                cols[i][j],
                Not(cols[i][j])
            )
        )


XY = [
    (0, 0), (0, 1), (0, 5),
    (1, 3), (1, 7),
    (2, 2), (2, 6),
    (3, 0), (3, 1), (3, 3),
    (4, 6),
    (5, 0), (5, 2), (5, 5),
    (6, 6),
    (7, 0), (7, 7)
]

xy_vec = IntVector('xy_vec', len(XY))

for x in xy_vec:
    s.add(Or(x == 0, x == 1, x == 2, x == 3))

for i in range(NUM):
    t = []
    t2 = []
    for j, (x, y) in enumerate(XY):
        if x == i:
            t.append(xy_vec[j])
        if y == i:
            t2.append(xy_vec[j])

    if len(t) >= 2:
        s.add(Distinct(t))
    if len(t2) >= 2:
        s.add(Distinct(t2))


def is_three_edges(sv, sm):
    return Or(
        And(sv[0] == 3, Not(sm[0])),
        And(sv[0] == 0, sv[1] == 3, Not(sm[0]), Not(sm[1])),
        And(sv[0] == 0, sv[1] == 0, sv[2] == 3,
            Not(sm[0]), Not(sm[1]), Not(sm[2])),
        And(sv[0] == 3, sv[1] == 0, sv[2] == 0, sv[3] == 3,
            Not(sm[0]), Not(sm[1]), Not(sm[2]), Not(sm[3])),
    )


def is_type_v_three_edges(x, y, v):
    s = [[0 for _ in range(4)] for _ in range(4)]
    # index 1 is type v (up down left right 4 types), index 2 is depth from 0 to 3
    sm = [[False for _ in range(4)] for _ in range(4)]

    for n in range(4):
        if x + n + 1 < NUM + 1:
            t = rows[x+n+1][y]
            s[1][n] += t
            s[2][n] += t
            s[3][n] += t
            sm[0][n] = t
        if x - n >= 0:
            t = rows[x-n][y]
            s[0][n] += t
            s[2][n] += t
            s[3][n] += t
            sm[1][n] = t
        if y + n + 1 < NUM + 1:
            t = cols[x][y+n+1]
            s[0][n] += t
            s[1][n] += t
            s[3][n] += t
            sm[2][n] = t
        if y - n >= 0:
            t = cols[x][y-n]
            s[0][n] += t
            s[1][n] += t
            s[2][n] += t
            sm[3][n] = t

    return Or(
        If(v == 0, is_three_edges(s[0], sm[0]), False),
        If(v == 1, is_three_edges(s[1], sm[1]), False),
        If(v == 2, is_three_edges(s[2], sm[2]), False),
        If(v == 3, is_three_edges(s[3], sm[3]), False),
    )


for i, (x, y) in enumerate(XY):
    s.add(is_type_v_three_edges(x, y, xy_vec[i]))


s.add(rows[0][0] == True)
s.add(cols[0][0] == True)
s.add(cols[1][0] == True)

s.add(rows[8][0] == True)
s.add(cols[7][0] == True)
s.add(rows[8][7] == True)
s.add(cols[7][8] == True)

# special
# s.add(cols[1][7] == True)
# s.add(cols[1][8] == True)
# s.add(rows[1][7] == True)
# s.add(rows[2][7] == False)

# s.add(rows[5][0] == False)
# s.add(rows[6][0] == False)
# s.add(cols[5][0] == False)
# s.add(cols[5][1] == False)


start = time.time()
res = s.check()
print(f'elapsed time: {time.time() - start}')

assert res == sat
m = s.model()

print(','.join(str(m[vecs[i]]) for i in range(LEN)))


def arrow_str(v):
    if v == 0:
        return '↓'
    elif v == 1:
        return '↑'
    elif v == 2:
        return '→'
    else:
        return '←'


for i in range(NUM):
    print(' ', end='')
    print(' '.join('-' if is_true(m[rows[i][j]]) else '.' for j in range(NUM)))
    for j in range(NUM+1):
        print('|' if is_true(m[cols[i][j]]) else '.', end='')
        print(arrow_str(m[xy_vec[XY.index((i, j))]])
              if (i, j) in XY else ' ', end='')
    print()

    # print(' '.join('|' if is_true(m[cols[i][j]])
    #       else '.' for j in range(NUM+1)))
    # print(' '.join('-' if m.eval(rows[i][j]) else '.' for j in range(NUM)))
    # print(' '.join('|' if m.eval(cols[i][j]) else '.' for j in range(NUM+1))
    #   )

print(' ', end='')
print(' '.join('-' if m.eval(rows[NUM][j]) else '.' for j in range(NUM)))
