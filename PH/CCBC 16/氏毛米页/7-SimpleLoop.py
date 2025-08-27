"""
Simple Loop with some blacks

CCBC 16 by Lost-MSth
"""

from itertools import combinations
from time import time

import grilops
import grilops.paths
from grilops.geometry import Point

HEIGHT, WIDTH = 10, 10

BLACKS = [
    Point(0, 1), Point(0, 6),
    Point(1, 2), Point(1, 5),
    Point(2, 8),
    Point(3, 9),
    Point(4, 1),
    Point(5, 0),
    Point(6, 8),
    Point(7, 6), Point(7, 9),
    Point(8, 2), Point(8, 5),
    Point(9, 1),
]

CHARS = {
    Point(2, 4): 'C',
    Point(2, 6): 'A',
    Point(3, 2): 'D',
    Point(5, 6): 'B',
    Point(6, 3): 'E',
}

LATTICE = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
SYM = grilops.paths.PathSymbolSet(LATTICE)
SYM.append("BLANK", " ")

START_TIME = time()


def one_try(blacks: 'list'):
    print(f'One test for {blacks}')

    sg = grilops.SymbolGrid(LATTICE, SYM)
    pc = grilops.paths.PathConstrainer(sg, allow_terminated_paths=False)
    sg.solver.add(pc.num_paths == 1)

    assert Point(0, 0) not in blacks
    # 限定开始点，加速
    sg.solver.add(pc.path_order_grid[Point(0, 0)] == 0)

    for p in LATTICE.points:
        if p in blacks:
            sg.solver.add(pc.path_instance_grid[p] == -1)
        else:
            sg.solver.add(pc.path_instance_grid[p] != -1)

    def print_grid():
        sg.print(lambda p, _: str(CHARS[(p.y, p.x)]) if p in CHARS else (
            'X' if p in blacks else None))

    if sg.solve():
        print_grid()
        print(f"Time taken: {time() - START_TIME:.2f} seconds")
        if sg.is_unique():
            print("Unique solution")
            exit(0)
        else:
            print("Alternate solution")
            print_grid()
    else:
        print("No solution")


def main():
    # step=2 因为奇数个格子不可能实现回路
    for l in range(2, len(BLACKS)+1, 2):
        for x in combinations(BLACKS, l):
            one_try(x)


if __name__ == "__main__":
    main()
