import grilops
import grilops.sightlines as sl
from grilops.geometry import Point
from z3 import *

N = 8
M = 8

# E 视野：线索表示周围四方向上能看到的非雷格数之和。

MINE_AMOUNT = 23
MINE_NUMBERS = {
    (0, 2): 2, (0, 5): 6,
    (1, 3): 8,
    (2, 0): 1, (2, 3): 9, (2, 7): 7,
    (3, 5): 11,
    (4, 2): 10, (4, 6): 8,
    (5, 0): 5, (5, 4): 12, (5, 7): 3,
    (7, 2): 8, (7, 5): 4,
}
NOT_MINES = []

# print the puzzle
for i in range(N):
    for j in range(M):
        if (i, j) in MINE_NUMBERS:
            print(MINE_NUMBERS[(i, j)], end=' ')
        else:
            print('.', end=' ')
    print()
print()


def print_answer(sg: grilops.SymbolGrid):
    m = sg.solver.model()
    for y in range(N):
        count = 0
        for x in range(M):
            p = Point(y, x)
            if m.eval(sg.cell_is(p, sg.symbol_set.M)):
                print('  x', end='')
                count += 1
            else:
                print(f'{m.eval(sg.grid[p]).as_long():3}', end='')
        print(f'   | {count}')


def main():
    sym = grilops.make_number_range_symbol_set(0, N+M-1)
    sym.append('M', 'x')
    lattice = grilops.get_rectangle_lattice(N, M)
    DIRECTIONS = {d.name: d for d in lattice.edge_sharing_directions()}
    sg = grilops.SymbolGrid(lattice, sym)

    for y in range(N):
        for x in range(M):
            if (y, x) in MINE_NUMBERS or (y, x) in NOT_MINES:
                sg.solver.add(Not(sg.cell_is(Point(y, x), sym.M)))
                if (y, x) in MINE_NUMBERS:
                    sg.solver.add(sg.grid[Point(y, x)] == MINE_NUMBERS[(y, x)])

            sg.solver.add(
                Implies(
                    Not(sg.cell_is(Point(y, x), sym.M)),
                    Sum([sl.count_cells(
                        sg,
                        Point(y, x),
                        d,
                        count=lambda c: c != sym.M,
                        stop=lambda c: c == sym.M,
                    ) for d in DIRECTIONS.values()]) == sg.grid[Point(y, x)] + 3
                )
            )

    mine_counts = [sg.cell_is(p, sym.M) for p in lattice.points]
    sg.solver.add(Sum(mine_counts) == MINE_AMOUNT)

    if sg.solve():
        sg.print()
        print_answer(sg)
        print()
        if sg.is_unique():
            print("Unique solution")
        else:
            print("Alternate solution")
            sg.print()
    else:
        print("No solution")


if __name__ == '__main__':
    main()
