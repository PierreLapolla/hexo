"""
Expose the public API for the Hexo engine package.

This module configures package-level logging and re-exports the primary engine
types so users can import them directly from `hexo` instead of internal modules.
"""

import logging
from pedros.logger import setup_logging

from hexo.engine import Hexo
from hexo.errors import HexoError, IllegalTurnError
from hexo.geometry import hex_distance
from hexo.types import AXES, Coord, EngineConfig, GameStatus, Player, State, TurnRecord

setup_logging(level=logging.INFO)

__all__ = [
    "Coord",
    "EngineConfig",
    "GameStatus",
    "Hexo",
    "HexoError",
    "IllegalTurnError",
    "AXES",
    "Player",
    "State",
    "TurnRecord",
    "hex_distance",
]
