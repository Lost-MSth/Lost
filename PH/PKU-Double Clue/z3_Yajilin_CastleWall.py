# https://mp.weixin.qq.com/s/yrVWMCtkk8UinjYttKhFyA

import sys

import grilops
import grilops.paths
import grilops.sightlines
from grilops import Point
from z3 import *

U, R, D, L = chr(0x25B4), chr(0x25B8), chr(0x25BE), chr(0x25C2)
HEIGHT, WIDTH = 10, 10
GIVENS = {
    (0, 8): (L, 3),
    (1, 3): (D, 2),
    (1, 5): (U, 0),
    (3, 0): (D, 2),
    (4, 2): (R, 2),
    (5, 3): (R, 2),
    (6, 6): (U, 2),
    (7, 5): (L, 2),
    (7, 7): (U, 2),
    (8, 6): (L, 2),
}
GRAYS = [
    (6, 4),
    (8, 9),
]


def print_clues():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (y, x) in GIVENS:
                direction, count = GIVENS[(y, x)]
                sys.stdout.write(str(count))
                sys.stdout.write(direction)
                sys.stdout.write(" ")
            elif (y, x) in GRAYS:
                sys.stdout.write(" G ")
            else:
                sys.stdout.write(" . ")
        print()
    print()


def main():
    print_clues()

    lattice = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
    DIRECTIONS = {d.name: d for d in lattice.edge_sharing_directions()}
    N = DIRECTIONS["N"]
    E = DIRECTIONS["E"]
    S = DIRECTIONS["S"]
    W = DIRECTIONS["W"]
    sym = grilops.paths.PathSymbolSet(lattice)
    sym.append("BLACK", chr(0x25AE))
    sym.append("GRAY", chr(0x25AF))
    sym.append("INDICATIVE", " ")
    sg = grilops.SymbolGrid(lattice, sym)
    pc = grilops.paths.PathConstrainer(sg, allow_terminated_paths=False)
    sg.solver.add(pc.num_paths == 1)

    DIRECTION_SEGMENT_SYMBOLS = {
        N: [sym.NS, sym.NE, sym.NW],
        E: [sym.EW, sym.NE, sym.SE],
        S: [sym.NS, sym.SE, sym.SW],
        W: [sym.EW, sym.SW, sym.NW],
    }

    for p in lattice.points:
        if p in GIVENS:
            sg.solver.add(sg.cell_is(p, sym.INDICATIVE))
        elif p in GRAYS:
            sg.solver.add(sg.cell_is(p, sym.GRAY))
        else:
            sg.solver.add(Not(sg.cell_is_one_of(
                p, [sym.INDICATIVE, sym.GRAY])))
            sg.solver.add(Implies(
                sg.cell_is(p, sym.BLACK),
                And(*[n.symbol != sym.BLACK for n in sg.edge_sharing_neighbors(p)])
            ))

    for (sy, sx), (direction, count) in GIVENS.items():
        if direction == U:
            cells = [(y, sx) for y in range(sy)]
        elif direction == R:
            cells = [(sy, x) for x in range(sx + 1, WIDTH)]
        elif direction == D:
            cells = [(y, sx) for y in range(sy + 1, HEIGHT)]
        elif direction == L:
            cells = [(sy, x) for x in range(sx)]
        sg.solver.add(
            PbEq(
                [(sg.cell_is(Point(y, x), sym.BLACK), 1) for (y, x) in cells],
                count
            )
        )

        if direction == U:
            dd = N
        elif direction == R:
            dd = E
        elif direction == D:
            dd = S
        elif direction == L:
            dd = W
        else:
            raise ValueError(f"Unknown direction: {direction}")

        seg_syms = DIRECTION_SEGMENT_SYMBOLS[dd]
        actual_count = grilops.sightlines.count_cells(
            sg, Point(sy, sx), dd,
            lambda c, ss=seg_syms: If(Or(*[c == s for s in ss]), 1, 0)
        )
        sg.solver.add(actual_count == count)

    def print_grid():
        sg.print(lambda p, _: GIVENS[(p.y, p.x)][0]
                 if (p.y, p.x) in GIVENS else None)

    if sg.solve():
        print_grid()
        print()
        if sg.is_unique():
            print("Unique solution")
        else:
            print("Alternate solution")
            print_grid()
    else:
        print("No solution")


if __name__ == "__main__":
    main()
