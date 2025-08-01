# https://mp.weixin.qq.com/s/zpOM_THpVvkGRv5KFLSItw


import grilops
import grilops.regions
import grilops.sightlines
from grilops.geometry import Point
from z3 import *

HEIGHT, WIDTH = 10, 10

TYPES = {
    'A': [1],
    'B': [2],
    'C': [1, 2],
    'D': [1, 3],
    'E': [1, 2, 3],
    'F': [2, 4],
}

CLUES = {
    Point(0, 1): 'B',
    Point(0, 5): 'B',
    Point(0, 6): 'E',
    Point(0, 7): 'C',
    Point(0, 9): 'D',
    Point(2, 7): 'B',
    Point(3, 0): 'F',
    Point(4, 0): 'C',
    Point(4, 9): 'B',
    Point(5, 0): 'A',
    Point(5, 1): 'E',
    Point(5, 2): 'F',
    Point(6, 0): 'E',
    Point(7, 4): 'F',
    Point(8, 1): 'B',
    Point(8, 5): 'A',
    Point(9, 4): 'C',
    Point(9, 6): 'F',
}


def print_clues():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = Point(y, x)
            if p in CLUES:
                print(f"{CLUES[p]:2s}", end=' ')
            else:
                print(" .", end=' ')
        print()


def must_in_or_zero(s, clues: 'list'):
    f = [s == 0]
    for c in clues:
        f.append(s == c)
    return Or(*f)


def main():
    print_clues()
    # The grid symbols will be the region IDs from the region constrainer.
    sym = grilops.make_number_range_symbol_set(0, HEIGHT * WIDTH - 1)
    lattice = grilops.get_rectangle_lattice(HEIGHT, WIDTH)
    DIRECTIONS = {d.name: d for d in lattice.edge_sharing_directions()}
    sg = grilops.SymbolGrid(lattice, sym)
    rc = grilops.regions.RegionConstrainer(
        lattice, sg.solver,
    )
    for point in lattice.points:
        sg.solver.add(sg.cell_is(point, rc.region_id_grid[point]))

    # 因为每个区域只有一个数字格子，所以直接设为根
    for p in lattice.points:
        region_id = lattice.point_to_index(p)
        if p in CLUES:
            sg.solver.add(
                rc.region_id_grid[p] == region_id,
                rc.parent_grid[p] == grilops.regions.R
            )
        else:
            sg.solver.add(
                rc.parent_grid[p] != grilops.regions.R
            )

    # clue type
    CLUE_TYPES = {}
    for p, c in CLUES.items():
        if c not in CLUE_TYPES:
            CLUE_TYPES[c] = []
        CLUE_TYPES[c].append(p)

    # Nikoji 平移重合规则
    for p in lattice.points:
        or_terms = []
        for gs in CLUE_TYPES.values():
            for g in gs:
                region_id = lattice.point_to_index(g)
                and_terms = [rc.region_id_grid[p] == region_id]
                flag = False
                for g2 in gs:
                    if g == g2:
                        continue
                    region_id2 = lattice.point_to_index(g2)
                    partner = Point(g2.y + p.y - g.y, g2.x + p.x - g.x)
                    if lattice.point_to_index(partner) is None:
                        # 平移点溢出了，那么这个点不可能是这个 clue 的
                        flag = True
                        break
                    and_terms.append(rc.region_id_grid[partner] == region_id2)
                if flag:
                    continue
                or_terms.append(And(*and_terms))

        sg.solver.add(Or(*or_terms))

    # Lohkous 长宽规则
    for p, c in CLUES.items():
        clue = TYPES[c]
        region_id = lattice.point_to_index(p)
        and_terms = []
        for y in range(HEIGHT):
            for x in range(WIDTH):
                # 从这点开始，向 S 和 E 方向去看
                S_imply = True
                E_imply = True
                if y >= 1:
                    S_imply = rc.region_id_grid[Point(y - 1, x)] != region_id
                if x >= 1:
                    E_imply = rc.region_id_grid[Point(y, x - 1)] != region_id

                S_count = grilops.sightlines.count_cells(
                    sg, Point(y, x), DIRECTIONS['S'],
                    lambda c: If(c == region_id, 1, 0),
                    lambda c: c != region_id,
                )
                E_count = grilops.sightlines.count_cells(
                    sg, Point(y, x), DIRECTIONS['E'],
                    lambda c: If(c == region_id, 1, 0),
                    lambda c: c != region_id,
                )
                and_terms.append(
                    Implies(
                        S_imply,
                        must_in_or_zero(S_count, clue)
                    )
                )
                and_terms.append(
                    Implies(
                        E_imply,
                        must_in_or_zero(E_count, clue)
                    )
                )

        sg.solver.add(And(*and_terms))

    def show_cell(unused_loc, region_id):
        return CLUES[lattice.points[region_id]]

    if sg.solve():
        sg.print(show_cell)
        print()
        # 输出第七行面积
        model = sg.solver.model()
        for x in range(WIDTH):
            p = Point(6, x)
            size = model.eval(rc.region_size_grid[p]).as_long()
            print(f"{size:2d}", end=' ')
        print()
        # for point in lattice.points:
        #     print(f"{point}: {sg.solver.model()[sg.grid[point]]}")
        if sg.is_unique():
            print("Unique solution")
        else:
            print("Alternate solution")
            sg.print(show_cell)
    else:
        print("No solution")


if __name__ == "__main__":
    main()
