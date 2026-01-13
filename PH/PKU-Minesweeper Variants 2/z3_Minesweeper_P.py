import grilops
from grilops.geometry import Point, Vector
from z3 import *

N = 8
M = 8

# P 划分：线索表示周围八格内的连续雷组数

MINE_AMOUNT = 26
MINE_NUMBERS = {
    (0, 0): 1, (0, 7): 1,
    (1, 1): 1, (1, 4): 1, (1, 6): 1,
    (2, 2): 1, (2, 3): 1, (2, 5): 1, (2, 7): 1,
    (3, 3): 1, (3, 6): 1,
    (4, 1): 1, (4, 2): 1, (4, 4): 1, (4, 5): 1,
    (5, 3): 1, (5, 7): 1,
    (6, 1): 1, (6, 6): 1,
    (7, 2): 1, (7, 5): 1,
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


# 计算 bit 转换到连续组数，注意循环
LOOKUP = {}
for bits in range(256):
    bit_list = [(bits >> i) & 1 for i in range(8)]
    group_count = 0
    in_group = False
    for b in bit_list:
        if b == 1:
            if not in_group:
                group_count += 1
                in_group = True
        else:
            in_group = False
    LOOKUP[bits] = group_count

# 处理循环的情况
for bits in range(256):
    bit_list = [(bits >> i) & 1 for i in range(8)]
    if bit_list[0] == 1 and bit_list[-1] == 1:
        # 合并首尾的连续组
        i = 0
        while i < 8 and bit_list[i] == 1:
            i += 1
        j = 7
        while j >= 0 and bit_list[j] == 1:
            j -= 1
        group_count = LOOKUP[bits] - 1
        LOOKUP[bits] = group_count

# for k, v in LOOKUP.items():
#     print(f'{k:08b}: {v}')

LOOKUP_ONE_OF = {v: [k for k, vv in LOOKUP.items() if vv == v]
                 for v in set(LOOKUP.values())}


def print_answer(sg: grilops.SymbolGrid):
    m = sg.solver.model()
    for y in range(N):
        count = 0
        for x in range(M):
            p = Point(y, x)
            if m.eval(sg.cell_is(p, sg.symbol_set.M)):
                print('   x', end='')
                count += 1
            else:
                # print(f'{m.eval(sg.grid[p]).as_long():4}', end='')
                num = m.eval(sg.grid[p]).as_long()
                print(f'{LOOKUP[num]:4}', end='')
        print(f'   | {count}')


def main():
    sym = grilops.make_number_range_symbol_set(0, 255)
    sym.append('M', 'x')
    lattice = grilops.get_rectangle_lattice(N, M)
    sg = grilops.SymbolGrid(lattice, sym)

    BIT_DIRECTIONS = [
        Vector(-1, -1), Vector(-1, 0), Vector(-1, 1),
        Vector(0, 1), Vector(1, 1), Vector(1, 0),
        Vector(1, -1), Vector(0, -1)
    ]

    for y in range(N):
        for x in range(M):
            if (y, x) in MINE_NUMBERS or (y, x) in NOT_MINES:
                sg.solver.add(Not(sg.cell_is(Point(y, x), sym.M)))
                if (y, x) in MINE_NUMBERS:
                    # sg.solver.add(sg.grid[Point(y, x)] == MINE_NUMBERS[(y, x)])
                    sg.solver.add(
                        sg.cell_is_one_of(
                            Point(y, x), LOOKUP_ONE_OF[MINE_NUMBERS[(y, x)]])
                    )

            term = []
            for i, d in enumerate(BIT_DIRECTIONS):
                new_p = Point(y, x).translate(d)
                if not new_p in lattice.points:
                    continue
                term.append(
                    If(sg.cell_is(new_p, sym.M), 1 << i, 0)
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
