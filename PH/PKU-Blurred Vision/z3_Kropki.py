from z3 import *

NUM = 6

x = [IntVector('x_%d' % i, NUM) for i in range(NUM)]
s = Solver()

for i in range(NUM):
    for j in range(NUM):
        s.add(x[i][j] >= 1, x[i][j] <= NUM)

# rows
for i in range(NUM):
    s.add(Distinct(x[i]))

# columns
for j in range(NUM):
    s.add(Distinct([x[i][j] for i in range(NUM)]))


def is_white(a, b):
    return Or(a - b == 1, b - a == 1)


def is_black(a, b):
    return Or(a * 2 == b, b * 2 == a)


black_constraints = [
    ((0, 0), (0, 1)),
    ((0, 3), (0, 4)),
    ((0, 4), (0, 5)),
    ((1, 2), (1, 3)),
    ((1, 3), (1, 4)),
    ((0, 3), (1, 3)),
]


def is_in_black_constraints(a, b):
    for (c, d) in black_constraints:
        if (a == c and b == d) or (a == d and b == c) or (a == (c[1], c[0]) and b == (d[1], d[0])) or (a == (d[1], d[0]) and b == (c[1], c[0])):
            return True
    return False


for (a, b) in black_constraints:
    s.add(is_black(x[a[0]][a[1]], x[b[0]][b[1]]))
    # 对称
    s.add(is_black(x[a[1]][a[0]], x[b[1]][b[0]]))

for i in range(NUM):
    s.add(Sum([And(Not(is_in_black_constraints((i, j), (i, j+1))),
          is_white(x[i][j], x[i][j+1])) for j in range(NUM-1)]) == 2)

for j in range(NUM):
    s.add(Sum([And(Not(is_in_black_constraints((i, j), (i+1, j))),
          is_white(x[i][j], x[i+1][j])) for i in range(NUM-1)]) == 2)


assert s.check() == sat
m = s.model()

for i in range(NUM):
    print([m[x[i][j]].as_long() for j in range(NUM)])
