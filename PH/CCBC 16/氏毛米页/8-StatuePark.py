"""
Statue Park solver example.

CCBC 16 changed by Lost-MSth
"""
from itertools import combinations, combinations_with_replacement
from time import time

import grilops
import grilops.regions
from grilops.geometry import Point, Vector
from grilops.shapes import Shape, ShapeConstrainer
from z3 import And, Implies

HEIGHT, WIDTH = 11, 11

WHITES = [
    Point(0, 5), Point(1, 5), Point(2, 5), Point(3, 5),
    Point(1, 2),
    Point(5, 0), Point(5, 1), Point(5, 2), Point(5, 3),
    Point(5, 7), Point(5, 8), Point(5, 9), Point(5, 10),
    Point(7, 5), Point(8, 5), Point(9, 5), Point(10, 5),
    Point(4, 4), Point(4, 6), Point(6, 4), Point(6, 6),

    # 中间啥也放不了，必须是白的
    Point(5, 5), Point(4, 5), Point(6, 5), Point(5, 4), Point(5, 6),
]

UNKNOWN = [
    Point(6, 0), Point(4, 9), Point(7, 8)
]
CHARS = ['B', 'W']

SHAPES = [
    [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],  # I
    [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],  # I
    [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],  # I
    [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1), (3, 1)],
    [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0), (2, 1), (3, 0)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
]

LATTICE = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
SYM = grilops.symbols.make_number_range_symbol_set(-1, len(SHAPES) - 1)

START_TIME = time()


def one_try(clues):
    print(f'Trying clues: {clues}')

    sg = grilops.SymbolGrid(LATTICE, SYM)

    sc = ShapeConstrainer(
        LATTICE,
        [Shape([Vector(y, x) for y, x in shape]) for shape in SHAPES],
        solver=sg.solver,
        allow_rotations=True,
        allow_reflections=True,
        allow_copies=False
    )
    rg = grilops.regions.RegionConstrainer(
        LATTICE,
        solver=sg.solver,
        complete=False,
    )

    white_root = LATTICE.point_to_index(min(WHITES))

    for p, c in clues.items():
        if c == 'W':
            sg.solver.add(sg.cell_is(p, -1))
        elif c == 'B':
            sg.solver.add(sg.grid[p] != -1)

    for p in LATTICE.points:
        if p in WHITES:
            sg.solver.add(sg.cell_is(p, -1))
        sg.solver.add(sg.grid[p] == sc.shape_type_grid[p])
        sg.solver.add(Implies(
            sg.cell_is(p, -1),
            rg.region_id_grid[p] == white_root
        ))
        sg.solver.add(Implies(
            sg.grid[p] != -1,
            rg.region_id_grid[p] == -1
        ))

        # Orthogonally-adjacent cells must be part of the same shape.
        for n in sg.edge_sharing_neighbors(p):
            np = n.location
            sg.solver.add(
                Implies(
                    And(
                        sc.shape_type_grid[p] != -1,
                        sc.shape_type_grid[np] != -1
                    ),
                    sc.shape_type_grid[p] == sc.shape_type_grid[np]
                )
            )

    def print_hook(p, x):
        if p in WHITES:
            return 'o'
        if x == -1:
            return '.'
        return chr(ord('A') + x)

    if sg.solve():
        sg.print(print_hook)
        print()
        sc.print_shape_types()
        print()
        print(f"Time taken: {time() - START_TIME:.2f} seconds")
        if sg.is_unique():
            print("Unique solution")
        else:
            print("Alternate solution")
            sg.print(print_hook)
    else:
        print("No solution")


def main():
    # for i in range(len(UNKNOWN), -1, -1):
    #     for ps in combinations(UNKNOWN, i):
    #         for cs in combinations_with_replacement(CHARS, i):
    #             one_try(dict(zip(ps, cs)))

    one_try({
        Point(6, 0): 'W', Point(4, 9): 'B', Point(7, 8): 'B'
    })


if __name__ == "__main__":
    main()
