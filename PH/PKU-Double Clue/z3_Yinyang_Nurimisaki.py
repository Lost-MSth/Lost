# https://mp.weixin.qq.com/s/w8jKJtUAmYsBBj19sLdx1w

import grilops
import grilops.regions
from grilops import Point
from z3 import *


WIDTH = 10
HEIGHT = 10

WHITES = {
    Point(1, 0): 1,
    Point(2, 2): 1,
    Point(4, 7): 1,
    Point(5, 4): 1,
    Point(5, 9): 1,
    Point(7, 3): 1,
}

BLACKS = {
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
        )

    for p, v in BLACKS.items():
        sg.solver.add(
            sg.cell_is(p, sym.B),
        )

    # 白色和黑色各只有一个区
    # white_root = Int('white_root')
    # 优化，直接取一个 white 圈作为 root
    white_root = la.point_to_index(list(WHITES.keys())[0])
    black_root = Int('black_root')
    # sg.solver.add(white_root >= 0, white_root <= HEIGHT * WIDTH - 1)
    sg.solver.add(black_root >= 0, black_root <= HEIGHT * WIDTH - 1)
    sg.solver.add(white_root != black_root)
    for p in la.points:
        sg.solver.add(
            Implies(
                sg.cell_is(p, sym.W),
                rc.region_id_grid[p] == white_root
            )
        )
        sg.solver.add(
            Implies(
                sg.cell_is(p, sym.B),
                rc.region_id_grid[p] == black_root
            )
        )

    # 没有 2*2 结构
    for y in range(HEIGHT - 1):
        for x in range(WIDTH - 1):
            p1 = Point(y, x)
            p2 = Point(y + 1, x)
            p3 = Point(y, x + 1)
            p4 = Point(y + 1, x + 1)
            sg.solver.add(
                Not(And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B),
                        sg.cell_is(p3, sym.B), sg.cell_is(p4, sym.B))),
                Not(And(sg.cell_is(p1, sym.W), sg.cell_is(p2, sym.W),
                        sg.cell_is(p3, sym.W), sg.cell_is(p4, sym.W)))
            )

    # Nurimisaki 规则：有且只有白圈邻接只有一个白格
    for p in la.points:
        sums = Sum(
            [If(n.symbol == sym.W, 1, 0) for n in sg.edge_sharing_neighbors(p)]
        )
        if p in WHITES:
            sg.solver.add(sums == 1)
        else:
            sg.solver.add(Implies(sg.cell_is(p, sym.W),
                                  sums != 1))

    if sg.solve():
        sg.print()
        # rc.print_region_ids()
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
