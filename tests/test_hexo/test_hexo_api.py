from hexo import GameStatus, Hexo, IllegalMoveError, Player


def test_game_starts_with_center_occupied() -> None:
    game = Hexo.new()
    assert game.turn() is Player.P2
    assert game.at((0, 0)) is Player.P1
    assert game.moves_left_in_turn() == 2


def test_is_legal_validates_single_stone_move() -> None:
    game = Hexo.new()

    legal, reason = game.is_legal((1, 0))
    assert legal is True
    assert reason is None

    legal, reason = game.is_legal(((1, 0), (0, 1)))
    assert legal is False
    assert reason == "move must be an axial coordinate (q, r)"


def test_distance_rule_enforced() -> None:
    game = Hexo.new()
    legal, reason = game.is_legal((9, 0))
    assert legal is False
    assert "within distance <= 8" in (reason or "")


def test_push_one_move_and_undo() -> None:
    game = Hexo.new()

    record = game.push((1, 0))
    assert record.player is Player.P2
    assert record.move == (1, 0)
    assert record.won is False
    assert game.turn() is Player.P2
    assert game.moves_left_in_turn() == 1

    undone = game.undo()
    assert undone.move == (1, 0)
    assert game.turn() is Player.P2
    assert game.moves_left_in_turn() == 2
    assert game.at((1, 0)) is None


def test_player_switches_after_two_moves() -> None:
    game = Hexo.new()

    game.push((1, 0))
    assert game.turn() is Player.P2
    assert game.moves_left_in_turn() == 1

    game.push((0, 1))
    assert game.turn() is Player.P1
    assert game.moves_left_in_turn() == 2


def test_legal_moves_produces_candidates() -> None:
    game = Hexo.new()
    moves = game.legal_moves
    assert len(moves) > 0
    assert (0, 0) not in moves
    for coord in moves:
        legal, reason = game.is_legal(coord)
        assert legal is True
        assert reason is None


def test_legal_moves_cache_updates_on_push_and_undo() -> None:
    game = Hexo.new()
    before = set(game.legal_moves)
    move = (1, 0)
    assert move in before

    game.push(move)
    during = set(game.legal_moves)
    assert move not in during

    game.undo()
    after = set(game.legal_moves)
    assert after == before


def test_connect_six_sets_winner_even_mid_turn() -> None:
    game = Hexo.new()

    game.push((8, 0))  # P2
    game.push((7, 1))  # P2

    game.push((1, 0))  # P1
    game.push((2, 0))  # P1

    game.push((8, 2))  # P2
    game.push((7, 3))  # P2

    game.push((3, 0))  # P1
    game.push((4, 0))  # P1

    game.push((8, 4))  # P2
    game.push((7, 5))  # P2

    final = game.push((5, 0))  # P1 wins with 0..5 on (1, 0) axis
    assert final.won is True
    assert game.status() is GameStatus.P1_WON

    try:
        game.push((6, 1))
        assert False, "push after game end should fail"
    except IllegalMoveError:
        pass


def test_state_roundtrip_with_partial_turn_progress() -> None:
    game = Hexo.new()
    game.push((1, 0))
    game.push((0, 1))
    game.push((2, 0))
    state = game.to_state()

    restored = Hexo.from_state(state)
    assert restored.turn() is game.turn()
    assert restored.status() is game.status()
    assert restored.at((0, 0)) is Player.P1
    assert restored.moves_left_in_turn() == game.moves_left_in_turn()


def test_from_state_rejects_legacy_format() -> None:
    try:
        Hexo.from_state({"turns": [[[1, 0], [0, 1]]], "pending": []})
        assert False, "legacy turns/pending state should be rejected"
    except IllegalMoveError:
        pass
