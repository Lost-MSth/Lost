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


def Equals(*xs):
    constr = True
    if xs:
        base = xs[0]
        for x in xs[1:]:
            constr = And(constr, base == x)
    return constr


# constraints

index = [BoolVector('index_%d' % i, NUM) for i in range(8)]
index_diag = BoolVector('index_diag', NUM - 1)


def bigger_than(x, ys: list):
    return And([x > y for y in ys])


def get_col(col_id, index_id):
    s = 0
    f = True
    for i in range(NUM):
        s += If(index[index_id][i], x[i][col_id], 0)
        f = And(f, Not(Xor(
            index[index_id][i],
            bigger_than(x[i][col_id], [x[j][col_id] for j in range(i)])
        )))

    return s, f


def get_row(row_id, index_id):
    s = 0
    f = True
    for j in range(NUM):
        s += If(index[index_id][j], x[row_id][j], 0)
        f = And(f, Not(Xor(
            index[index_id][j],
            bigger_than(x[row_id][j], [x[row_id][k] for k in range(j)])
        )))
    return s, f


def get_col_inv(col_id, index_id):
    s = 0
    f = True
    for i in range(NUM):
        s += If(index[index_id][i], x[i][col_id], 0)
        f = And(f, Not(Xor(
            index[index_id][i],
            bigger_than(x[i][col_id], [x[j][col_id] for j in range(i+1, NUM)])
        )))

    return s, f


def get_diag():
    s = 0
    f = True
    for i in range(NUM - 1):
        s += If(index_diag[i], x[i + 1][NUM - i - 1], 0)
        f = And(f, Not(Xor(
            index_diag[i],
            bigger_than(x[i + 1][NUM - i - 1], [x[j + 1][NUM - j - 1]
                        for j in range(i)])
        )))
    return s, f


sums = []

su, f = get_diag()
sums.append(su)
s.add(f)

for index_id, i in [(0, 0), (1, 1), (2, 3)]:
    su, f = get_col(i, index_id)
    sums.append(su)
    s.add(f)

for index_id, i in [(3, 1), (4, 3)]:
    su, f = get_row(i, index_id)
    sums.append(su)
    s.add(f)

for index_id, i in [(5, 2), (6, 4), (7, 5)]:
    su, f = get_col_inv(i, index_id)
    sums.append(su)
    s.add(f)


s.add(Equals(*sums))


assert s.check() == sat
m = s.model()

for i in range(NUM):
    print([m[x[i][j]].as_long() for j in range(NUM)])

for i in range(8):
    print([m[index[i][j]] for j in range(NUM)])

print([m[index_diag[i]] for i in range(NUM - 1)])
