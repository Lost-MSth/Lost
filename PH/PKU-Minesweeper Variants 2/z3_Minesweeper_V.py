import grilops
from grilops.geometry import Point, Vector
from z3 import *

N = 8
M = 8

# V 标准：普通扫雷

MINE_AMOUNT = 20
MINE_NUMBERS = {
    (0, 1): 1, (0, 2): 1,
    (1, 1): 2, (1, 3): 3, (1, 5): 2, (1, 7): 2,
    (2, 1): 3, (2, 3): 3, (2, 5): 2, (2, 6): 2,
    (3, 1): 2, (3, 3): 3, (3, 5): 2, (3, 7): 2,
    (4, 1): 3, (4, 2): 2,
    (5, 1): 4, (5, 4): 5, (5, 7): 3,
    (6, 1): 4, (6, 4): 4, (6, 7): 2,
    (7, 5): 2, (7, 6): 1,
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
                print(' x', end='')
                count += 1
            else:
                print(f'{m.eval(sg.grid[p]).as_long():2}', end='')
        print(f'   | {count}')


def main():
    sym = grilops.make_number_range_symbol_set(0, 8)
    sym.append('M', 'x')
    lattice = grilops.get_rectangle_lattice(N, M)
    sg = grilops.SymbolGrid(lattice, sym)

    for y in range(N):
        for x in range(M):
            if (y, x) in MINE_NUMBERS or (y, x) in NOT_MINES:
                sg.solver.add(Not(sg.cell_is(Point(y, x), sym.M)))
                if (y, x) in MINE_NUMBERS:
                    sg.solver.add(sg.grid[Point(y, x)] == MINE_NUMBERS[(y, x)])

            term = []
            for p in sg.vertex_sharing_neighbors(Point(y, x)):
                term.append(
                    If(p.symbol == sym.M, 1, 0)
                )

            sg.solver.add(
                Implies(
                    Not(sg.cell_is(Point(y, x), sym.M)),
                    Sum(term) == sg.grid[Point(y, x)]
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
