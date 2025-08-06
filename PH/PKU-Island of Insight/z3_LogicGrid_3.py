# https://mp.weixin.qq.com/s/VZEnwL3IKN3tHDH6tOixgg

import grilops
import grilops.regions
from grilops import Point
from z3 import *


WIDTH = 10
HEIGHT = 10

WHITES = {
    Point(0, 4),
    Point(3, 1),
    Point(4, 3),
    Point(5, 6),
    Point(8, 4),
}

BLACKS = {
    Point(1, 3),
    Point(2, 2),
    Point(3, 8),
    Point(4, 2),
    Point(4, 4),
    Point(5, 4),
    Point(6, 2),
    Point(6, 5),
}


def print_grid():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = Point(y, x)
            if p in WHITES:
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

    for p in WHITES:
        sg.solver.add(
            sg.cell_is(p, sym.W),
        )

    for p in BLACKS:
        sg.solver.add(
            sg.cell_is(p, sym.B),
        )

    # 黑区 白区 只能各有一个
    black_root = la.point_to_index(min(BLACKS))
    white_root = la.point_to_index(min(WHITES))

    for p in la.points:
        sg.solver.add(Or(
            And(sg.cell_is(p, sym.W), rc.region_id_grid[p] == white_root),
            And(sg.cell_is(p, sym.B), rc.region_id_grid[p] == black_root)
        ))

    # 禁止黑色 2*2
    for y in range(HEIGHT - 1):
        for x in range(WIDTH - 1):
            p1 = Point(y, x)
            p2 = Point(y + 1, x)
            p3 = Point(y, x + 1)
            p4 = Point(y + 1, x + 1)
            sg.solver.add(
                Not(And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B),
                        sg.cell_is(p3, sym.B), sg.cell_is(p4, sym.B)))
            )

    # 禁止白色 4*1 1*4
    for y in range(HEIGHT):
        for x in range(WIDTH - 3):
            p1 = Point(y, x)
            p2 = Point(y, x + 1)
            p3 = Point(y, x + 2)
            p4 = Point(y, x + 3)
            sg.solver.add(
                Not(And(sg.cell_is(p1, sym.W), sg.cell_is(p2, sym.W),
                        sg.cell_is(p3, sym.W), sg.cell_is(p4, sym.W)))
            )
    for x in range(WIDTH):
        for y in range(HEIGHT - 3):
            p1 = Point(y, x)
            p2 = Point(y + 1, x)
            p3 = Point(y + 2, x)
            p4 = Point(y + 3, x)
            sg.solver.add(
                Not(And(sg.cell_is(p1, sym.W), sg.cell_is(p2, sym.W),
                        sg.cell_is(p3, sym.W), sg.cell_is(p4, sym.W)))
            )

    # 颜色相同连一起是一个区，不同则不是
    # for p in la.points:
    #     p1 = p
    #     for n in sg.edge_sharing_neighbors(p):
    #         p2 = n.location
    #         sg.solver.add(
    #             (rc.region_id_grid[p1] == rc.region_id_grid[p2]) ==
    #             Or(
    #                 And(sg.cell_is(p1, sym.W), sg.cell_is(p2, sym.W)),
    #                 And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B))
    #             )
    #         )

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
