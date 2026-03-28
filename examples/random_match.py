from __future__ import annotations

import random

from pedros import get_logger, timed

from hexo import Coord, GameStatus, Hexo


def random_engine(game: Hexo, rng: random.Random) -> Coord:
    candidates = game.legal_moves()
    if not candidates:
        raise RuntimeError("no legal candidate placements found")
    return rng.choice(candidates)


def play_turn_random(game: Hexo, rng: random.Random) -> tuple[Coord, ...]:
    chosen: list[Coord] = []
    player = game.turn()
    while game.turn() is player and game.status() is GameStatus.ONGOING:
        coord = random_engine(game, rng)
        game.push(coord)
        chosen.append(coord)
    return tuple(chosen)


@timed
def run_demo_match(seed: int = 42, max_turns: int = 100) -> GameStatus:
    logger = get_logger()
    rng = random.Random(seed)
    game = Hexo.new()

    logger.info("Starting Hexo demo: P1=random, P2=random, seed=%s", seed)
    logger.info("Initial center stone is fixed at (0, 0) for P1")

    turn_no = 1
    while game.status() is GameStatus.ONGOING and turn_no <= max_turns:
        player = game.turn()
        placements = play_turn_random(game, rng)
        logger.info("Turn %s | %s (random) -> %s", turn_no, player.name, placements)
        turn_no += 1

    status = game.status()
    if status is GameStatus.P1_WON:
        logger.info(
            "Game finished: winner=P1 status=%s turns=%s", status.name, turn_no - 1
        )
    elif status is GameStatus.P2_WON:
        logger.info(
            "Game finished: winner=P2 status=%s turns=%s", status.name, turn_no - 1
        )
    else:
        logger.warning("Reached max turns (%s) with status=%s", max_turns, status.name)
    return status


if __name__ == "__main__":
    run_demo_match()
