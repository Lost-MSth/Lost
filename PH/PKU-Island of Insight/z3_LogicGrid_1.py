# https://mp.weixin.qq.com/s/QX9RnIrDn_z7ov1iHc2lug

import grilops
import grilops.regions
from grilops import Point
from z3 import *


WIDTH = 8
HEIGHT = 8

WHITES = {
    Point(0, 3): 4,
    Point(0, 6): 5,
    Point(2, 1): 3,
    Point(2, 4): 4,
    Point(3, 7): 2,
    Point(4, 5): 2,
    Point(6, 2): 8,
    Point(6, 7): 6,
}

BLACKS = {
    Point(1, 0): 6,
    Point(1, 5): 3,
    Point(3, 2): 2,
    Point(4, 0): 5,
    Point(5, 3): 4,
    Point(5, 6): 5,
    Point(7, 1): 5,
    Point(7, 4): 3,
}


def print_grid():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = Point(y, x)
            if p in WHITES:
                print(f"W{WHITES[p]:1d}", end=' ')
            elif p in BLACKS:
                print(f"B{BLACKS[p]:1d}", end=' ')
            else:
                print(" .", end=' ')
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
    sg = grilops.SymbolGrid(la, sym)
    rc = grilops.regions.RegionConstrainer(
        la,
        solver=sg.solver,
    )

    for p, v in WHITES.items():
        sg.solver.add(
            sg.cell_is(p, sym.W),
            rc.region_size_grid[p] == v,
        )

    for p, v in BLACKS.items():
        sg.solver.add(
            sg.cell_is(p, sym.B),
            rc.region_size_grid[p] == v,
        )

    # 颜色相同连一起是一个区，不同则不是
    for p in la.points:
        p1 = p
        for n in sg.edge_sharing_neighbors(p):
            p2 = n.location
            sg.solver.add(
                (rc.region_id_grid[p1] == rc.region_id_grid[p2]) ==
                Or(
                    And(sg.cell_is(p1, sym.W), sg.cell_is(p2, sym.W)),
                    And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B))
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
