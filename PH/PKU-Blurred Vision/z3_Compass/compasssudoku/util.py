"""Contains utility"""
import enum
from typing import Tuple, List, Optional

Coord2D = Tuple[int, int]


class CardinalDirection(enum.Enum):
    """Cardinal directions"""

    north = enum.auto()
    east = enum.auto()
    south = enum.auto()
    west = enum.auto()


DIRECTION_MAP = {
    CardinalDirection.north: (0, -1),
    CardinalDirection.east: (1, 0),
    CardinalDirection.south: (0, 1),
    CardinalDirection.west: (-1, 0),
}
ORTHOGONAL_DIRECTION_MAP = {
    CardinalDirection.north: (1, 0),
    CardinalDirection.east: (0, 1),
    CardinalDirection.south: (-1, 0),
    CardinalDirection.west: (0, -1),
}


def in_bounds(cell: Coord2D, bounds: Coord2D) -> bool:
    """Check that coordinate is in [0, bounds)"""
    return cell[0] >= 0 and cell[0] < bounds[0] and cell[1] >= 0 and cell[1] < bounds[1]

def add_coords(summand1: Coord2D, summand2: Coord2D, bounds: Optional[Coord2D] = None) -> Coord2D:
    """Add two tuples"""
    result = (summand1[0] + summand2[0], summand1[1] + summand2[1])
    if bounds is not None:
        result = (result[0] % bounds[0], result[1] % bounds[1])
    return result


def get_direction_cells(
    origin: Coord2D, dimensions: Coord2D, direction: CardinalDirection
) -> List[Coord2D]:
    """List all cells in the given direction"""
    result = []
    current = add_coords(origin, DIRECTION_MAP[direction])
    while in_bounds(current, dimensions):
        if current != (2, 6):
            result.append(current)
        current = add_coords(
            current, ORTHOGONAL_DIRECTION_MAP[direction], dimensions)
        if current[0] == origin[0] or current[1] == origin[1]:
            current = add_coords(current, DIRECTION_MAP[direction])

    return result
