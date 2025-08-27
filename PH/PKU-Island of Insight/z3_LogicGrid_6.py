# https://mp.weixin.qq.com/s/jZWIK0BxARiUtLIDUO7eIA

import grilops
import grilops.regions
from grilops import Point
from z3 import *

WIDTH = 11
HEIGHT = 11

WHITES = {
    Point(1, 1): None, Point(1, 3): None, Point(1, 5): None, Point(1, 7): 2, Point(1, 9): None,
    Point(3, 1): 33, Point(3, 3): None, Point(3, 5): None, Point(3, 7): None, Point(3, 9): None,
    Point(5, 1): None, Point(5, 3): 33, Point(5, 5): None, Point(5, 7): 8, Point(5, 9): None,
    Point(7, 1): None, Point(7, 3): None, Point(7, 5): None, Point(7, 7): None, Point(7, 9): 8,
    Point(9, 1): None, Point(9, 3): 2, Point(9, 5): None, Point(9, 7): None, Point(9, 9): None,
}

BLACKS = {
    Point(0, 0): 72, Point(0, 10): None,
    Point(10, 0): None, Point(10, 10): None,
}


def extra_rules(sg, rc: grilops.regions.RegionConstrainer):
    # 人肉添加的特殊规则，为了加快计算
    # 注意到 121 - 72 - 33 - 8 = 8， 所以白色的 33、8 都是一个区
    sg.solver.add(
        rc.parent_grid[Point(3, 1)] == grilops.regions.R,
        rc.parent_grid[Point(5, 3)] != grilops.regions.R,
        rc.region_id_grid[Point(3, 1)] == rc.region_id_grid[Point(5, 3)],
        rc.parent_grid[Point(5, 7)] == grilops.regions.R,
        rc.parent_grid[Point(7, 9)] != grilops.regions.R,
        rc.region_id_grid[Point(5, 7)] == rc.region_id_grid[Point(7, 9)],
        rc.parent_grid[Point(1, 7)] == grilops.regions.R,
        rc.parent_grid[Point(9, 3)] == grilops.regions.R,
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

    extra_rules(sg, rc)

    for p, v in WHITES.items():
        sg.solver.add(
            sg.cell_is(p, sym.W)
        )
        if v is None:
            continue
        sg.solver.add(
            rc.region_size_grid[p] == v,
        )

    for p, v in BLACKS.items():
        sg.solver.add(
            sg.cell_is(p, sym.B),
        )
        if v is None:
            continue
        sg.solver.add(
            rc.region_size_grid[p] == v,
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
