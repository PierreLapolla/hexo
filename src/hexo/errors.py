from __future__ import annotations

from hexo.types import Coord


class HexoError(Exception):
    """
    Represent the base exception for all Hexo engine failures.

    This exception is used as the root class for domain-specific errors raised
    by the package so callers can catch all Hexo-related exceptions with one type.
    """


class IllegalTurnError(HexoError):
    """
    Signal that a move or turn violates Hexo game rules.

    This exception is raised when validation fails during state reconstruction,
    move application, or other rule-checked operations.
    """


STATE_INVALID_TURN_SIZE = (
    "state contains invalid turn size; each turn must have 1 or 2 coordinates"
)
GAME_IS_OVER = "game is over"
PARTIAL_TURN_IN_PROGRESS = "cannot play a full move while a partial turn is in progress"
TURN_MUST_PLACE_TWO = "each turn must place exactly 2 stones"
DUPLICATE_COORDINATES = "duplicate coordinates in same turn"
TURN_ALREADY_HAS_TWO = "current turn already has two placements"
NO_PLACEMENT_TO_UNDO = "cannot undo: no placement has been played"
ILLEGAL_MOVE = "illegal move"
ILLEGAL_PLACEMENT = "illegal placement"


def occupied_cell(coord: Coord) -> str:
    """
    Return an "occupied cell" validation message for one coordinate.
    """
    return f"occupied cell: {coord}"


def placement_out_of_radius(coord: Coord, radius: int) -> str:
    """
    Return a distance-rule violation message for one coordinate.
    """
    return f"placement {coord} has no occupied cell within distance <= {radius}"
