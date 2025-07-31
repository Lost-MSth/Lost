# https://mp.weixin.qq.com/s/SyMBbgeDVxVDTgB4X2gKgA

import grilops
import grilops.regions
from grilops import Point
from z3 import *


WIDTH = 8
HEIGHT = 8

CLUES = {
    Point(0, 7): 'NE',
    Point(1, 5): 'NE',
    Point(2, 3): 'W',
    Point(3, 2): 'E',
    Point(5, 4): 'NW',
    Point(6, 2): 'N',
    Point(7, 0): 'NE',
    Point(7, 5): 'N',
}


def print_grid():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = Point(y, x)
            if p in CLUES:
                print(f"{CLUES[p]:2s}", end=' ')
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

    black_root = Int('black_root')
    sg.solver.add(black_root >= 0, black_root <= HEIGHT * WIDTH - 1)

    for p in la.points:
        # 黑色必须全连通，只有一个区域
        sg.solver.add(
            Implies(
                sg.cell_is(p, sym.B),
                rc.region_id_grid[p] == black_root
            )
        )

        # 白色区域必须有 clue
        if p not in CLUES:
            sg.solver.add(
                Implies(
                    sg.cell_is(p, sym.W),
                    rc.parent_grid[p] != grilops.regions.R
                )
            )

    # 每个白色区域只能有一个 clue，直接设为 root
    for p in CLUES.keys():
        sg.solver.add(
            sg.cell_is(p, sym.W),
            rc.parent_grid[p] == grilops.regions.R
        )

    # clue 镜像对称要求
    for p in la.points:
        or_terms = []
        for g, mode in CLUES.items():
            region_id = la.point_to_index(g)
            if mode in ['N', 'S']:
                partner = Point(p.y, 2*g.x - p.x)
            elif mode in ['W', 'E']:
                partner = Point(2*g.y - p.y, p.x)
            elif mode in ['NW', 'SE']:
                partner = Point(g.y+p.x-g.x, g.x+p.y-g.y)
            elif mode in ['NE', 'SW']:
                partner = Point(g.y-p.x+g.x, g.x-p.y+g.y)
            else:
                raise ValueError(f"Unknown clue mode: {mode}")

            if la.point_to_index(partner) is None:
                continue

            or_terms.append(
                And(
                    rc.region_id_grid[p] == region_id,
                    rc.region_id_grid[partner] == region_id,
                )
            )

        sg.solver.add(
            Implies(sg.cell_is(p, sym.W), Or(*or_terms))
        )

    # 不允许 2*2 黑色
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
