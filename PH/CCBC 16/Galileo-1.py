from z3 import *

x = IntVector('x', 9)

s = Solver()

s.add(Distinct(x))

for i in range(9):
    s.add(x[i] >= 1, x[i] <= 9)

s.add([
    x[0] * 10 + x[1] - x[2] * 10 - x[3] == x[4] * 10 + x[5],
    (x[0] * 10 + x[1]) * (x[2] * 10 + x[3]) == x[6] * 100 + x[7] * 10 + x[8]
])

s.check()
m = s.model()
for i in range(9):
    print(m[x[i]])
