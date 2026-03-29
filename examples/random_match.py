from __future__ import annotations

import random

from pedros import get_logger, timed

from hexo import GameStatus, Hexo

Coord = tuple[int, int]


def random_engine(game: Hexo, rng: random.Random) -> Coord:
    candidates = game.legal_moves
    if not candidates:
        raise RuntimeError("no legal candidate placements found")
    return rng.choice(tuple(candidates))


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
    return status


if __name__ == "__main__":
    run_demo_match()
