"""
Expose the public API for the Hexo engine package.

This module re-exports the primary engine types so users can import them
directly from `hexo` instead of internal modules.
"""

from hexo.engine import Hexo
from hexo.errors import IllegalMoveError
from hexo.types import EngineConfig, GameStatus, MoveRecord, Player

__all__ = [
    "EngineConfig",
    "GameStatus",
    "Hexo",
    "IllegalMoveError",
    "MoveRecord",
    "Player",
]
