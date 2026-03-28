"""
Provide geometry helpers for the axial hex grid used by Hexo.
"""

from hexo.types import Coord


def hex_distance(a: Coord, b: Coord) -> int:
    """
    Compute hex-grid distance between two axial coordinates.

    :param a:
        First coordinate as `(q, r)`.
    :param b:
        Second coordinate as `(q, r)`.
    :return:
        Hex distance between `a` and `b`.
    """
    dq = a[0] - b[0]
    dr = a[1] - b[1]
    return (abs(dq) + abs(dr) + abs(dq + dr)) // 2
