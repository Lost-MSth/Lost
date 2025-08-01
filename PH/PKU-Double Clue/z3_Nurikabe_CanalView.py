# https://mp.weixin.qq.com/s/yC_gOh24rgVof00JeUbkow

import grilops
import grilops.regions
import grilops.sightlines
from grilops import Point
from z3 import *

WIDTH = 10
HEIGHT = 10

CLUES = {
    Point(1, 1): 4,
    Point(2, 2): 4,
    Point(2, 7): 4,
    Point(3, 9): 4,
    Point(4, 5): 4,
    Point(5, 2): 4,
    Point(7, 7): 4,
    Point(8, 2): 4,
    Point(9, 0): 4,
    Point(9, 5): 4,
    Point(9, 8): 4,
}


def print_grid():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = Point(y, x)
            if p in CLUES:
                print(f"{CLUES[p]:2d}", end=' ')
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

    # 每个白区域有一个数字
    # Nurikabe 规则认为是区域大小，Canal View 规则认为是四方向黑格数量
    for p, v in CLUES.items():
        sg.solver.add(
            sg.cell_is(p, sym.W),
            rc.region_size_grid[p] == v,
            rc.parent_grid[p] == grilops.regions.R,
            rc.region_id_grid[p] == la.point_to_index(p),
            Sum([
                grilops.sightlines.count_cells(
                    sg, n.location, n.direction,
                    lambda c: If(c == sym.B, 1, 0),
                    lambda c: c != sym.B
                ) for n in sg.edge_sharing_neighbors(p)
            ]) == v
        )

    for p in la.points:
        if p in CLUES:
            continue
        sg.solver.add(
            Implies(
                sg.cell_is(p, sym.W),
                rc.parent_grid[p] != grilops.regions.R
            )
        )

    # 黑色只有一个区
    black_root = Int('black_root')
    sg.solver.add(black_root >= 0, black_root <= HEIGHT * WIDTH - 1)
    for p in la.points:
        sg.solver.add(
            sg.cell_is(p, sym.B) == (rc.region_id_grid[p] == black_root)
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
