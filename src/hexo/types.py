"""
Provide core type definitions used by the Hexo engine.

This module centralizes enums, coordinate aliases, and immutable records that
describe game configuration and move history.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

Coord = tuple[int, int]
"""Represent an axial hex-grid coordinate as `(q, r)` integers."""

State = dict[str, Any]
"""Represent a serialized Hexo game state."""

AXES: tuple[Coord, ...] = ((1, 0), (0, 1), (1, -1))
"""Define the three principal axes used for straight-line win detection."""


class Player(Enum):
    """
    Identify one of the two players in a Hexo game.
    """

    P1 = auto()
    P2 = auto()

    @property
    def opponent(self) -> Player:
        """
        Return the opponent of the current player.

        :return:
            `Player.P2` when called on `Player.P1`, otherwise `Player.P1`.
        """
        return Player.P1 if self is Player.P2 else Player.P2


class GameStatus(Enum):
    """
    Describe the global game state from a terminal-condition perspective.
    """

    ONGOING = auto()
    P1_WON = auto()
    P2_WON = auto()


@dataclass(frozen=True, slots=True)
class EngineConfig:
    """
    Store immutable configuration values for a Hexo game instance.

    :param win_length:
        Number of aligned stones required for a win.
    :param placement_radius:
        Maximum hex distance from an occupied cell allowed for a new placement.
    :param opening_center:
        Fixed coordinate of the pre-placed opening stone for `P1`.
    """

    win_length: int = 6
    placement_radius: int = 8
    opening_center: Coord = (0, 0)


@dataclass(frozen=True, slots=True)
class MoveRecord:
    """
    Record one executed move (one stone placement).

    :param player:
        Player who placed the stone.
    :param move:
        Coordinate that was placed.
    :param won:
        Whether this move produced a winning line for `player`.
    """

    player: Player
    move: Coord
    won: bool


UndoSnapshot = tuple[
    Coord,
    Player,
    Player | None,
    int,
    bool,
    list[Coord],
]
"""
Capture all state required to undo one `push` operation.

Fields:
- pushed coordinate
- previous player to move
- previous winner
- previous turn-progress (moves already played in current turn)
- whether pushed coordinate was removed from legal cache
- coordinates newly added to legal cache by the push
"""
