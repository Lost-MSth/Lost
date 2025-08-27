"""Spiral Galaxies solver example.

Example puzzle can be found at
https://www.gmpuzzles.com/blog/spiral-galaxies-rules-info/.

For CCBC16 changed by Lost-MSth
"""

import math
from z3 import And, Or, Implies, PbEq

import grilops
import grilops.regions
from grilops.geometry import Point


HEIGHT, WIDTH = 15, 15
GIVENS = [
    (0, 1.5),
    (0, 9.5),
    (0, 13),
    (0.5, 4),
    (0.5, 7),
    (1.5, 5),
    (2, 1.5),
    (2, 3),
    (2, 7),
    (2, 10),
    (2.5, 13),
    (3, 5),
    (3, 11),
    (4, 6),
    (4, 14),
    (5, 0.5),
    (5, 2.5),
    (5, 10),
    (5, 13),
    (6, 0),
    (6, 12.5),
    (7, 2),
    (7, 4),
    (7, 11),
    (7.5, 5.5),
    (7.5, 9),
    (7.5, 12),
    (8, 0),
    (8, 3),
    (8, 7),
    (9, 3),
    (9.5, 7.5),
    (10, 4),
    (10, 5),
    (10, 13),
    (10.5, 0),
    (11, 3.5),
    (11, 8.5),
    (11.5, 7),
    (11.5, 10),
    (12, 1),
    (12, 3),
    (12, 8.5),
    (12, 11),
    (12, 14),
    (12.5, 5),
    (13, 2.5),
    (13, 8.5),
    (13.5, 6),
    (13.5, 6),
    (13.5, 10),
    (13.5, 12),
    (14, 3),
    (14, 7.5),
    (14, 13.5),
]


def main():
    """Spiral Galaxies solver example."""
    # The grid symbols will be the region IDs from the region constrainer.
    sym = grilops.make_number_range_symbol_set(-1, HEIGHT * WIDTH - 1)
    lattice = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
    sg = grilops.SymbolGrid(lattice, sym)
    rc = grilops.regions.RegionConstrainer(lattice, sg.solver, complete=False)

    for p in sg.grid:
        sg.solver.add(sg.cell_is(p, rc.region_id_grid[p]))

    # Make the upper-left-most cell covered by a circle the root of its region.
    roots = {(int(math.floor(y)), int(math.floor(x))) for (y, x) in GIVENS}
    r = grilops.regions.R
    for y in range(HEIGHT):
        for x in range(WIDTH):
            sg.solver.add(
                (rc.parent_grid[Point(y, x)] == r) == ((y, x) in roots))

    # Ensure that each cell has a "partner" within the same region that is
    # rotationally symmetric with respect to that region's circle.
    for p in lattice.points:
        or_terms = []
        for (gy, gx) in GIVENS:
            region_id = lattice.point_to_index(
                Point(int(math.floor(gy)), int(math.floor(gx))))
            partner = Point(int(2 * gy - p.y), int(2 * gx - p.x))
            if lattice.point_to_index(partner) is None:
                continue
            or_terms.append(
                And(
                    rc.region_id_grid[p] == region_id,
                    rc.region_id_grid[partner] == region_id,
                )
            )
        sg.solver.add(Implies(
            rc.region_id_grid[p] != -1,
            Or(*or_terms)
        ))

    empty = -1
    # 空白位置每行每列三个
    for y in range(HEIGHT):
        sg.solver.add(
            PbEq(
                [(sg.cell_is(Point(y, x), empty), 1) for x in range(WIDTH)],
                3,
            )
        )
    for x in range(WIDTH):
        sg.solver.add(
            PbEq(
                [(sg.cell_is(Point(y, x), empty), 1) for y in range(HEIGHT)],
                3,
            )
        )
    # 空白位置禁止相邻或者对角相邻
    for p in lattice.points:
        sg.solver.add(Implies(
            sg.cell_is(p, empty),
            And(
                [n.symbol != empty for n in
                 sg.vertex_sharing_neighbors(p) + sg.edge_sharing_neighbors(p)],
            )
        ))

    def show_cell(unused_p, region_id):
        rp = lattice.points[region_id]
        for i, (gy, gx) in enumerate(GIVENS):
            if int(math.floor(gy)) == rp.y and int(math.floor(gx)) == rp.x:
                return chr(65 + i)
        if region_id == -1:
            return '.'
        raise RuntimeError("unexpected region id")

    if sg.solve():
        sg.print(show_cell)
        print()
        rc.print_region_ids()
        print()
        if sg.is_unique():
            print("Unique solution")
        else:
            print("Alternate solution")
            sg.print(show_cell)
    else:
        print("No solution")


if __name__ == "__main__":
    main()
