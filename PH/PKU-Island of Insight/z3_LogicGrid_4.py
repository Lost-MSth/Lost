# https://mp.weixin.qq.com/s/iXgADE1idGZGvguwnaD7IQ

import grilops
import grilops.regions
from grilops import Point
from z3 import *

WIDTH = 10
HEIGHT = 10

WHITES = {
    Point(0, 0): 1, Point(0, 4): 4,
    Point(1, 1): 3, Point(1, 8): 5,
    Point(2, 2): None,
    Point(3, 3): None,
    Point(4, 4): None, Point(4, 0): 2,
    Point(5, 5): None, Point(5, 9): 6,
    Point(6, 6): None,
    Point(7, 7): None,
    Point(8, 8): None, Point(8, 1): 5,
    Point(9, 5): 7,
}

BLACKS = {
    Point(9, 9),
}


def print_grid():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = Point(y, x)
            if p in WHITES:
                if WHITES[p] is not None:
                    print(f"{WHITES[p]}", end=' ')
                else:
                    print(f"W", end=' ')
            elif p in BLACKS:
                print(f"B", end=' ')
            else:
                print(".", end=' ')
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
            sg.cell_is(p, sym.W)
        )
        if v is None:
            continue
        sg.solver.add(
            rc.region_size_grid[p] == v,
            rc.parent_grid[p] == grilops.regions.R
        )

    for p in BLACKS:
        sg.solver.add(
            sg.cell_is(p, sym.B),
        )

    # 黑区 只能各有一个
    black_root = la.point_to_index(min(BLACKS))

    for p in la.points:
        sg.solver.add(
            Implies(sg.cell_is(p, sym.B), rc.region_id_grid[p] == black_root)
        )

    # 禁止黑色 4 格小 T 形状
    # 三连横，中间下面一个
    for y in range(HEIGHT - 1):
        for x in range(WIDTH - 3):
            p1 = Point(y, x)
            p2 = Point(y, x + 1)
            p3 = Point(y, x + 2)
            p4 = Point(y + 1, x + 1)
            sg.solver.add(
                Not(And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B),
                        sg.cell_is(p3, sym.B), sg.cell_is(p4, sym.B)))
            )
    # 三连横，中间上面一个
    for y in range(1, HEIGHT):
        for x in range(WIDTH - 3):
            p1 = Point(y, x)
            p2 = Point(y, x + 1)
            p3 = Point(y, x + 2)
            p4 = Point(y - 1, x + 1)
            sg.solver.add(
                Not(And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B),
                        sg.cell_is(p3, sym.B), sg.cell_is(p4, sym.B)))
            )
    # 三连竖，中间右边一个
    for y in range(HEIGHT - 3):
        for x in range(WIDTH - 1):
            p1 = Point(y, x)
            p2 = Point(y + 1, x)
            p3 = Point(y + 2, x)
            p4 = Point(y + 1, x + 1)
            sg.solver.add(
                Not(And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B),
                        sg.cell_is(p3, sym.B), sg.cell_is(p4, sym.B)))
            )
    # 三连竖，中间左边一个
    for y in range(HEIGHT - 3):
        for x in range(1, WIDTH):
            p1 = Point(y, x)
            p2 = Point(y + 1, x)
            p3 = Point(y + 2, x)
            p4 = Point(y + 1, x - 1)
            sg.solver.add(
                Not(And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B),
                        sg.cell_is(p3, sym.B), sg.cell_is(p4, sym.B)))
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
