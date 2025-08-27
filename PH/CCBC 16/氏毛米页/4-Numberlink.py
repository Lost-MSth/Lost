"""Numberlink solver example.

Example puzzle can be found at https://en.wikipedia.org/wiki/Numberlink.

CCBC 16 by Lost-MSth
"""

from collections import defaultdict
from itertools import permutations

import grilops
import grilops.paths
from grilops.geometry import Point

HEIGHT, WIDTH = 7, 7
GIVENS = {
    Point(1, 1): 'D',
    Point(1, 3): 'A',
    Point(2, 1): 'B',
    Point(2, 4): 'F',
    Point(4, 1): 'G',
    Point(4, 6): 'C',
    Point(5, 6): 'E',
}

CHARS = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
BLACKS = [
    Point(1, 5), Point(2, 0), Point(4, 0),
    Point(4, 3), Point(4, 4),
    Point(5, 3), Point(5, 4),
]

LATTICE = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
SYM = grilops.paths.PathSymbolSet(LATTICE)
SYM.append("BLANK", " ")


def one_try(chars: 'tuple[str]'):
    print(f'One test for {chars}')
    this_givens = GIVENS.copy()
    for p, c in zip(BLACKS, chars):
        this_givens[p] = c

    sg = grilops.SymbolGrid(LATTICE, SYM)
    pc = grilops.paths.PathConstrainer(sg, allow_loops=False)

    for p, cell in sg.grid.items():
        sg.solver.add(SYM.is_terminal(cell) == (p in this_givens))

    number_to_points = defaultdict(list)
    for p, n in this_givens.items():
        number_to_points[n].append(p)
    for points in number_to_points.values():
        assert len(points) == 2
        path_instance = LATTICE.point_to_index(points[0])
        sg.solver.add(pc.path_instance_grid[points[0]] == path_instance)
        sg.solver.add(pc.path_instance_grid[points[1]] == path_instance)

    def print_grid():
        sg.print(lambda p, _: str(this_givens[(p.y, p.x)]) if (
            p.y, p.x) in this_givens else None)

    if sg.solve():
        print_grid()
        print()
        if sg.is_unique():
            print("Unique solution")
            exit(0)
        else:
            print("Alternate solution")
            print_grid()
    else:
        print("No solution")


def main():
    for perm in permutations(CHARS):
        one_try(perm)


if __name__ == "__main__":
    main()
