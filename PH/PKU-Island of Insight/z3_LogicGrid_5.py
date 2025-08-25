# https://mp.weixin.qq.com/s/f4KWCNdktGC-2zh7o2bokw

import grilops
import grilops.regions
from grilops import Point
from grilops.sightlines import count_cells
from z3 import *

WIDTH = 10
HEIGHT = 10

WHITES = {
    Point(0, 3): 2,
    Point(3, 8): 2,
    Point(4, 3): 2, Point(4, 5): 2,
    Point(5, 4): 2,
    Point(7, 2): 2, Point(7, 5): 2,
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
            Sum(
                [count_cells(sg, n.location, n.direction,
                             lambda c: c == sym.W,
                             lambda c: c == sym.B)
                 for n in sg.edge_sharing_neighbors(p)],
            ) == v - 1
        )

    # 白区 只能各有一个
    white_root = la.point_to_index(min(WHITES))

    for p in la.points:
        sum_expr = [(n.symbol == sym.B, 1)
                    for n in sg.edge_sharing_neighbors(p)]
        sg.solver.add(
            Or(
                And(sg.cell_is(p, sym.W), rc.region_id_grid[p] == white_root),
                # 黑区面积必须为 3
                And(sg.cell_is(p, sym.B), rc.region_size_grid[p] == 3)
            ),
            # 黑格面积为 3 的加强条件
            Implies(sg.cell_is(p, sym.B),
                    Or(
                    And(PbEq(sum_expr, 1),
                        rc.parent_grid[p] != grilops.regions.R),
                    And(PbEq(sum_expr, 2),
                        rc.parent_grid[p] == grilops.regions.R)
                    ))
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
