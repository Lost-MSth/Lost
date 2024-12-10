"""
Solve championship compass sudoku puzzle
https://cracking-the-cryptic.web.app/sudoku/P68BrQPTp7

Known solution:
  7  7  7  7  7  7  7  7  7
  7  5  0  2  4  4  4  4  7
  7  5  0  2  4  3  1  4  7
  7  5  2  2  4  3  1  1  7
  7  5  2  4  4  6  6  1  7
  7  5  5  5  4  6  8  1  7
  7  7  7  4  4  6  8  1  7
  7  7  4  4  6  6  1  1  7
  7  7  7  6  6  6  1  1  7
"""
import logging

from compasssudoku.builder import Compass, build_compass_problem
import compasssudoku.builder


def main(N: int) -> None:
    """Main function"""
    logging.basicConfig(
        format="%(asctime)s %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=logging.DEBUG,
    )
    compasssudoku.builder.MODULE_LOGGER.setLevel(logging.DEBUG)

    # Note: (2, 6) is not in bound

    my_problem = build_compass_problem(
        (9, 9),
        [
            Compass((1, 1), [N, N, N, N]),
            Compass((1, 7), [N, N, N, N]),
            Compass((3, 3), [N, N, N, N]),
            Compass((4, 5), [N, N, N, N]),
            Compass((6, 1), [N, N, N, N]),
            Compass((7, 4), [N, N, N, N]),
            Compass((7, 7), [N, N, N, N]),
        ],
    )
    my_problem.solver.add(
        my_problem.cells[(7, 3)] == my_problem.cells[(7, 5)]  # symmetry
    )
    print("Solving...")
    my_result = my_problem.get_result()
    if my_result is None:
        print(f"No solution found in N={N}")
        return
    ans = my_result.table()
    print(ans)
    for i in range(7):
        print(f'compass_{i}: {ans.count(str(i))}')


if __name__ == "__main__":
    # 7*4*3 > 9*9-1, so start from 3
    # second row has two compass, N < 9/2, so end at 4
    # N=4 is ok
    for i in range(3, 5):
        main(i)
