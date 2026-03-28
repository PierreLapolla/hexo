# Hexo Rules (Engine Specification v0.1)

## 1. Board

- The board is an infinite hexagonal grid.
- Use integer axial coordinates `(q, r)` for positions.
- The center cell is `(0, 0)`.

## 2. Players

- Two players: `P1` and `P2`.
- `P1` plays first.

## 3. Opening and Turn Structure

- Opening placement is fixed:
  - `P1` starts with exactly one stone at `(0, 0)`.
- First reply:
  - `P2` places exactly two stones.
- From then on:
  - Each turn places exactly two stones.
- Both stones placed in the same turn must be on distinct empty cells.
- Engine convention used in this repository:
  - `Hexo.new()` pre-applies the opening stone `(0, 0)` for `P1`.
  - The first `play(...)` call is therefore `P2` placing 2 stones.

## 4. Legal Placement

A stone placement is legal only if all conditions hold:

- The target cell is empty.
- Distance constraint:
  - The new stone must be within hex distance `<= 8` from at least one already occupied cell on the board.

Hex distance for axial coordinates:

`hex_distance((q1, r1), (q2, r2)) = (|dq| + |dr| + |dq + dr|) / 2`

where `dq = q1 - q2` and `dr = r1 - r2`.

Because `P1` starts with `(0, 0)`, there is always at least one occupied cell before any free placement occurs.

## 5. Win Condition

- A player wins immediately when they have 6 stones in one straight line on any hex-grid axis.
- Valid line directions are the 3 principal axes:
  - `(1, 0)`
  - `(0, 1)`
  - `(1, -1)`
- Horizontal and both diagonal directions are included by these axes.
- A line of 6 or more stones counts as a win.

## 6. Game End

- The game ends as soon as a win condition is met.
- If both stones of a turn are placed and both create winning lines for the same player, the result is still a single win for that player.

## 7. Notes for Engine API

- Keep rule validation deterministic and side-effect free.
- Recommended checks for a turn:
  - Correct number of stones for that turn stage.
  - No duplicate cells in the move.
  - All cells empty.
  - Distance rule for each placed stone.
  - Win detection after applying the full turn.
