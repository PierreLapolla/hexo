from __future__ import annotations

from hexo.types import Coord


class HexoError(Exception):
    """
    Represent the base exception for all Hexo engine failures.

    This exception is used as the root class for domain-specific errors raised
    by the package so callers can catch all Hexo-related exceptions with one type.
    """


class IllegalMoveError(HexoError):
    """
    Signal that a move violates Hexo game rules.

    This exception is raised when validation fails during state reconstruction,
    move application, or other rule-checked operations.
    """


STATE_INVALID_MOVE = (
    "state contains invalid move; each move must have exactly two integers"
)
GAME_IS_OVER = "game is over"
INVALID_COORDINATE = "move must be an axial coordinate (q, r)"
NO_MOVE_TO_UNDO = "cannot undo: no move has been played"
ILLEGAL_MOVE = "illegal move"


def occupied_cell(coord: Coord) -> str:
    """
    Return an "occupied cell" validation message for one coordinate.
    """
    return f"occupied cell: {coord}"


def move_out_of_radius(coord: Coord, radius: int) -> str:
    """
    Return a distance-rule violation message for one coordinate.
    """
    return f"move {coord} has no occupied cell within distance <= {radius}"
