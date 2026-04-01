from __future__ import annotations

from collections.abc import Collection, Iterator, Sequence

from hexo._engine_utils import (
    build_radius_offsets,
    expand_legal_cache_from,
    has_winning_line_at,
)
from hexo.errors import (
    GAME_IS_OVER,
    ILLEGAL_MOVE,
    INVALID_COORDINATE,
    NO_MOVE_TO_UNDO,
    STATE_INVALID_MOVE,
    IllegalMoveError,
    move_out_of_radius,
    occupied_cell,
)
from hexo.types import (
    Coord,
    EngineConfig,
    GameStatus,
    MoveRecord,
    Player,
    State,
    UndoSnapshot,
)

MOVES_PER_TURN = 2


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
    Public Hexo engine API.

    The opening stone for `P1` is automatically placed at `(0, 0)` on init.
    Every call to `push` places exactly one stone.
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
        self._move_history: list[MoveRecord] = []
        self._undo_stack: list[UndoSnapshot] = []
        self._winner: Player | None = None
        self._to_move = Player.P2
        self._moves_played_in_turn = 0
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

        Expected format:
            `{ "moves": [[q, r], ...] }`

        :param state:
            Serialized state dictionary.
        :param config:
            Optional engine configuration to use for validation.
        :return:
            A reconstructed `Hexo` game after replaying all serialized moves.
        """
        game = cls.new(config=config)
        push = game.push

        raw_moves = state.get("moves")
        if isinstance(raw_moves, (str, bytes)) or not isinstance(raw_moves, Sequence):
            raise IllegalMoveError(STATE_INVALID_MOVE)
        for raw_coord in raw_moves:
            push(cls._coord_from_state(raw_coord))

        return game

    def to_state(self) -> State:
        """
        Serialize the current game into a portable dictionary representation.

        :return:
            A state dictionary with replayable move history.
        """
        moves = [[record.move[0], record.move[1]] for record in self._move_history]
        return {"moves": moves}

    def turn(self) -> Player:
        """
        Return the player expected to move next.

        :return:
            The current side to move.
        """
        return self._to_move

    def moves_left_in_turn(self) -> int:
        """
        Return remaining moves for the current player's turn.

        :return:
            `2` when starting a turn, `1` after the first move, `0` when game is over.
        """
        if self._winner is not None:
            return 0
        return MOVES_PER_TURN - self._moves_played_in_turn

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

    def is_legal(self, move: Coord) -> tuple[bool, str | None]:
        """
        Validate a single-stone move.

        :param move:
            Candidate coordinate `(q, r)`.
        :return:
            Tuple `(is_legal, reason)` where `reason` is `None` when legal.
        """
        coord, reason = self._normalize_coord(move)
        if reason is not None:
            return False, reason
        return self._is_legal_coord(coord)

    def push(self, move: Coord) -> MoveRecord:
        """
        Place one stone for the current player.

        The side to move changes only after every second move, matching Hexo's
        rule that each player places two stones per turn.

        :param move:
            Coordinate `(q, r)` to place.
        :return:
            Immutable record describing the applied move.
        """
        # Fast path for bot/search loops: valid tuple move already in legal cache.
        if (
            self._winner is None
            and isinstance(move, tuple)
            and len(move) == 2
            and isinstance(move[0], int)
            and isinstance(move[1], int)
            and move in self._legal_moves_cache
        ):
            coord = move
        else:
            coord, reason = self._normalize_coord(move)
            if reason is not None:
                raise IllegalMoveError(reason)

            legal, reason = self._is_legal_coord(coord)
            if not legal:
                raise IllegalMoveError(reason or ILLEGAL_MOVE)

        prev_to_move = self._to_move
        prev_winner = self._winner
        prev_turn_progress = self._moves_played_in_turn
        board = self._board
        legal_cache = self._legal_moves_cache
        removed_from_cache = coord in legal_cache

        board[coord] = prev_to_move
        player_cells = self._stones_by_player[prev_to_move]
        player_cells.add(coord)
        legal_cache.discard(coord)
        added_legal = expand_legal_cache_from(
            coord,
            self._radius_offsets,
            board,
            legal_cache,
        )

        # Avoid line scanning until this player has enough stones to win.
        if len(player_cells) >= self.config.win_length:
            won = has_winning_line_at(player_cells, coord, self.config.win_length)
        else:
            won = False
        record = MoveRecord(player=prev_to_move, move=coord, won=won)
        self._move_history.append(record)
        self._undo_stack.append(
            (
                coord,
                prev_to_move,
                prev_winner,
                prev_turn_progress,
                removed_from_cache,
                added_legal,
            )
        )

        if won:
            self._winner = prev_to_move
            return record

        if prev_turn_progress == 0:
            self._moves_played_in_turn = 1
        else:
            self._moves_played_in_turn = 0
            self._to_move = prev_to_move.opponent

        return record

    def undo(self) -> MoveRecord:
        """
        Revert the last applied move.

        :return:
            Record of the undone move.
        """
        if not self._undo_stack:
            raise IllegalMoveError(NO_MOVE_TO_UNDO)

        record = self._move_history.pop()
        (
            coord,
            prev_to_move,
            prev_winner,
            prev_turn_progress,
            removed_from_cache,
            added_legal,
        ) = self._undo_stack.pop()

        self._board.pop(coord, None)
        self._stones_by_player[record.player].discard(coord)
        self._to_move = prev_to_move
        self._winner = prev_winner
        self._moves_played_in_turn = prev_turn_progress

        if removed_from_cache:
            self._legal_moves_cache.add(coord)
        for added in added_legal:
            self._legal_moves_cache.discard(added)

        return record

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
        Return a live view of all currently legal moves.

        :return:
            Collection view of legal coordinates.
        """
        return self._legal_moves_view

    @staticmethod
    def _normalize_coord(move: object) -> tuple[Coord | None, str | None]:
        """
        Validate runtime move shape and return a normalized coordinate.
        """
        if isinstance(move, tuple):
            if len(move) != 2:
                return None, INVALID_COORDINATE
            q, r = move
        elif isinstance(move, list):
            if len(move) != 2:
                return None, INVALID_COORDINATE
            q, r = move
        else:
            return None, INVALID_COORDINATE
        if not isinstance(q, int) or not isinstance(r, int):
            return None, INVALID_COORDINATE
        if isinstance(move, tuple):
            return move, None
        return (q, r), None

    def _is_legal_coord(self, coord: Coord) -> tuple[bool, str | None]:
        """
        Validate one already-normalized coordinate.
        """
        if self._winner is not None:
            return False, GAME_IS_OVER
        if coord in self._legal_moves_cache:
            return True, None
        if coord in self._board:
            return False, occupied_cell(coord)
        return False, move_out_of_radius(coord, self.config.placement_radius)

    @staticmethod
    def _coord_from_state(raw_coord: object) -> Coord:
        """
        Parse one serialized coordinate pair.
        """
        if isinstance(raw_coord, (str, bytes)) or not isinstance(raw_coord, Sequence):
            raise IllegalMoveError(STATE_INVALID_MOVE)
        if len(raw_coord) != 2:
            raise IllegalMoveError(STATE_INVALID_MOVE)

        try:
            return int(raw_coord[0]), int(raw_coord[1])
        except (TypeError, ValueError) as exc:
            raise IllegalMoveError(STATE_INVALID_MOVE) from exc
