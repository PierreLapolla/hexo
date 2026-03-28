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
- `game.legal_moves() -> tuple[Coord, ...]`: return legal single-move candidates.
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
from hexo import Hexo

game = Hexo.new()
print(game.turn())  # Player.P2

legal, reason = game.is_legal_move((1, 0))
if not legal:
    raise ValueError(reason)
game.push((1, 0))

# Hook point for engines: run a search after first placement.
# ... search code here ...

record = game.push((0, 1))  # turn completes here
print(record)  # TurnRecord
print(game.moves_left_in_turn())  # 2

state = game.to_state()
restored = Hexo.from_state(state)
print(restored.turn())
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
