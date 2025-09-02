# https://mp.weixin.qq.com/s/vN_etSaBG3ZR3foJuOaxjA

import grilops
import grilops.regions
from grilops import Point
from grilops.sightlines import count_cells
from z3 import *

WIDTH = 8
HEIGHT = 8

WHITES = {
    Point(0, 1): 'A', Point(0, 7): 'A',
    Point(2, 2): 5, Point(2, 5): 5,
    Point(6, 0): 'C',
    Point(7, 3): 'A', Point(7, 7): 'B',
}

def extra_rules(sg, rc: grilops.regions.RegionConstrainer):
    # 人肉猜测的特殊规则，为了加快计算
    # 两个 5 大概不是一个区的，当然只要改一下就可以两种可能都遍历（改后两行的判断，取反，可发现无解）
    sg.solver.add(
        rc.parent_grid[Point(2, 2)] == grilops.regions.R,
        rc.parent_grid[Point(2, 5)] == grilops.regions.R,
        rc.region_id_grid[Point(2, 2)] != rc.region_id_grid[Point(2, 5)],
    )


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

    extra_rules(sg, rc)

    white_class = {}
    for p, v in WHITES.items():
        sg.solver.add(
            sg.cell_is(p, sym.W)
        )
        if v is None:
            continue
        elif isinstance(v, int):
            sg.solver.add(
                rc.region_size_grid[p] == v,
            )
        elif isinstance(v, str):
            white_class.setdefault(v, []).append(p)

    for v in white_class.values():
        sg.solver.add(
            rc.parent_grid[v[0]] == grilops.regions.R
        )
        for p in v[1:]:
            sg.solver.add(
                rc.parent_grid[p] != grilops.regions.R,
                rc.region_id_grid[p] == rc.region_id_grid[v[0]]
            )

    for p in la.points:
        sum_expr = [(n.symbol == sym.B, 1)
                    for n in sg.edge_sharing_neighbors(p)]
        sg.solver.add(
            # 黑区面积必须为 2
            Implies(sg.cell_is(p, sym.B), rc.region_size_grid[p] == 2),
            # 黑格面积为 2 的加强条件
            Implies(sg.cell_is(p, sym.B), PbEq(sum_expr, 1))
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
