from __future__ import annotations

import random

from pedros import get_logger, timed

from hexo import GameStatus, Hexo


def play_turn_random(game: Hexo, rng: random.Random):
    player = game.turn()
    while game.turn() is player:
        move = rng.choice(tuple(game.legal_moves))
        game.push(move)


@timed
def run_demo_match(seed: int = 42, max_turns: int = 2000):
    logger = get_logger()
    rng = random.Random(seed)
    game = Hexo.new()

    logger.info(f"Starting Hexo demo: P1=random, P2=random, seed={seed}")
    logger.info("Initial center stone is fixed at (0, 0) for P1")

    turn_no = 1
    while game.status() is GameStatus.ONGOING and turn_no <= max_turns:
        play_turn_random(game, rng)
        turn_no += 1

    status = game.status()
    if status is GameStatus.P1_WON:
        logger.info(
            f"Game finished: winner=P1 status={status.name} turns={turn_no - 1}"
        )
    elif status is GameStatus.P2_WON:
        logger.info(
            f"Game finished: winner=P2 status={status.name} turns={turn_no - 1}"
        )
    else:
        logger.warning(f"Reached max turns ({max_turns}) with status={status.name}")


if __name__ == "__main__":
    run_demo_match()
