import grilops
from grilops.geometry import Point, Vector
from z3 import *

N = 8
M = 8

# W 数墙：线索表示周围八格内每组连续雷的长度。

MINE_AMOUNT = 23
MINE_NUMBERS = {
    (0, 0): '1', (0, 3): '4', (0, 5): '2',
    (1, 1): '12',
    (2, 2): '12', (2, 5): '6', (2, 7): '2',
    (3, 0): '2', (3, 3): '12',
    (4, 4): '12', (4, 7): '3',
    (5, 0): '3', (5, 5): '12',
    (6, 6): '12',
    (7, 0): '1', (7, 2): '2', (7, 7): '1',
}
NOT_MINES = [(0, 7), (5, 2), (7, 4)]

# print the puzzle
for i in range(N):
    for j in range(M):
        if (i, j) in MINE_NUMBERS:
            print(MINE_NUMBERS[(i, j)], end=' ')
        else:
            print('.', end=' ')
    print()
print()


# 计算 bit 转换到连续组数的查找表，注意循环
# 例子：bits = 0b11001101 -> 2 个连续组，长度为 2, 4，排序后 -> '24'
LOOKUP = {}
for bits in range(256):
    bit_list = [(bits >> i) & 1 for i in range(8)]
    groups = []
    count = 0
    for b in bit_list + [0]:
        if b == 1:
            count += 1
        else:
            if count > 0:
                groups.append(count)
                count = 0

    # 处理循环：如果首尾都是 1，需要合并
    if bit_list[0] == 1 and bit_list[-1] == 1 and len(groups) > 0:
        groups[0] += groups[-1]
        groups.pop()

    groups.sort()
    key = ''.join(str(g) for g in groups)
    LOOKUP[bits] = key

LOOKUP[0b00000000] = '0'  # 特例，无雷
LOOKUP[0b11111111] = '8'  # 特例，全部为雷

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
                print('    x', end='')
                count += 1
            else:
                # print(f'{m.eval(sg.grid[p]).as_long():4}', end='')
                num = m.eval(sg.grid[p]).as_long()
                print(LOOKUP[num].rjust(5), end='')
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
