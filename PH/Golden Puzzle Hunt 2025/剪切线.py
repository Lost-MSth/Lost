"""
https://goldenph.art/puzzle?key=clue_03

by Lost-MSth
"""

import grilops
import grilops.regions
import grilops.sightlines
from grilops.geometry import Point
from z3 import And, If, Implies, Not, PbEq

HEIGHT, WIDTH = 10, 10


BLUES = {
    Point(0, 2): 5,
    Point(1, 0): 6,
    Point(1, 5): 3,
    Point(6, 0): 5,
    Point(6, 5): 4,
    Point(8, 1): 4,
    Point(2, 3): 3,
    Point(4, 4): 3,
}

REDS = {
    Point(0, 7): 1,
    Point(1, 5): 3,
    Point(3, 6): 2,
    Point(4, 9): 1,
    Point(5, 7): 3,
    Point(7, 3): 2,
    Point(8, 6): 3,
    Point(9, 9): 0,
    Point(2, 3): 3,
    Point(4, 4): 3,
}

GREENS = {
    Point(3, 1): 4,
    Point(2, 8): 7,
    Point(1, 0): 6,
    Point(5, 2): 7,
    Point(7, 8): 7,
    Point(8, 6): 3,
    Point(9, 4): 5,
    Point(2, 3): 3,
    Point(4, 4): 3,
}


ROOT = [Point(4, 0), Point(5, 0)]


def main():

    MINS = 5

    # The grid symbols will be the region IDs from the region constrainer.
    sym = grilops.make_number_range_symbol_set(0, HEIGHT * WIDTH - 1)
    lattice = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
    sg = grilops.SymbolGrid(lattice, sym)
    rc = grilops.regions.RegionConstrainer(
        lattice, sg.solver,
        min_region_size=MINS,
        max_region_size=HEIGHT * WIDTH - MINS
    )
    for point in lattice.points:
        sg.solver.add(sg.cell_is(point, rc.region_id_grid[point]))

    # only two regions are allowed
    sg.solver.add(rc.parent_grid[ROOT[0]] == grilops.regions.R)
    sg.solver.add(rc.parent_grid[ROOT[1]] == grilops.regions.R)
    for point in lattice.points:
        if point in ROOT:
            continue
        sg.solver.add(rc.parent_grid[point] != grilops.regions.R)

    # Blue constraints
    # 周围 3*3 数量匹配
    for point, value in BLUES.items():
        my_symbol = sg.grid[point]
        sg.solver.add(
            PbEq(
                [(my_symbol == v.symbol, 1)
                 for v in sg.vertex_sharing_neighbors(point)],
                value - 1
            )
        )

    # Red constraints
    # 周围四邻居有多少个和自己不一样
    for point, value in REDS.items():
        my_symbol = sg.grid[point]
        neighbors = sg.edge_sharing_neighbors(point)
        sg.solver.add(
            PbEq(
                [(my_symbol != v.symbol, 1) for v in neighbors],
                value
            )
        )

    # Green constraints
    # 向四个方向看去，和自己一样的数量
    for point, value in GREENS.items():
        my_symbol = sg.grid[point]
        ss = sum(grilops.sightlines.count_cells(
            sg, n.location, n.direction,
            count=lambda c: If(c == my_symbol, 1, 0),
            stop=lambda c: c != my_symbol
        ) for n in sg.edge_sharing_neighbors(point))
        sg.solver.add(ss == value-1)

    def show_cell(unused_loc, region_id):
        return 'x' if region_id <= 40 else 'o'

    if sg.solve():
        sg.print(show_cell)
        print()
        # for point in lattice.points:
        #     print(f"{point}: {sg.solver.model()[sg.grid[point]]}")
        # if sg.is_unique():
        #     print("Unique solution")
        # else:
        #     print("Alternate solution")
        #     sg.print(show_cell)
        while not sg.is_unique():
            print("Alternate solution")
            sg.print(show_cell)
            print()
    else:
        print("No solution")


if __name__ == "__main__":
    main()
