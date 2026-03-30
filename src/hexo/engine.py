from __future__ import annotations

from collections.abc import Collection, Iterator, Sequence

from hexo._engine_utils import (
    hex_distance,
    build_radius_offsets,
    expand_legal_cache_from,
    has_winning_line_at,
)
from hexo.errors import (
    DUPLICATE_COORDINATES,
    GAME_IS_OVER,
    ILLEGAL_MOVE,
    ILLEGAL_PLACEMENT,
    NO_PLACEMENT_TO_UNDO,
    PARTIAL_TURN_IN_PROGRESS,
    STATE_INVALID_TURN_SIZE,
    TURN_ALREADY_HAS_TWO,
    TURN_MUST_PLACE_TWO,
    IllegalTurnError,
    occupied_cell,
    placement_out_of_radius,
)
from hexo.types import (
    Coord,
    EngineConfig,
    GameStatus,
    Player,
    State,
    TurnRecord,
    UndoSnapshot,
)

SUBMOVES_PER_TURN = 2


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
        self._radius_offsets = build_radius_offsets(self.config.placement_radius)
        expand_legal_cache_from(
            self.config.opening_center,
            self._radius_offsets,
            self._board,
            self._legal_moves_cache,
        )

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
        push = game.push
        for raw_turn in state.get("turns", []):
            if len(raw_turn) not in (1, 2):
                raise IllegalTurnError(STATE_INVALID_TURN_SIZE)
            for raw_coord in raw_turn:
                push((int(raw_coord[0]), int(raw_coord[1])))
        for raw_coord in state.get("pending", []):
            push((int(raw_coord[0]), int(raw_coord[1])))
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
        return SUBMOVES_PER_TURN - len(self._pending)

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
            return False, GAME_IS_OVER

        if self._pending:
            return False, PARTIAL_TURN_IN_PROGRESS

        if len(move) != SUBMOVES_PER_TURN:
            return False, TURN_MUST_PLACE_TWO

        a, b = move[0], move[1]
        if a == b:
            return False, DUPLICATE_COORDINATES
        if a in self._board:
            return False, occupied_cell(a)
        if b in self._board:
            return False, occupied_cell(b)
        if a not in self._legal_moves_cache:
            return False, placement_out_of_radius(a, self.config.placement_radius)
        if (
            b not in self._legal_moves_cache
            and hex_distance(a, b) > self.config.placement_radius
        ):
            return False, placement_out_of_radius(b, self.config.placement_radius)

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
            return False, GAME_IS_OVER
        if len(self._pending) >= SUBMOVES_PER_TURN:
            return False, TURN_ALREADY_HAS_TWO
        if coord in self._legal_moves_cache:
            return True, None
        if coord in self._board:
            return False, occupied_cell(coord)
        return False, placement_out_of_radius(coord, self.config.placement_radius)

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
            raise IllegalTurnError(reason or ILLEGAL_MOVE)

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
            raise IllegalTurnError(reason or ILLEGAL_PLACEMENT)

        to_move = self._to_move
        prev_to_move = to_move
        prev_winner = self._winner
        prev_pending = tuple(self._pending)
        prev_history_len = len(self._turn_history)
        board = self._board
        legal_cache = self._legal_moves_cache
        removed_from_cache = coord in legal_cache

        board[coord] = to_move
        player_cells = self._stones_by_player[to_move]
        player_cells.add(coord)
        legal_cache.discard(coord)
        added_legal = expand_legal_cache_from(
            coord,
            self._radius_offsets,
            board,
            legal_cache,
        )
        self._pending.append(coord)
        self._undo_stack.append(
            (
                coord,
                prev_to_move,
                prev_winner,
                prev_pending,
                prev_history_len,
                removed_from_cache,
                added_legal,
            )
        )

        won = has_winning_line_at(player_cells, coord, self.config.win_length)
        if won:
            return self._finish_turn(won=True)

        if len(self._pending) == SUBMOVES_PER_TURN:
            return self._finish_turn(won=False)

        return None

    def undo(self) -> TurnRecord:
        """
        Revert the last applied placement.

        :return:
            Record of the affected turn before the undo.
        """
        if not self._undo_stack:
            raise IllegalTurnError(NO_PLACEMENT_TO_UNDO)

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
        self._pending.clear()
        self._pending.extend(prev_pending)
        if removed_from_cache:
            self._legal_moves_cache.add(coord)
        for added in added_legal:
            self._legal_moves_cache.discard(added)
        if len(self._turn_history) > prev_history_len:
            self._turn_history.pop()
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

    def _finish_turn(self, won: bool) -> TurnRecord:
        """
        Finalize the current turn, updating history and turn ownership.
        """
        record = TurnRecord(
            player=self._to_move,
            placements=tuple(self._pending),
            won=won,
        )
        self._turn_history.append(record)
        self._pending.clear()
        if won:
            self._winner = self._to_move
        else:
            self._to_move = self._to_move.opponent
        return record
