"""Contains CompassProblem class"""
from typing import Dict

import z3

from .util import Coord2D


class CompassSolution:
    """Solution to compass problem"""

    cells: Dict[Coord2D, int]
    dimensions: Coord2D

    def __repr__(self) -> str:
        return "\n".join(
            [f"{'x':>2} {'y':>2}  {'v':>2}"]
            + [f"{x:>2} {y:>2}: {region:>2}" for (x, y), region in self.cells.items()]
        )

    def table(self) -> str:
        """Return string representing the solution in an ASCII table"""
        result_rows = []
        for x in range(self.dimensions[0]):
            result_row = ""
            for y in range(self.dimensions[1]):
                if (x, y) not in self.cells:
                    result_row += " " * 3
                    continue
                result_row += f"{self.cells[(x, y)]:3}"
            result_rows.append(result_row)
        return "\n".join(result_rows)
    


class CompassProblem:
    """Wraps the compass sudoku problem"""

    cells: Dict[Coord2D, z3.Int]
    solver: z3.Solver
    dimensions: Coord2D

    def get_result(self) -> CompassSolution:
        """Get result for problem"""
        if self.solver.check() != z3.sat:
            return None

        my_model = self.solver.model()
        result_cells: Dict[Coord2D, int] = {}
        for index, expression in self.cells.items():
            result_cells[index] = my_model[expression].as_long()
        result = CompassSolution()
        result.cells = result_cells
        result.dimensions = self.dimensions
        return result
