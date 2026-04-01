![Ruff](https://img.shields.io/badge/ruff-enabled-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

# Hexo Engine

Hexo is a Python engine for the Hexo game played on an infinite hex grid.

The goal of this repository is to provide a clean, reusable engine API (similar in spirit to `python-chess`) so others can build bots, analysis tools, and frontends without re-implementing game logic.

Game rules are documented in [RULES.md](RULES.md).

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
- `game.to_state() -> dict`: serialize move history as `{"moves": [[q, r], ...]}`.
- `game.turn() -> Player`: return the player currently placing stones.
- `game.status() -> GameStatus`: return `ONGOING`, `P1_WON`, or `P2_WON`.
- `game.moves_left_in_turn() -> int`: return remaining moves in current turn (`2` or `1`).
- `game.is_legal(coord) -> tuple[bool, str | None]`: validate one move.
- `game.legal_moves -> Collection[Coord]`: property that returns legal single-move candidates as a live iterable view.
- `game.push(coord) -> MoveRecord`: play one stone placement.
- `game.undo() -> MoveRecord`: undo one move.
- `game.at(coord) -> Player | None`: inspect occupancy at a coordinate.
- `game.board() -> dict[Coord, Player]`: get a snapshot of all occupied coordinates.

Notes:

- `Hexo.new()` starts with `P1` already placed at `(0, 0)`.
- One engine move is exactly one stone placement.
- The engine still enforces Hexo turn rules: each player makes two consecutive moves before side-to-move switches.

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


def play_full_turn(game: Hexo):
    player = game.turn()
    records = []
    while game.status() is GameStatus.ONGOING and game.turn() is player:
        move = min(game.legal_moves, key=move_key)
        records.append(game.push(move))
    return records


game = Hexo.new()  # P1 center stone is pre-applied at (0, 0)

for turn_no in range(1, 6):
    if game.status() is not GameStatus.ONGOING:
        break
    records = play_full_turn(game)
    for record in records:
        print(f"turn {turn_no}: {record.player.name} {record.move} won={record.won}")

print("stones on board:", len(game.board()))
print("next player:", game.turn().name)

# Useful for bot search trees: snapshot, restore, undo
snapshot = game.to_state()
restored = Hexo.from_state(snapshot)
affected = restored.undo()
print("undo affected move:", affected)
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
