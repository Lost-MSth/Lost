"""Contains CompassProblemBuilder class"""
import logging
from typing import Dict, List, Tuple, Union

import z3

from .problem import CompassProblem
from .util import (
    CardinalDirection,
    Coord2D,
    DIRECTION_MAP,
    add_coords,
    get_direction_cells,
    in_bounds,
)

MODULE_LOGGER = logging.getLogger(__name__)


class Compass:
    """Contains information for single compass cell in the compass sudoku problem"""

    position: Coord2D
    _info: Dict[CardinalDirection, int]

    def __init__(
        self, position: Coord2D, info: Union[Dict[CardinalDirection, int], List[int]]
    ):
        self.position = position
        self.info = info

    @property
    def info(self) -> Dict[CardinalDirection, int]:
        """Returns the information this compass provides for the different directions"""
        return self._info

    @info.setter
    def info(self, infos: Union[Dict[CardinalDirection, int], List[int]]) -> None:
        if isinstance(infos, list):
            self._info = {}
            assert len(infos) == 4
            for direction, amount in zip(CardinalDirection, infos):
                if amount >= 0:
                    self._info[direction] = amount
            infos = self._info
        elif isinstance(infos, dict):
            self._info = infos
        else:
            raise TypeError("Unknown type in override function")


def build_compass_problem(
    dimensions: Coord2D, compasses: List[Compass]
) -> CompassProblem:
    """Build compass problem"""
    solver = CompassProblem()
    solver.dimensions = dimensions
    solver.solver = z3.Solver()
    _add_cell_clauses(solver, len(compasses))
    _add_connectivity_clauses(solver)
    for index, compass in enumerate(compasses):
        _add_compass(solver, compass, index)
    return solver


def _add_compass(solver: CompassProblem, compass: Compass, compass_id: int) -> None:
    """Add compass to field"""

    # count = z3.Int(f"compass_{compass_id}_count")

    solver.solver.add(solver.cells[compass.position] == compass_id)
    for direction, count in compass.info.items():
        cell_list = get_direction_cells(
            compass.position, solver.dimensions, direction)
        current_compass_counter = 0
        for index, cell_coord in enumerate(cell_list):
            last_compass_counter = current_compass_counter
            current_compass_counter = z3.Int(
                f"compass_{compass_id}_{direction.name}_[{index:02}]"
                f"_({cell_coord[0]},{cell_coord[1]})"
            )
            solver.solver.add(
                current_compass_counter
                == (
                    last_compass_counter
                    + z3.If(solver.cells[cell_coord] == compass_id, 1, 0)
                )
            )
        solver.solver.add(current_compass_counter == count)
    MODULE_LOGGER.debug("Added compass")


def _add_cell_clauses(solver: CompassProblem, compass_count: int) -> None:
    """Add cell clauses to compass problem"""
    x_dim, y_dim = solver.dimensions
    solver.cells = {
        (x, y): z3.Int(f"cell_({x},{y})")
        for x in range(x_dim) for y in range(y_dim)
        if (x, y) != (2, 6)  # Note: (2, 6) is not in bound
    }
    MODULE_LOGGER.debug("Created cell variables")

    for cell in solver.cells.values():
        solver.solver.add(cell >= 0)
        solver.solver.add(cell < compass_count)
    MODULE_LOGGER.debug("Created cell constraints")


def _add_connectivity_clauses(solver: CompassProblem) -> None:
    """Add connectivity clauses to compass problem"""
    x_dim, y_dim = solver.dimensions

    connectivity = {
        ((x1, y1), (x2, y2)): z3.Int(f"conn_({x1},{y1})->({x2}_{y2})")
        for x1 in range(x_dim)
        for y1 in range(y_dim)
        for x2 in range(x_dim)
        for y2 in range(y_dim)
        if (y2 > y1 or (y2 == y1 and x2 > x1))
        and (x1, y1) != (2, 6) and (x2, y2) != (2, 6)
    }
    MODULE_LOGGER.debug("Created connectivity variables")

    def get_conn_index(c1: Coord2D, c2: Coord2D) -> Tuple[Coord2D, Coord2D]:
        if c2[1] > c1[1] or (c2[1] == c1[1] and c2[0] > c1[0]):
            return (c1, c2)
        return (c2, c1)

    for (c1, c2), conn in connectivity.items():
        distance = abs(c2[0] - c1[0]) + abs(c2[1] - c1[1])
        assert distance > 0
        solver.solver.add(
            (solver.cells[c1] != solver.cells[c2]) == (conn == -1))
        if distance == 1:
            solver.solver.add(
                (solver.cells[c1] == solver.cells[c2]) == (conn == 1))
        if distance > 1:
            solver.solver.add(
                (solver.cells[c1] == solver.cells[c2]) == (conn > 1))
            neighbors = []
            for direction_vector in DIRECTION_MAP.values():
                new_cell = add_coords(c2, direction_vector)
                if in_bounds(new_cell, solver.dimensions) and new_cell != (2, 6):
                    neighbors.append(
                        connectivity[get_conn_index(c1, new_cell)])
            assert len(neighbors) >= 2
            solver.solver.add(
                z3.Implies(conn > 1, z3.Or(
                    [x == conn - 1 for x in neighbors]),)
            )
    MODULE_LOGGER.debug("Created connectivity constraints")
