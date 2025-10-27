"""Masyu solver example.

Example puzzle can be found at https://en.wikipedia.org/wiki/Masyu.


NSPH #1 by Lost-MSth
"""

from time import time

import grilops
import grilops.paths
from grilops.geometry import Point, Vector
from z3 import And, Implies, Not, Or, PbEq

HEIGHT, WIDTH = 12, 12

START = (0, 0)
END = (11, 11)
BANNED = [
    (0, 1), (0, 11),
    (1, 11),
    (2, 0),
    (3, 0),
    (4, 11),
    (5, 11),
    (6, 0), (6, 8),
    (7, 2), (7, 8),
    (8, 11),
    (9, 1),
    (10, 1),
    (11, 7),
]


def special_constraint(sg, sg2, sym2):
    # 其它规则
    sg.solver.add(
        sg2.cell_is_one_of(Point(2, 3), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(2, 4), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(2, 5), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(3, 3), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(3, 4), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(3, 5), [sym2.B, sym2.W]),

        sg2.cell_is_one_of(Point(1, 8), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(1, 9), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(2, 8), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(2, 9), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(3, 8), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(3, 9), [sym2.B, sym2.W]),

        sg2.cell_is_one_of(Point(3, 6), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(3, 7), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(4, 6), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(4, 7), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(5, 6), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(5, 7), [sym2.B, sym2.W]),

        sg2.cell_is_one_of(Point(6, 3), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(6, 4), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(7, 3), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(7, 4), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(8, 3), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(8, 4), [sym2.B, sym2.W]),

        sg2.cell_is_one_of(Point(8, 7), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(8, 8), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(8, 9), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(9, 7), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(9, 8), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(9, 9), [sym2.B, sym2.W]),

        sg2.cell_is_one_of(Point(9, 3), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(9, 4), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(9, 5), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(10, 3), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(10, 4), [sym2.B, sym2.W]),
        sg2.cell_is_one_of(Point(10, 5), [sym2.B, sym2.W]),

        PbEq([(sg2.cell_is_one_of(Point(2, x), [sym2.B, sym2.W]), 1)
             for x in range(1, WIDTH)], 8),
        PbEq([(sg2.cell_is_one_of(Point(4, x), [sym2.B, sym2.W]), 1)
             for x in range(0, WIDTH - 1)], 7),
        PbEq([(sg2.cell_is_one_of(Point(5, x), [sym2.B, sym2.W]), 1)
             for x in range(0, WIDTH - 1)], 5),
        PbEq([(sg2.cell_is_one_of(Point(7, x), [sym2.B, sym2.W]), 1)
             for x in range(3, WIDTH)], 6),
        PbEq([(sg2.cell_is_one_of(Point(8, x), [sym2.B, sym2.W]), 1)
             for x in range(0, WIDTH - 1)], 9),
    )


def main():

    lattice = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
    sym = grilops.paths.PathSymbolSet(lattice)
    sym.append("EMPTY", " ")
    sym2 = grilops.symbols.SymbolSet([('E', '.'), ('B', '●'), ('W', '○')])
    sg = grilops.SymbolGrid(lattice, sym)
    sg2 = grilops.SymbolGrid(lattice, sym2, solver=sg.solver)
    pc = grilops.paths.PathConstrainer(
        sg,
        allow_terminated_paths=True,
        # complete=True,
        allow_loops=False
    )
    sg.solver.add(pc.num_paths == 1)
    sg.solver.add(pc.path_order_grid[START] == 0)
    sg.solver.add(pc.path_order_grid[END] == WIDTH * HEIGHT - 1 - len(BANNED))
    special_constraint(sg, sg2, sym2)

    straights = [sym.NS, sym.EW]
    turns = [sym.NE, sym.SE, sym.SW, sym.NW]

    for p in lattice.points:
        if p in BANNED:
            sg.solver.add(sg.cell_is(p, sym.EMPTY))
            sg2.solver.add(sg2.cell_is(p, sym2.E))
            continue
        sg.solver.add(Not(sg.cell_is(p, sym.EMPTY)))

        black_terms = []
        # The loop must turn at a black circle.
        black_terms.append(sg.cell_is_one_of(p, turns))

        # All connected adjacent cells must contain straight loop segments.
        for n in sg.edge_sharing_neighbors(p):
            if n.location.y < p.y:
                black_terms.append(Implies(
                    sg.cell_is_one_of(p, [sym.NE, sym.NW]),
                    sg.cell_is(n.location, sym.NS)
                ))
            if n.location.y > p.y:
                black_terms.append(Implies(
                    sg.cell_is_one_of(p, [sym.SE, sym.SW]),
                    sg.cell_is(n.location, sym.NS)
                ))
            if n.location.x < p.x:
                black_terms.append(Implies(
                    sg.cell_is_one_of(p, [sym.SW, sym.NW]),
                    sg.cell_is(n.location, sym.EW)
                ))
            if n.location.x > p.x:
                black_terms.append(Implies(
                    sg.cell_is_one_of(p, [sym.NE, sym.SE]),
                    sg.cell_is(n.location, sym.EW)
                ))
        sg2.solver.add(sg2.cell_is(p, sym2.B) == And(black_terms))

        white_terms = []
        # The loop must go straight through a white circle.
        white_terms.append(sg.cell_is_one_of(p, straights))

        # At least one connected adjacent cell must turn.
        if 0 < p.y < HEIGHT - 1:
            white_terms.append(Implies(
                sg.cell_is(p, sym.NS),
                Or(
                    sg.cell_is_one_of(p.translate(Vector(-1, 0)), turns),
                    sg.cell_is_one_of(p.translate(Vector(1, 0)), turns)
                )
            ))
        if 0 < p.x < WIDTH - 1:
            white_terms.append(Implies(
                sg.cell_is(p, sym.EW),
                Or(
                    sg.cell_is_one_of(p.translate(Vector(0, -1)), turns),
                    sg.cell_is_one_of(p.translate(Vector(0, 1)), turns)
                )
            ))
        sg2.solver.add(sg2.cell_is(p, sym2.W) == And(white_terms))

    start_time = time()
    print("Solving...")
    if sg.solve():
        sg.print()
        sg2.print()
        print()
        print(f"Solved in {time() - start_time:.3f} seconds")
        if sg.is_unique():
            print("Unique solution")
        else:
            print("Alternate solution")
            sg.print()
            sg2.print()
        print(f'Total solver time: {time() - start_time:.3f} seconds')
    else:
        print("No solution")


if __name__ == "__main__":
    main()
