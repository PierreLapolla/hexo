from __future__ import annotations

from collections.abc import Sequence

from hexo.types import AXES, Coord, Player

AXIS_PAIRS: tuple[tuple[Coord, Coord], ...] = tuple(
    (axis, (-axis[0], -axis[1])) for axis in AXES
)


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
    aq, ar = a
    bq, br = b
    dq = aq - bq
    dr = ar - br
    return (abs(dq) + abs(dr) + abs(dq + dr)) // 2


def build_radius_offsets(radius: int) -> tuple[Coord, ...]:
    """
    Return all axial offsets within a hex-disc radius.
    """
    offsets: list[Coord] = []
    for dq in range(-radius, radius + 1):
        dr_min = max(-radius, -dq - radius)
        dr_max = min(radius, -dq + radius)
        for dr in range(dr_min, dr_max + 1):
            offsets.append((dq, dr))
    return tuple(offsets)


def expand_legal_cache_from(
    anchor: Coord,
    radius_offsets: Sequence[Coord],
    board: dict[Coord, Player],
    legal_moves_cache: set[Coord],
) -> list[Coord]:
    """
    Expand legal moves around one occupied anchor.

    Returns only the coordinates that were newly added to `legal_moves_cache`.
    """
    aq, ar = anchor
    added: list[Coord] = []
    for dq, dr in radius_offsets:
        candidate = (aq + dq, ar + dr)
        # In typical search positions, most neighborhood cells are already legal.
        if candidate in legal_moves_cache or candidate in board:
            continue
        legal_moves_cache.add(candidate)
        added.append(candidate)

    return added


def has_winning_line(
    player_cells: set[Coord], newly_placed: Sequence[Coord], win_length: int
) -> bool:
    """
    Check whether any newly placed stone completes a line of at least `win_length`.
    """
    for center in newly_placed:
        if has_winning_line_at(player_cells, center, win_length):
            return True
    return False


def has_winning_line_at(
    player_cells: set[Coord], center: Coord, win_length: int
) -> bool:
    """
    Check whether one anchor coordinate completes a line of at least `win_length`.
    """
    contains = player_cells.__contains__
    center_q, center_r = center
    for (fdq, fdr), (bdq, bdr) in AXIS_PAIRS:
        run = 1

        q = center_q + fdq
        r = center_r + fdr
        while contains((q, r)):
            run += 1
            q += fdq
            r += fdr
        if run >= win_length:
            return True

        q = center_q + bdq
        r = center_r + bdr
        while contains((q, r)):
            run += 1
            q += bdq
            r += bdr
        if run >= win_length:
            return True
    return False
