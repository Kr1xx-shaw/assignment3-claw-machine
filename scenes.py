"""Repeatable illustration states for screenshots; never used in normal play.

The carry/drop example is reached by running real physics and successful grabs.
End-state screenshot fixtures are explicitly created for layout inspection.
"""
import copy
from model import Game, State, BIN_CENTER


def advance_until(game, predicate, limit=1200):
    for _ in range(limit):
        game.update(1/120)
        if predicate():
            return
    raise RuntimeError('Scene did not reach the expected state.')


def actual_catch(game):
    # Try candidate aims in isolated replays of the SAME starting state.
    # This is a documentation helper, not a player assist or game success rule.
    for x in (350, 590, 670, 750, 830, 430, 510, 900):
        trial = copy.deepcopy(game)
        trial.aim(x)
        advance_until(trial, lambda: abs(trial.claw_x-x)<1)
        trial.action()
        advance_until(trial, lambda: trial.state in (State.CARRY, State.MOVE, State.LOST))
        if trial.state == State.CARRY:
            return trial
    raise RuntimeError('No documentation catch found.')


def documentation_scene(name):
    game = Game(7)
    if name == 'start':
        for _ in range(36):
            game.update(1/120)
        return game
    if name in ('win', 'loss'):
        game.collected = [(0, 0), (2, 2), (3, 3)] if name == 'win' else [(0, 0)]
        game.misses = 1 if name == 'win' else 3
        game.state = State.WON if name == 'win' else State.LOST
        game.message = 'Three collected. Your collection is complete!' if name == 'win' else 'Three empty grabs. Try a new round.'
        collected_ids = {identity for _, identity in game.collected}
        game.balls = [ball for ball in game.balls if ball.id not in collected_ids]
        return game
    game = actual_catch(game)
    game.aim(BIN_CENTER)
    advance_until(game, lambda: abs(game.claw_x-BIN_CENTER)<1)
    game.action()
    advance_until(game, lambda: game.state == State.MOVE)
    game = actual_catch(game)
    game.aim(BIN_CENTER)
    advance_until(game, lambda: abs(game.claw_x-BIN_CENTER)<1)
    if name == 'drop':
        game.action()
        for _ in range(82):
            game.update(1/120)
    return game

