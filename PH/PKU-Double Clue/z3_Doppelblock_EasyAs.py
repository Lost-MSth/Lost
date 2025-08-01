# https://mp.weixin.qq.com/s/necH45U4Rw3Ov5uDCXDE5w


import grilops
import grilops.sightlines
from grilops.geometry import Point
from z3 import *

LEN = 6

BLANKS = [
    Point(1, 4), Point(5, 5)
]

N_CLUES = [2, 1, 0, None, 3, None]
W_CLUES = [0, None, None, 2, 3, None]


def main():
    sym = grilops.make_number_range_symbol_set(0, LEN-3)
    sym.append('B', 'x')
    lattice = grilops.get_square_lattice(LEN)
    DIRECTIONS = {d.name: d for d in lattice.edge_sharing_directions()}
    sg = grilops.SymbolGrid(lattice, sym)

    # 每行每列只能用一次数字，每个数字都必须出现
    for y in range(LEN):
        for i in range(LEN-2):
            sg.solver.add(
                PbEq(
                    [(sg.cell_is(Point(y, x), i), 1) for x in range(LEN)],
                    1
                ),
                # x=y, y=x
                PbEq(
                    [(sg.cell_is(Point(x, y), i), 1) for x in range(LEN)],
                    1
                )
            )

    # Doppelblock 每行每列两个空格
    for y in range(LEN):
        sg.solver.add(
            PbEq(
                [(sg.cell_is(Point(y, x), sym.B), 1) for x in range(LEN)],
                2
            ),
            # y=x, x=y
            PbEq(
                [(sg.cell_is(Point(x, y), sym.B), 1) for x in range(LEN)],
                2
            ),
        )

    Acc = Datatype('Acc')
    Acc.declare('acc', ('flag', BoolSort()), ('sum', IntSort()))
    Acc = Acc.create()
    # flag 判断是否在空格之间，遇到空格就取反

    def accumulate(a, c):
        return Acc.acc(
            If(c == sym.B, Not(Acc.flag(a)), Acc.flag(a)),
            Acc.sum(a) + If(c == sym.B, 0, If(
                Acc.flag(a), c, 0
            ))
        )

    # Doppelblock 约束
    for y in range(LEN):
        if W_CLUES[y] is None:
            continue
        sg.solver.add(
            Acc.sum(grilops.sightlines.reduce_cells(
                sg, Point(y, 0), DIRECTIONS['E'],
                Acc.acc(False, 0),
                accumulate
            )) == W_CLUES[y]
        )
    for x in range(LEN):
        if N_CLUES[x] is None:
            continue
        sg.solver.add(
            Acc.sum(grilops.sightlines.reduce_cells(
                sg, Point(0, x), DIRECTIONS['S'],
                Acc.acc(False, 0),
                accumulate
            )) == N_CLUES[x]
        )

    # BLANKS 必须是空格
    for p in BLANKS:
        sg.solver.add(sg.cell_is(p, sym.B))

    Acc2 = Datatype('Acc2')
    Acc2.declare('acc', ('flag', BoolSort()), ('num', IntSort()))
    Acc2 = Acc2.create()
    # flag 表示还没找到数字

    def get_first_num(a, c):
        return Acc2.acc(
            If(Acc2.flag(a), If(c == sym.B, True, False), False),
            If(Acc2.flag(a), If(c != sym.B, c, 0), Acc2.num(a))
        )

    # Easy As 规则
    for y in range(LEN):
        if W_CLUES[y] is None:
            continue
        sg.solver.add(
            Acc2.num(grilops.sightlines.reduce_cells(
                sg, Point(y, 0), DIRECTIONS['E'],
                Acc2.acc(True, 0),
                get_first_num
            )) == W_CLUES[y]
        )

    for x in range(LEN):
        if N_CLUES[x] is None:
            continue
        sg.solver.add(
            Acc2.num(grilops.sightlines.reduce_cells(
                sg, Point(0, x), DIRECTIONS['S'],
                Acc2.acc(True, 0),
                get_first_num
            )) == N_CLUES[x]
        )

    if sg.solve():
        sg.print()
        print()
        if sg.is_unique():
            print("Unique solution")
        else:
            print("Alternate solution")
            sg.print()
    else:
        print("No solution")


if __name__ == "__main__":
    main()
