import time
from multiprocessing import Pool

from z3 import *

N = 10
M = 10

'''
Results on my computer (i7-13700KF):

len = 50, unsat in  155.0069510936737
len = 54, unsat in  469.2377362251282
len = 52, unsat in  313.6931788921356
len = 58, unsat in  1129.9667391777039
len = 56, unsat in  874.1088855266571
len = 62, unsat in  2686.0952541828156
len = 60, unsat in  2001.019581079483
len = 64, unsat in  4038.2118265628815
len = 66, unsat in  6790.132362604141
len = 68, unsat in  11274.9692132473
len = 70, unsat in  17300.010066986084
len = 74, unsat in  43690.05572223663
len = 72, unsat in  28566.13824224472
len = 78, unsat in  92086.5150771141
len = 76, unsat in  86107.08173251152
len = 86, unsat in  133143.11881375313
len = 82, unsat in  237573.35317206383
len = 80, sat in  163879.3654372692
1,2,3,13,23,24,25,26,16,15,14,4,5,6,7,17,18,19,29,39,38,28,27,37,47,48,49,59,69,79,78,88,98,97,96,86,87,77,67,66,65,64,63,73,83,84,85,95,94,93,92,82,81,80,70,60,61,62,52,42,43,44,54,55,56,46,36,35,34,33,32,31,41,51,50,40,30,20,21,11

 .   b1   w2    3    12  w13  w14   15   .    .
 .   w80   .   w4    11   10   9    16  w17  b18
 78   79   .   b5   w6   w7    8    23   22  w19
w77   72  w71   70   69   68  b67  w24   21   20
w76   73  b60   61   62   .   w66  b25  w26   27
 75   74  w59   .    63  w64   65   .    .   w28
 56  w57   58  b43   42   41  w40  b39   .   w29
w55   .    .   w44   .    .    .   w38   31   30
b54  w53   52  b45  w46   47   36   37  w32   .
 .    .    51  w50  w49   48   35  w34  b33   .

len = 90, unsat in  143784.2249069214
len = 88, unsat in  135377.26178717613
len = 94, unsat in  156887.71202254295
len = 92, unsat in  155498.47499227524
len = 98, unsat in  150654.56004929543
len = 84, unsat in  254824.76630306244
len = 96, unsat in  153534.07352995872
'''


BLACK_CIRCLE_XY = {
    (0, 1),
    (1, 9),
    (2, 3),
    (3, 6),
    (4, 2), (4, 7),
    (6, 3), (6, 7),
    (8, 0), (8, 3),
    (9, 8),
}


def white_blurred_vision(is_white_circle, s):

    # 每行三个
    for i in range(N):
        x = 0
        for j in range(M):
            x += If(is_white_circle[i][j], 1, 0)
        s.add(x == 3)

    # 每列三个
    for j in range(M):
        x = 0
        for i in range(N):
            x += If(is_white_circle[i][j], 1, 0)
        s.add(x == 3)


def special(s, path):
    # 固定一下开头和结尾
    s.add(path[0] == xy2idx(0, 1))
    s.add(path[1] == xy2idx(0, 2))
    s.add(path[2] == xy2idx(0, 3))
    s.add(path[-1] == xy2idx(1, 1))
    s.add(path[-2] == xy2idx(2, 1))


def idx2xy(idx):
    return idx / M, idx % M


def xy2idx(x, y):
    return x * M + y


def in_bound(x, y):
    return x >= 0 and x < N and y >= 0 and y < M


FOUR_DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def is_linked(path_num, path_len, x1, y1, x2, y2):
    return Or(
        path_num[x1][y1] - path_num[x2][y2] == 1,
        path_num[x2][y2] - path_num[x1][y1] == 1,
        And(path_num[x1][y1] == 1, path_num[x2][y2] == path_len),
        And(path_num[x2][y2] == 1, path_num[x1][y1] == path_len),
    )


def solve_one(path_len: int):
    print(f'path_len = {path_len}')

    path = IntVector('path', path_len)

    s = Solver()
    s.add(Distinct(path))

    for i in path:
        s.add(And(i >= 0, i < N * M))

    # path connected
    for i in range(path_len):
        x0, y0 = idx2xy(path[i])
        x1, y1 = idx2xy(path[(i + 1) % path_len])
        s.add(Or(
            And(x0 == x1, Or(y0 == y1 + 1, y0 == y1 - 1)),
            And(y0 == y1, Or(x0 == x1 + 1, x0 == x1 - 1))
        ))

    is_white_circle = [BoolVector(f'is_white_circle_{i}', M) for i in range(N)]
    for i in range(N):
        for j in range(M):
            if (i, j) in BLACK_CIRCLE_XY:
                s.add(is_white_circle[i][j] == False)

    white_blurred_vision(is_white_circle, s)

    path_num = [IntVector(f'is_path_{i}', M) for i in range(N)]
    for i in range(N):
        for j in range(M):
            f = 0
            for k in range(path_len):
                f += If(path[k] == xy2idx(i, j), k+1, 0)

            s.add(path_num[i][j] == f)

    # black circle 直角拐弯加直行一个格子
    for i, j in BLACK_CIRCLE_XY:
        f = False
        for k in range(4):
            x1, y1 = i + FOUR_DIRS[k][0], j + FOUR_DIRS[k][1]
            x2, y2 = i + FOUR_DIRS[(k + 1) % 4][0], j + \
                FOUR_DIRS[(k + 1) % 4][1]
            xx1, yy1 = x1 + FOUR_DIRS[k][0], y1 + FOUR_DIRS[k][1]
            xx2, yy2 = x2 + FOUR_DIRS[(k + 1) % 4][0], y2 + \
                FOUR_DIRS[(k + 1) % 4][1]
            if in_bound(x1, y1) and in_bound(x2, y2) and in_bound(xx1, yy1) and in_bound(xx2, yy2):
                f = Or(f, And(
                    is_linked(path_num, path_len, x1, y1, i, j),
                    is_linked(path_num, path_len, x2, y2, i, j),
                    is_linked(path_num, path_len, xx1, yy1, x1, y1),
                    is_linked(path_num, path_len, xx2, yy2, x2, y2),
                    path_num[x1][y1] > 0,
                    path_num[x2][y2] > 0,
                    path_num[xx1][yy1] > 0,
                    path_num[xx2][yy2] > 0,
                ))
        s.add(f)
        s.add(path_num[i][j] > 0)

    # white circle 直线通行一格后至少在一个地方拐弯
    for i in range(N):
        for j in range(M):
            if (i, j) in BLACK_CIRCLE_XY:
                continue

            f = False
            for k in range(4):
                x1, y1 = i + FOUR_DIRS[k][0], j + FOUR_DIRS[k][1]
                x2, y2 = i + FOUR_DIRS[(k + 2) %
                                       4][0], j + FOUR_DIRS[(k + 2) % 4][1]
                xx1, yy1 = x1 + FOUR_DIRS[k][0], y1 + FOUR_DIRS[k][1]
                xx2, yy2 = x2 + FOUR_DIRS[(k + 2) % 4][0], y2 + \
                    FOUR_DIRS[(k + 2) % 4][1]
                if in_bound(x1, y1) and in_bound(x2, y2):
                    if in_bound(xx1, yy1) and in_bound(xx2, yy2):
                        f = Or(f, And(
                            is_linked(path_num, path_len, x1, y1, i, j),
                            is_linked(path_num, path_len, x2, y2, i, j),
                            path_num[x1][y1] > 0,
                            path_num[x2][y2] > 0,
                            Or(
                                Not(is_linked(path_num, path_len, xx1, yy1, x1, y1)),
                                Not(is_linked(path_num, path_len, xx2, yy2, x2, y2)),
                                path_num[xx1][yy1] == 0,
                                path_num[xx2][yy2] == 0,
                            )
                        ))
                    else:
                        f = Or(f, And(
                            is_linked(path_num, path_len, x1, y1, i, j),
                            is_linked(path_num, path_len, x2, y2, i, j),
                            path_num[x1][y1] > 0,
                            path_num[x2][y2] > 0,
                        ))
            s.add(Implies(is_white_circle[i][j], f))
            s.add(Implies(is_white_circle[i][j], path_num[i][j] > 0))

    special(s, path)

    start = time.time()
    if s.check() == unsat:
        print(f'len = {path_len}, unsat in ', time.time() - start)
        print()
        return None
    print(f'len = {path_len}, sat in ', time.time() - start)

    m = s.model()
    print(','.join([str(m[path[i]]) for i in range(path_len)]))
    print()

    for i in range(N):
        for j in range(M):
            char = '.'
            x = m[path_num[i][j]].as_long()
            if x > 0:
                char = str(x)

            if (i, j) in BLACK_CIRCLE_XY:
                char = 'b' + char
            elif m[is_white_circle[i][j]]:
                char = 'w' + char
            else:
                char = ' ' + char

            print(char.ljust(4), end=' ')
        print()

    print()


def main():
    with Pool(4) as p:
        # start from 5 * 10 = 50
        # end with 10 * 10 = 100
        p.map(solve_one, range(50, 100, 2))


if __name__ == '__main__':
    main()
