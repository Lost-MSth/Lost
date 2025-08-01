# https://mp.weixin.qq.com/s/NazJFvsI5YMgL7vURzRD-A

import grilops
import grilops.regions
import grilops.sightlines
from grilops import Point
from z3 import *

WIDTH = 8
HEIGHT = 8

CLUES = {
    Point(0, 0): ('E', 1),
    Point(0, 3): ('W', 1),
    Point(0, 4): ('S', 1),
    Point(0, 5): ('S', 1),
    Point(0, 6): ('E', 0),
    Point(1, 1): ('E', 2),
    Point(1, 2): ('E', 2),
    Point(2, 1): ('E', 2),
    Point(2, 2): ('E', 2),
    Point(4, 0): ('E', 1),
    Point(4, 3): ('E', 1),
    Point(4, 6): ('E', 1),
    Point(5, 6): ('E', 1),
    Point(5, 1): ('N', 2),
    Point(5, 2): ('N', 2),
    Point(6, 1): ('N', 2),
    Point(6, 2): ('N', 2),
    Point(7, 3): ('W', 1),
    Point(7, 4): ('N', 1),
    Point(7, 5): ('N', 1),
    Point(7, 6): ('E', 0),
}


def print_grid():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = Point(y, x)
            if p in CLUES:
                direction, count = CLUES[p]
                print(f"{direction}{count:1d}", end=' ')
            else:
                print(". ", end=' ')
        print()


def print_black_row_nums(sg: grilops.SymbolGrid):
    m = sg.solver.model()
    for y in range(HEIGHT):
        s = 0
        for x in range(WIDTH):
            p = Point(y, x)
            s += m.eval(sg.grid[p]).as_long() == 0
        print(s, end=' ')
    print()


def main():
    print_grid()
    sym = grilops.SymbolSet([('B', 'x'), ('W', '.')])
    la = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
    DIRECTIONS = {d.name: d for d in la.edge_sharing_directions()}
    sg = grilops.SymbolGrid(la, sym)
    rc = grilops.regions.RegionConstrainer(
        la,
        solver=sg.solver,
    )

    # Hitori 规则：同行和列不能有相同的数字（带符号）
    for y in range(HEIGHT):
        d = {}
        for x in range(WIDTH):
            p = Point(y, x)
            if p in CLUES:
                if CLUES[p] not in d:
                    d[CLUES[p]] = []
                d[CLUES[p]].append(p)

        for l in d.values():
            if len(l) < 2:
                continue
            sg.solver.add(
                Sum(
                    [If(sg.cell_is(p, sym.W), 1, 0) for p in l]
                ) <= 1
            )

    for x in range(WIDTH):
        d = {}
        for y in range(HEIGHT):
            p = Point(y, x)
            if p in CLUES:
                if CLUES[p] not in d:
                    d[CLUES[p]] = []
                d[CLUES[p]].append(p)

        for l in d.values():
            if len(l) < 2:
                continue
            sg.solver.add(
                Sum(
                    [If(sg.cell_is(p, sym.W), 1, 0) for p in l]
                ) <= 1
            )

    # Yajisan-Kazusan 规则：白色线索格子代表此方向黑色格子数量
    for p, c in CLUES.items():
        sg.solver.add(
            Implies(
                sg.cell_is(p, sym.W),
                grilops.sightlines.count_cells(
                    sg, p, DIRECTIONS[c[0]],
                    lambda c: c == sym.B,
                ) == c[1]
            )
        )

    # 白色连一起是一个区，黑色不连接
    for p in la.points:
        p1 = p
        for n in sg.edge_sharing_neighbors(p):
            p2 = n.location
            sg.solver.add(
                (rc.region_id_grid[p1] == rc.region_id_grid[p2]) ==
                And(sg.cell_is(p1, sym.W), sg.cell_is(p2, sym.W)),
                # 黑色不连接
                Not(And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B)))
            )

    # 白色只有一个区域
    white_root = Int('white_root')
    sg.solver.add(white_root >= 0, white_root <= HEIGHT * WIDTH - 1)
    for p in la.points:
        sg.solver.add(
            Implies(
                sg.cell_is(p, sym.W),
                rc.region_id_grid[p] == white_root
            )
        )

    if sg.solve():
        sg.print()
        print_black_row_nums(sg)
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
