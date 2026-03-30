![Ruff](https://img.shields.io/badge/ruff-enabled-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

# Hexo Engine

Hexo is a Python engine for the Hexo game played on an infinite hex grid.

The goal of this repository is to provide a clean, reusable engine API (similar in spirit to `python-chess`) so others can build bots, analysis tools, and frontends without re-implementing game logic.

Game rules are documented in [RULES.md](RULES.md).
Agent handoff context is documented in [AGENT_CONTEXT.md](AGENT_CONTEXT.md).

## Features

- Deterministic game engine with strict rule validation
- Infinite hex-grid coordinate model
- Opening and turn rules enforced by the engine
- Win detection (connect 6 on any hex axis)
- Undo support for search algorithms

## Installation

### Requirements

- [UV](https://docs.astral.sh/uv/) package manager

### Clone the repository

```bash
  git clone https://github.com/<your-org>/hexo.git
  cd hexo
```

### Initialize your environment

```bash
  uv sync
  uv run pre-commit install
```

## API

Public entry point is the `Hexo` class.

- `Hexo.new(config=None) -> Hexo`: create a new game with `P1` already placed at `(0, 0)`.
- `Hexo.from_state(state, config=None) -> Hexo`: restore a game from serialized state.
- `game.to_state() -> dict`: serialize committed turns and any in-progress partial turn.
- `game.turn() -> Player`: return the player currently placing stones.
- `game.status() -> GameStatus`: return `ONGOING`, `P1_WON`, or `P2_WON`.
- `game.moves_left_in_turn() -> int`: return remaining moves in current turn (`2` or `1`).
- `game.pending_moves() -> tuple[Coord, ...]`: return moves already made in the current turn.
- `game.is_legal_move(coord) -> tuple[bool, str | None]`: validate one submove.
- `game.legal_moves -> Collection[Coord]`: property that returns legal single-move candidates as a live iterable view.
- `game.push(coord) -> TurnRecord | None`: play one move; returns `None` if turn is still partial, or `TurnRecord` when the turn completes (or wins early).
- `game.is_legal(move) -> tuple[bool, str | None]`: validate a full 2-stone move (only when no partial turn is active).
- `game.play(move) -> TurnRecord`: convenience wrapper that places two stones in sequence.
- `game.undo() -> TurnRecord`: undo the last placement (works for both partial and completed turns).
- `game.at(coord) -> Player | None`: inspect occupancy at a coordinate.
- `game.board() -> dict[Coord, Player]`: get a snapshot of all occupied coordinates.

Notes:

- `Hexo.new()` starts with `P1` already placed at `(0, 0)`.
- Every played turn is a 2-stone move.

## Quickstart

```python
from hexo import GameStatus, Hexo


def move_key(coord: tuple[int, int]) -> tuple[int, int, int]:
    # Deterministic "closest to center" move ordering.
    return (
        abs(coord[0]) + abs(coord[1]) + abs(coord[0] + coord[1]),
        coord[0],
        coord[1],
    )


def play_turn(game: Hexo):
    first = min(game.legal_moves, key=move_key)
    record = game.push(first)
    if record is not None:  # win can happen on first placement
        return record

    second = min(game.legal_moves, key=move_key)
    return game.push(second)


game = Hexo.new()  # P1 center stone is pre-applied at (0, 0)

for turn_no in range(1, 6):
    if game.status() is not GameStatus.ONGOING:
        break
    record = play_turn(game)
    print(f"turn {turn_no}: {record.player.name} {record.placements} won={record.won}")

print("stones on board:", len(game.board()))
print("next player:", game.turn().name)

# Useful for bot search trees: snapshot, restore, undo
snapshot = game.to_state()
restored = Hexo.from_state(snapshot)
affected = restored.undo()
print("undo affected turn:", affected)
```

## Tests, linting and formatting

```bash
uv run pytest
```

```bash
uvx ruff check . --fix
```

```bash
uvx ruff format .
```

Run all hooks manually:

```bash
uv run pre-commit run --all-files
```

## Benchmarks

Benchmarking uses `pytest-benchmark` and is kept separate from normal tests.

Run benchmarks:

```bash
uv run pytest benchmarks --benchmark-only
```

Save a baseline:

```bash
uv run pytest benchmarks --benchmark-only --benchmark-save=baseline
```

Compare with a saved baseline:

```bash
uv run pytest benchmarks --benchmark-only --benchmark-compare=baseline
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- issue reporting guidelines
- feature proposal flow
- pull request requirements
- code style and testing expectations

## License

This project is licensed under the MIT [LICENSE](LICENSE)
