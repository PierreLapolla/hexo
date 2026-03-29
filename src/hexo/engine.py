from __future__ import annotations

from collections.abc import Collection, Iterator, Sequence

from hexo.errors import IllegalTurnError
from hexo.geometry import hex_distance
from hexo.types import (
    AXES,
    Coord,
    EngineConfig,
    GameStatus,
    Player,
    State,
    TurnRecord,
    UndoSnapshot,
)


class LegalMovesView(Collection[Coord]):
    """
    Provide a lightweight live view over an engine's legal move set.

    :param engine:
        Engine instance whose legal moves should be exposed.
    """

    def __init__(self, engine: Hexo) -> None:
        """
        Initialize a legal moves view for one engine.

        :param engine:
            Engine instance whose legal move cache is accessed.
        """
        self._engine = engine

    def __iter__(self) -> Iterator[Coord]:
        """
        Iterate over current legal moves.

        :return:
            Iterator over legal coordinates.
        """
        if self._engine._winner is not None:
            return iter(())
        return iter(self._engine._legal_moves_cache)

    def __len__(self) -> int:
        """
        Return number of current legal moves.

        :return:
            Number of legal coordinates.
        """
        if self._engine._winner is not None:
            return 0
        return len(self._engine._legal_moves_cache)

    def __contains__(self, coord: object) -> bool:
        """
        Check membership in the legal move set.

        :param coord:
            Candidate coordinate object.
        :return:
            `True` if `coord` is a legal move.
        """
        if self._engine._winner is not None:
            return False
        return coord in self._engine._legal_moves_cache


class Hexo:
    """
    Single public API for Hexo.

    The opening stone for P1 is automatically placed at (0, 0) on init.

    :param config:
        Optional engine configuration. When omitted, defaults are used.
    """

    def __init__(self, config: EngineConfig | None = None) -> None:
        """
        Initialize a new Hexo game with the opening center pre-applied.

        :param config:
            Optional engine configuration. When omitted, defaults are used.
        """
        self.config = config or EngineConfig()
        self._board: dict[Coord, Player] = {self.config.opening_center: Player.P1}
        self._stones_by_player: dict[Player, set[Coord]] = {
            Player.P1: {self.config.opening_center},
            Player.P2: set(),
        }
        self._turn_history: list[TurnRecord] = []
        self._undo_stack: list[UndoSnapshot] = []
        self._pending: list[Coord] = []
        self._winner: Player | None = None
        self._to_move = Player.P2
        self._legal_moves_cache: set[Coord] = set()
        self._legal_moves_view = LegalMovesView(self)
        self._radius_offsets = self._build_radius_offsets(self.config.placement_radius)
        self._expand_legal_cache_from(self.config.opening_center)

    @classmethod
    def new(cls, config: EngineConfig | None = None) -> Hexo:
        """
        Create a new game instance.

        :param config:
            Optional engine configuration. When omitted, defaults are used.
        :return:
            A newly initialized `Hexo` game object.
        """
        return cls(config=config)

    @classmethod
    def from_state(cls, state: State, config: EngineConfig | None = None) -> Hexo:
        """
        Rebuild a game from serialized move history.

        :param state:
            Serialized state with `turns` and optional `pending` arrays.
        :param config:
            Optional engine configuration to use for validation.
        :return:
            A reconstructed `Hexo` game after replaying all serialized moves.
        """
        game = cls.new(config=config)
        for raw_turn in state.get("turns", []):
            if len(raw_turn) not in (1, 2):
                raise IllegalTurnError(
                    "state contains invalid turn size; each turn must have 1 or 2 coordinates"
                )
            for raw_coord in raw_turn:
                game.push((int(raw_coord[0]), int(raw_coord[1])))
        for raw_coord in state.get("pending", []):
            game.push((int(raw_coord[0]), int(raw_coord[1])))
        return game

    def to_state(self) -> State:
        """
        Serialize the current game into a portable dictionary representation.

        :return:
            A state dictionary containing replayable turn history and pending placements.
        """
        turns = [
            [[coord[0], coord[1]] for coord in record.placements]
            for record in self._turn_history
        ]
        pending = [[coord[0], coord[1]] for coord in self._pending]
        return {"turns": turns, "pending": pending}

    def turn(self) -> Player:
        """
        Return the player expected to move next.

        :return:
            The current side to move.
        """
        return self._to_move

    def moves_left_in_turn(self) -> int:
        """
        Return how many placements remain for the current player's turn.

        :return:
            Number of stones left to place in the current turn.
        """
        return 2 - len(self._pending)

    def pending_moves(self) -> tuple[Coord, ...]:
        """
        Return coordinates already placed in the current unfinished turn.

        :return:
            Tuple containing zero or one coordinates for the active turn.
        """
        return tuple(self._pending)

    def status(self) -> GameStatus:
        """
        Report whether the game is ongoing or won.

        :return:
            Current game status.
        """
        if self._winner is Player.P1:
            return GameStatus.P1_WON
        if self._winner is Player.P2:
            return GameStatus.P2_WON
        return GameStatus.ONGOING

    def is_legal(self, move: Sequence[Coord]) -> tuple[bool, str | None]:
        """
        Validate whether a two-stone turn is currently legal.

        :param move:
            Candidate move containing exactly two coordinates.
        :return:
            Tuple `(is_legal, reason)` where `reason` is `None` when legal.
        """
        if self._winner is not None:
            return False, "game is over"

        if self._pending:
            return False, "cannot play a full move while a partial turn is in progress"

        if len(move) != 2:
            return False, "each turn must place exactly 2 stones"

        a, b = move[0], move[1]
        if a == b:
            return False, "duplicate coordinates in same turn"
        if a in self._board:
            return False, f"occupied cell: {a}"
        if b in self._board:
            return False, f"occupied cell: {b}"
        if a not in self._legal_moves_cache:
            return (
                False,
                f"placement {a} has no occupied cell within distance <= {self.config.placement_radius}",
            )
        if (
            b not in self._legal_moves_cache
            and hex_distance(a, b) > self.config.placement_radius
        ):
            return (
                False,
                f"placement {b} has no occupied cell within distance <= {self.config.placement_radius}",
            )

        return True, None

    def is_legal_move(self, coord: Coord) -> tuple[bool, str | None]:
        """
        Validate a single placement for submove-based play.

        :param coord:
            Candidate coordinate to place for the current player.
        :return:
            Tuple `(is_legal, reason)` where `reason` is `None` when legal.
        """
        if self._winner is not None:
            return False, "game is over"
        if len(self._pending) >= 2:
            return False, "current turn already has two placements"
        if coord in self._board:
            return False, f"occupied cell: {coord}"
        if coord in self._legal_moves_cache:
            return True, None
        return (
            False,
            f"placement {coord} has no occupied cell within distance <= {self.config.placement_radius}",
        )

    def play(self, move: Sequence[Coord]) -> TurnRecord:
        """
        Apply a legal move and update game state.

        :param move:
            Sequence containing exactly two coordinates for the current player.
        :return:
            Immutable record describing the applied turn.
        """
        legal, reason = self.is_legal(move)
        if not legal:
            raise IllegalTurnError(reason or "illegal move")

        self.push(move[0])
        if self._winner is not None:
            return self._turn_history[-1]
        self.push(move[1])
        return self._turn_history[-1]

    def push(self, coord: Coord) -> TurnRecord | None:
        """
        Place one stone for the current player as a submove.

        This method enables search workflows that evaluate positions between the
        first and second placement of a turn.

        :param coord:
            Coordinate to place for the current player.
        :return:
            `TurnRecord` when a turn is completed (or wins early), otherwise `None`.
        """
        legal, reason = self.is_legal_move(coord)
        if not legal:
            raise IllegalTurnError(reason or "illegal placement")

        prev_to_move = self._to_move
        prev_winner = self._winner
        prev_pending = tuple(self._pending)
        prev_history_len = len(self._turn_history)
        removed_from_cache = coord in self._legal_moves_cache

        self._board[coord] = self._to_move
        self._stones_by_player[self._to_move].add(coord)
        self._legal_moves_cache.discard(coord)
        added_legal = self._expand_legal_cache_from(coord)
        self._pending.append(coord)
        self._undo_stack.append(
            (
                coord,
                prev_to_move,
                prev_winner,
                prev_pending,
                prev_history_len,
                removed_from_cache,
                tuple(added_legal),
            )
        )

        won = self._has_winning_line(self._to_move, (coord,))
        if won:
            record = TurnRecord(
                player=self._to_move, placements=tuple(self._pending), won=True
            )
            self._winner = self._to_move
            self._turn_history.append(record)
            self._pending.clear()
            return record

        if len(self._pending) == 2:
            record = TurnRecord(
                player=self._to_move, placements=tuple(self._pending), won=False
            )
            self._turn_history.append(record)
            self._pending.clear()
            self._to_move = self._to_move.opponent
            return record

        return None

    def undo(self) -> TurnRecord:
        """
        Revert the last applied placement.

        :return:
            Record of the affected turn before the undo.
        """
        if not self._undo_stack:
            raise IllegalTurnError("cannot undo: no placement has been played")

        affected = (
            self._turn_history[-1]
            if self._turn_history
            else TurnRecord(self._to_move, tuple(self._pending), False)
        )
        (
            coord,
            prev_to_move,
            prev_winner,
            prev_pending,
            prev_history_len,
            removed_from_cache,
            added_legal,
        ) = self._undo_stack.pop()
        self._board.pop(coord, None)
        self._stones_by_player[prev_to_move].discard(coord)
        self._to_move = prev_to_move
        self._winner = prev_winner
        self._pending = list(prev_pending)
        if removed_from_cache:
            self._legal_moves_cache.add(coord)
        for added in added_legal:
            self._legal_moves_cache.discard(added)
        if len(self._turn_history) > prev_history_len:
            self._turn_history = self._turn_history[:prev_history_len]
        return affected

    def at(self, coord: Coord) -> Player | None:
        """
        Return the occupant of a specific coordinate.

        :param coord:
            Coordinate to inspect.
        :return:
            Occupying player or `None` if the cell is empty.
        """
        return self._board.get(coord)

    def board(self) -> dict[Coord, Player]:
        """
        Return a snapshot of current board occupancy.

        :return:
            New dictionary mapping occupied coordinates to owning players.
        """
        return dict(self._board)

    @property
    def legal_moves(self) -> Collection[Coord]:
        """
        Return a live view of all currently legal single-move candidates.

        :return:
            Collection view of legal coordinates.
        """
        return self._legal_moves_view

    def _expand_legal_cache_from(self, anchor: Coord) -> set[Coord]:
        """
        Expand legal move cache from one occupied anchor coordinate.

        :param anchor:
            Occupied coordinate used to generate new reachable empty cells.
        :return:
            Coordinates that were newly introduced in the legal-move cache.
        """
        aq, ar = anchor
        added: set[Coord] = set()
        for dq, dr in self._radius_offsets:
            coord = (aq + dq, ar + dr)
            if coord in self._board:
                continue
            if coord not in self._legal_moves_cache:
                self._legal_moves_cache.add(coord)
                added.add(coord)
        return added

    @staticmethod
    def _build_radius_offsets(radius: int) -> tuple[Coord, ...]:
        """
        Build axial offsets for a hex disc of a given radius.

        :param radius:
            Radius in hex distance.
        :return:
            Tuple of `(dq, dr)` offsets within the radius.
        """
        offsets: list[Coord] = []
        for dq in range(-radius, radius + 1):
            dr_min = max(-radius, -dq - radius)
            dr_max = min(radius, -dq + radius)
            for dr in range(dr_min, dr_max + 1):
                offsets.append((dq, dr))
        return tuple(offsets)

    def _has_winning_line(self, player: Player, newly_placed: Sequence[Coord]) -> bool:
        """
        Determine whether the latest move creates a winning alignment.

        :param player:
            Player whose board alignment should be evaluated.
        :param newly_placed:
            Two coordinates placed by `player` in the current turn.
        :return:
            `True` if the move creates a line meeting the win length.
        """
        needed = self.config.win_length
        player_cells = self._stones_by_player[player]
        for center in newly_placed:
            for axis in AXES:
                run = (
                    1
                    + self._count_direction(player_cells, center, axis)
                    + self._count_direction(player_cells, center, (-axis[0], -axis[1]))
                )
                if run >= needed:
                    return True
        return False

    @staticmethod
    def _count_direction(cells: set[Coord], origin: Coord, step: Coord) -> int:
        """
        Count contiguous stones in one direction from an origin.

        :param cells:
            Set of coordinates occupied by one player.
        :param origin:
            Starting coordinate for the directional scan.
        :param step:
            Axis step increment used for scanning.
        :return:
            Number of contiguous cells encountered along the direction.
        """
        count = 0
        cur = (origin[0] + step[0], origin[1] + step[1])
        while cur in cells:
            count += 1
            cur = (cur[0] + step[0], cur[1] + step[1])
        return count
