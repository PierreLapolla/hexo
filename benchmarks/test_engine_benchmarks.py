from __future__ import annotations

from hexo import Hexo

Coord = tuple[int, int]


def _coord_key(coord: Coord) -> tuple[int, int, int]:
    return (
        abs(coord[0]) + abs(coord[1]) + abs(coord[0] + coord[1]),
        coord[0],
        coord[1],
    )


def _build_position(plies: int = 80) -> Hexo:
    game = Hexo.new()
    for _ in range(plies):
        if game.status().name != "ONGOING":
            break
        legal = game.legal_moves
        if not legal:
            break
        game.push(min(legal, key=_coord_key))
    return game


def test_benchmark_legal_moves(benchmark) -> None:
    game = _build_position()
    benchmark(lambda: tuple(game.legal_moves))


def test_benchmark_is_legal_move(benchmark) -> None:
    game = Hexo.new()
    target = min(game.legal_moves, key=_coord_key)
    benchmark(lambda: game.is_legal_move(target))


def test_benchmark_push_undo_cycle(benchmark) -> None:
    game = Hexo.new()
    target = min(game.legal_moves, key=_coord_key)

    def _action() -> None:
        game.push(target)
        game.undo()

    benchmark(_action)


def test_benchmark_state_roundtrip(benchmark) -> None:
    game = _build_position()
    state = game.to_state()
    benchmark(lambda: Hexo.from_state(state))
