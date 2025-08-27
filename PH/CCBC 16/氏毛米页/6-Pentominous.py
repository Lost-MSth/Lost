"""
Pentominous solver

CCBC 16 changed by Lost-MSth
"""

from itertools import combinations_with_replacement
from time import time

import grilops
from grilops.geometry import Point, Vector
from grilops.shapes import Shape, ShapeConstrainer
from z3 import Implies

HEIGHT, WIDTH = 10, 10
TYPES = ['F', 'I', 'L', 'N', 'P', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

GIVENS = {
    Point(0, 4): 'X', Point(0, 5): 'I',
    Point(2, 8): 'F',
    Point(3, 1): 'T',
    Point(5, 4): 'X',
    Point(5, 6): 'X',
    Point(6, 2): 'N',
    Point(8, 2): 'N',
    Point(8, 8): 'N',
}
BLACKS = [Point(2, 5), Point(5, 9)]

SHAPES = [
    [(0, 0), (0, 1), (-1, 1), (1, 1), (1, 2)],  # F
    [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],  # I
    [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1)],  # L
    [(0, 0), (1, 0), (2, 0), (2, 1), (3, 1)],  # N
    [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1)],  # P
    [(0, 0), (1, 0), (2, 0), (2, -1), (2, 1)],  # T
    [(0, 0), (1, 0), (0, 1), (0, 2), (1, 2)],  # U
    [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],  # V
    [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],  # W
    [(0, 0), (1, 0), (1, 1), (1, -1), (2, 0)],  # X
    [(0, 0), (1, 0), (2, 0), (2, -1), (3, 0)],  # Y
    [(0, 0), (0, 1), (-1, 1), (-2, 1), (-2, 2)],  # Z
]

LATTICE = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
SYM = grilops.SymbolSet(TYPES)

START_TIME = time()


def one_try(chars):
    print(f'One test for {chars}')

    this_givens = GIVENS.copy()
    for p, c in zip(BLACKS, chars):
        this_givens[p] = c

    sg = grilops.SymbolGrid(LATTICE, SYM)
    sc = ShapeConstrainer(
        LATTICE,
        [Shape([Vector(y, x) for y, x in shape]) for shape in SHAPES],
        solver=sg.solver,
        allow_rotations=True,
        allow_reflections=True,
        allow_copies=True,
        complete=True
    )

    sg.solver.add(sc.shape_instance_grid[Point(0, 0)] == 0)

    for p, c in this_givens.items():
        sg.solver.add(sc.shape_type_grid[p] == TYPES.index(c))

    for p in LATTICE.points:
        sg.solver.add(
            sc.shape_type_grid[p] == sg.grid[p]
        )

        for n in sg.edge_sharing_neighbors(p):
            np = n.location
            sg.solver.add(
                (sc.shape_instance_grid[p] == sc.shape_instance_grid[np])
                == (sc.shape_type_grid[p] == sc.shape_type_grid[np])
            )

    if sg.solve():
        sg.print()
        print()
        sc.print_shape_types()
        print()
        print(f"Time taken: {time() - START_TIME:.2f} seconds")
        if sg.is_unique():
            print("Unique solution")
            exit(0)
        else:
            print("Alternate solution")
            sg.print()
    else:
        print("No solution")


def main():
    for i in range(len(BLACKS), -1, -1):
        for chars in combinations_with_replacement(TYPES, i):
            one_try(chars)


if __name__ == "__main__":
    main()
