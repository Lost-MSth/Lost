# https://mp.weixin.qq.com/s/My46Vp3h7oLWaBCo9hFsNA

from time import time

import grilops
import grilops.regions
from grilops import Point
from z3 import *

WIDTH = 11
HEIGHT = 11

WHITES = {
    Point(0, 0): 1,
    Point(3, 5): 5,
    Point(5, 0): 3, Point(5, 9): 4,
    Point(6, 1): 2,
    Point(9, 4): 4,
    Point(10, 10): 1,
    Point(5, 5): 'Star',  # 星星，白色区域
}

BLACKS = {
    # 人工添加一个能一眼看出的黑色格子作为根
    Point(0, 1): None,
    # 再加几个能看出来的加快速度，这本应该属于 extra_rules
    Point(1, 0): None,
    Point(3, 1): None,
    Point(4, 5): None,
    Point(5, 1): None,
    Point(6, 0): None, Point(6, 5): None,
    Point(7, 0): None, Point(7, 2): None,
    Point(9, 10): None,
    Point(10, 9): None,
}


def print_grid():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = Point(y, x)
            if p in WHITES:
                if WHITES[p] is not None:
                    print(f"{WHITES[p]}", end=' ')
                else:
                    print(f"W", end=' ')
            elif p in BLACKS:
                print(f"B", end=' ')
            else:
                print(".", end=' ')
        print()


def print_black_row_nums(sg: grilops.SymbolGrid):
    m = sg.solver.model()
    for y in range(HEIGHT):
        s = 0
        for x in range(WIDTH):
            p = Point(y, x)
            b = m.eval(sg.grid[p])
            s += 1 if b else 0
        print(s, end=' ')
    print()


def constrain_adjacent_cells(sg, rc):
    """Different regions of the same color may not be orthogonally adjacent."""
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = Point(y, x)
            adjacent_cells = [n.symbol for n in sg.edge_sharing_neighbors(p)]
            adjacent_region_ids = [
                n.symbol for n in sg.lattice.edge_sharing_neighbors(rc.region_id_grid, p)
            ]
            for cell, region_id in zip(adjacent_cells, adjacent_region_ids):
                sg.solver.add(
                    # Implies(
                    #     sg.grid[p] == cell,
                    #     rc.region_id_grid[p] == region_id
                    # )
                    (sg.grid[p] == cell) == (rc.region_id_grid[p] == region_id)
                )


def create_solver_with_optimizations():
    """创建带有优化设置的求解器"""
    solver = Solver()
    # 优化求解器参数
    solver.set("threads", 4)  # 使用多线程
    # solver.set("sat.lookahead_simplify", True)
    # solver.set('sat.acce', True)
    # solver.set('MBQI', True)
    # solver.set('logic', 'QF_FD')
    return solver


def extra_rules(sg: grilops.SymbolGrid, rc: grilops.regions.RegionConstrainer, sym: grilops.SymbolSet):
    # 人肉添加的特殊规则，为了加快计算
    sg.solver.add(
        sg.cell_is(Point(4, 0), sym.W),
        PbEq([(sg.cell_is(Point(4, 1), sym.W), 1),
             (sg.cell_is(Point(3, 0), sym.W), 1)], 1),
        PbEq([(sg.cell_is(Point(6, 2), sym.W), 1),
             (sg.cell_is(Point(7, 1), sym.W), 1)], 1),

        # 最大的白色，也就是中间的星星区域，应该是个 X 形状，否则黑色四方块很容易在四个角落形成
        # 因为即是对称又要连通，所以这两个位置必须是黑色
        sg.cell_is(Point(1, 1), sym.B), sg.cell_is(Point(9, 9), sym.B),
        # 同样，另外两个角落必须也是黑色
        sg.cell_is(Point(0, 10), sym.B), sg.cell_is(Point(10, 0), sym.B),
        # 右上角的四块里面有一个白，但是肯定不是数字区域，那只能是有一个星星区域的白色，形状随之固定了
        sg.cell_is(Point(0, 9), sym.B), sg.cell_is(
            Point(1, 10), sym.B), sg.cell_is(Point(1, 9), sym.W),
        # 由于对称，左下角也一样
        sg.cell_is(Point(9, 0), sym.B), sg.cell_is(
            Point(10, 1), sym.B), sg.cell_is(Point(9, 1), sym.W),

        # 星星两边肯定是白，得伸出来
        sg.cell_is(Point(5, 4), sym.W), sg.cell_is(Point(5, 6), sym.W),
    )


class MySymbolGrid(grilops.SymbolGrid):
    def __init__(self, lattice, symbol_set, solver=None):
        super().__init__(lattice, symbol_set, solver)
        for p in lattice.points:
            v = Bool(f"sg-{grilops.SymbolGrid._instance_index}-{p.y}-{p.x}")
            self.grid[p] = v

    def cell_is(self, p: Point, value: int) -> BoolRef:
        assert value == 0 or value == 1
        return self.grid[p] if value == 1 else Not(self.grid[p])

    def print(self, hook_function=None):
        model = self.solver.model()
        label_width = max(len(s.label)
                          for s in self.symbol_set.symbols.values())

        def print_function(p: Point) -> str:
            cell = self.grid[p]
            i = model.eval(cell)
            i = 1 if i else 0
            label = None
            if hook_function is not None:
                label = hook_function(p, i)
            if label is None:
                label = f"{self.symbol_set.symbols[i].label:{label_width}}"
            return label

        self.lattice.print(print_function, " " * label_width)

    def is_unique(self) -> bool:
        model = self.solver.model()
        or_terms = []
        for cell in self.grid.values():
            or_terms.append(cell != model.eval(cell))
        self.solver.add(Or(*or_terms))
        result = self.solver.check()
        return result == unsat


def main():
    print_grid()
    sym = grilops.SymbolSet([('B', 'x'), ('W', '.')])
    la = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
    # sg = grilops.SymbolGrid(la, sym, solver=create_solver_with_optimizations())
    sg = MySymbolGrid(la, sym, solver=create_solver_with_optimizations())
    rc = grilops.regions.RegionConstrainer(
        la,
        solver=sg.solver,
        min_region_size=1,
        max_region_size=HEIGHT * WIDTH -
        sum(1 for v in WHITES.values() if v is not None or v == 'Star')
    )

    extra_rules(sg, rc, sym)

    for p, v in WHITES.items():
        sg.solver.add(
            sg.cell_is(p, sym.W),
        )
        if v is None or v == 'Star':
            continue
        sg.solver.add(
            rc.region_size_grid[p] == v,
        )

    for p, v in BLACKS.items():
        sg.solver.add(
            sg.cell_is(p, sym.B),
        )
        if v is None:
            continue
        sg.solver.add(
            rc.region_size_grid[p] == v,
        )

    # 黑区 只能各有一个
    black_point = min(BLACKS)
    black_root = la.point_to_index(black_point)

    # 星星是对称中心
    stars = [p for p, v in WHITES.items() if v == 'Star']

    for p in la.points:
        sg.solver.add(
            sg.cell_is(p, sym.B) == (rc.region_id_grid[p] == black_root)
        )
        if p != black_point:
            sg.solver.add(
                Implies(
                    sg.cell_is(p, sym.B),
                    rc.parent_grid[p] != grilops.regions.R
                )
            )
        else:
            sg.solver.add(
                rc.parent_grid[p] == grilops.regions.R
            )
        # 白色每个区必须有一个线索，也就是白色线索就是根，白色不是线索就不是根
        if p in WHITES:
            sg.solver.add(
                rc.parent_grid[p] == grilops.regions.R,
                rc.region_id_grid[p] == la.point_to_index(p)
            )
        else:
            sg.solver.add(
                Implies(sg.cell_is(p, sym.W),
                        rc.parent_grid[p] != grilops.regions.R)
            )

        for center in stars:
            region_id = la.point_to_index(center)
            partner = Point(center.y * 2 - p.y, center.x * 2 - p.x)
            sg.solver.add(
                (rc.region_id_grid[p] == region_id) ==
                (rc.region_id_grid[partner] == region_id)
            )

    # 禁止黑色 2*2
    for y in range(HEIGHT - 1):
        for x in range(WIDTH - 1):
            p1 = Point(y, x)
            p2 = Point(y + 1, x)
            p3 = Point(y, x + 1)
            p4 = Point(y + 1, x + 1)
            sg.solver.add(
                Not(And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B),
                        sg.cell_is(p3, sym.B), sg.cell_is(p4, sym.B)))
            )

    # 颜色相同连一起是一个区，不同则不是
    constrain_adjacent_cells(sg, rc)
    # for p in la.points:
    #     p1 = p
    #     for n in sg.edge_sharing_neighbors(p):
    #         p2 = n.location
    #         sg.solver.add(
    #             (rc.region_id_grid[p1] == rc.region_id_grid[p2]) ==
    #             Or(
    #                 And(sg.cell_is(p1, sym.W), sg.cell_is(p2, sym.W)),
    #                 And(sg.cell_is(p1, sym.B), sg.cell_is(p2, sym.B))
    #             )
    #         )

    start = time()

    if sg.solve():
        sg.print()
        print_black_row_nums(sg)
        print(f'Solved in {time() - start:.2f} seconds')
        print()
        if sg.is_unique():
            print("Unique solution")
            print(f"Solved in {time() - start:.2f} seconds")
        else:
            print("Alternate solution")
            print(f"Solved in {time() - start:.2f} seconds")
            sg.print()
    else:
        print("No solution")


if __name__ == "__main__":
    main()
