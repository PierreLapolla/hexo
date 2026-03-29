from hexo import GameStatus, Hexo, IllegalTurnError, Player


def test_game_starts_with_center_occupied() -> None:
    game = Hexo.new()
    assert game.turn() is Player.P2
    assert game.at((0, 0)) is Player.P1


def test_each_played_turn_requires_two_stones() -> None:
    game = Hexo.new()
    legal, reason = game.is_legal([(1, 0)])
    assert legal is False
    assert reason == "each turn must place exactly 2 stones"


def test_distance_rule_enforced() -> None:
    game = Hexo.new()
    legal, reason = game.is_legal([(9, 0), (1, 0)])
    assert legal is False
    assert "within distance <= 8" in (reason or "")


def test_play_and_undo() -> None:
    game = Hexo.new()
    record = game.play([(1, 0), (0, 1)])
    assert record.player is Player.P2
    assert game.turn() is Player.P1

    undone = game.undo()
    assert undone.placements == ((1, 0), (0, 1))
    assert game.turn() is Player.P2
    assert game.at((1, 0)) is Player.P2
    assert game.at((0, 1)) is None


def test_submoves_allow_partial_turn_search_state() -> None:
    game = Hexo.new()
    first = game.push((1, 0))
    assert first is None
    assert game.moves_left_in_turn() == 1
    assert game.pending_moves() == ((1, 0),)
    assert game.turn() is Player.P2

    second = game.push((0, 1))
    assert second is not None
    assert second.placements == ((1, 0), (0, 1))
    assert game.moves_left_in_turn() == 2
    assert game.pending_moves() == ()
    assert game.turn() is Player.P1


def test_legal_moves_produces_candidates() -> None:
    game = Hexo.new()
    moves = game.legal_moves
    assert len(moves) > 0
    assert (0, 0) not in moves
    for coord in moves:
        legal, reason = game.is_legal_move(coord)
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


def test_connect_six_sets_winner() -> None:
    game = Hexo.new()
    game.play([(8, 0), (7, 1)])  # P2 filler
    game.play([(1, 0), (2, 0)])  # P1
    game.play([(8, 1), (7, 2)])  # P2 filler
    game.play([(3, 0), (4, 0)])  # P1
    game.play([(8, 2), (7, 3)])  # P2 filler
    final = game.play([(5, 0), (6, 0)])  # P1
    assert final.won is True
    assert game.status() is GameStatus.P1_WON

    try:
        game.play([(6, 1), (6, 2)])
        assert False, "play after game end should fail"
    except IllegalTurnError:
        pass


def test_state_roundtrip() -> None:
    game = Hexo.new()
    game.play([(1, 0), (0, 1)])
    game.push((2, 0))
    state = game.to_state()

    restored = Hexo.from_state(state)
    assert restored.turn() is game.turn()
    assert restored.status() is game.status()
    assert restored.at((0, 0)) is Player.P1
    assert restored.pending_moves() == game.pending_moves()
