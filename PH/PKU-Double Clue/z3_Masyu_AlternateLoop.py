# https://mp.weixin.qq.com/s/bctSnLgfaVjy5mWiiF-lzg

import sys

import grilops
import grilops.paths
from grilops.geometry import Point, Vector
from z3 import *

E, W, B = ".", chr(0x25e6), chr(0x2022)
GIVENS = [
    [E, E, E, E, E, E, E, E, E, E],
    [E, E, E, E, E, E, E, E, E, E],
    [E, E, B, E, B, E, W, E, E, E],
    [E, E, E, E, E, E, W, E, E, E],
    [E, E, E, B, E, E, E, E, E, E],
    [E, E, E, E, E, E, E, E, E, E],
    [W, E, W, E, E, E, E, W, E, E],
    [E, E, E, E, E, E, E, B, E, E],
    [E, W, E, E, E, B, B, E, E, E],
    [E, E, E, E, E, E, E, E, E, E],
]


def main():

    for row in GIVENS:
        for cell in row:
            sys.stdout.write(cell)
        print()

    lattice = grilops.get_rectangle_lattice(len(GIVENS), len(GIVENS[0]))
    sym = grilops.paths.PathSymbolSet(lattice)
    sym.append("EMPTY", " ")
    sg = grilops.SymbolGrid(lattice, sym)
    pc = grilops.paths.PathConstrainer(sg, allow_terminated_paths=False,
                                       complete=True)  # Alternate Loop 要求全经过
    sg.solver.add(pc.num_paths == 1)

    # Choose a non-empty cell to have loop order zero, to speed up solving.
    p = min(p for p in lattice.points if GIVENS[p.y][p.x] != E)
    sg.solver.add(pc.path_order_grid[p] == 0)

    # Masyu 规则，抄自官方例子
    straights = [sym.NS, sym.EW]
    turns = [sym.NE, sym.SE, sym.SW, sym.NW]

    for p in lattice.points:
        given = GIVENS[p.y][p.x]
        if given == B:
            # The loop must turn at a black circle.
            sg.solver.add(sg.cell_is_one_of(p, turns))

            # All connected adjacent cells must contain straight loop segments.
            for n in sg.edge_sharing_neighbors(p):
                if n.location.y < p.y:
                    sg.solver.add(Implies(
                        sg.cell_is_one_of(p, [sym.NE, sym.NW]),
                        sg.cell_is(n.location, sym.NS)
                    ))
                if n.location.y > p.y:
                    sg.solver.add(Implies(
                        sg.cell_is_one_of(p, [sym.SE, sym.SW]),
                        sg.cell_is(n.location, sym.NS)
                    ))
                if n.location.x < p.x:
                    sg.solver.add(Implies(
                        sg.cell_is_one_of(p, [sym.SW, sym.NW]),
                        sg.cell_is(n.location, sym.EW)
                    ))
                if n.location.x > p.x:
                    sg.solver.add(Implies(
                        sg.cell_is_one_of(p, [sym.NE, sym.SE]),
                        sg.cell_is(n.location, sym.EW)
                    ))
        elif given == W:
            # The loop must go straight through a white circle.
            sg.solver.add(sg.cell_is_one_of(p, straights))

            # At least one connected adjacent cell must turn.
            if 0 < p.y < len(GIVENS) - 1:
                sg.solver.add(Implies(
                    sg.cell_is(p, sym.NS),
                    Or(
                        sg.cell_is_one_of(p.translate(Vector(-1, 0)), turns),
                        sg.cell_is_one_of(p.translate(Vector(1, 0)), turns)
                    )
                ))
            if 0 < p.x < len(GIVENS[0]) - 1:
                sg.solver.add(Implies(
                    sg.cell_is(p, sym.EW),
                    Or(
                        sg.cell_is_one_of(p.translate(Vector(0, -1)), turns),
                        sg.cell_is_one_of(p.translate(Vector(0, 1)), turns)
                    )
                ))

    # Alternate Loop 规则：path 不能连续过两个同色圈
    blacks = [p for p in lattice.points if GIVENS[p.y][p.x] == B]
    whites = [p for p in lattice.points if GIVENS[p.y][p.x] == W]
    alls = blacks + whites

    def in_range(a, b, x):
        return Or(
            And(x > a, x < b),
            And(x > b, x < a)
        )

    for p1 in blacks:
        for p2 in whites:
            # 黑与白之间不能只有一个
            i1 = pc.path_order_grid[p1]
            i2 = pc.path_order_grid[p2]
            sg.solver.add(
                Sum(
                    [If(in_range(i1, i2, pc.path_order_grid[p]), 1, 0)
                        for p in alls]
                ) % 2 == 0
            )

    def print_order_of_circle(sg, pc):
        model = sg.solver.model()
        orders = []
        for p in whites:
            orders.append((model.eval(pc.path_order_grid[p]).as_long(), 'W'))
        for p in blacks:
            orders.append((model.eval(pc.path_order_grid[p]).as_long(), 'B'))
        sorted_orders = sorted(orders, key=lambda x: x[0])
        for (i, color) in sorted_orders:
            print(f"{color}{i}", end=" ")
        print()

    def print_turns(sg, pc, y=2):
        # 打印第 y 行的拐弯情况
        model = sg.solver.model()
        for x in range(len(GIVENS[0])):
            p = Point(y, x)
            b = model.eval(sg.cell_is_one_of(p, turns))
            print(2 if b else 1, end=" ")
        print()

    if sg.solve():
        sg.print()
        # pc.print_path_numbering()
        print()
        print_order_of_circle(sg, pc)
        print_turns(sg, pc)
        if sg.is_unique():
            print("Unique solution")
        else:
            print("Alternate solution")
            sg.print()
            print_order_of_circle(sg, pc)

    else:
        print("No solution")


if __name__ == "__main__":
    main()
