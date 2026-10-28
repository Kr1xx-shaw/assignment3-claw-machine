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


def campaign_scene(name):
    """Isolated layout fixtures: never read or write player progress."""
    from campaign import Campaign
    a = Campaign(seed=7)
    if name == 'start':
        return a
    if name in ('help', 'reset', 'broke'):
        a.screen = name
        if name == 'broke':
            a.progress.coins = 50
        return a
    if name in ('briefing', 'level3'):
        a.progress.unlocked = 3
        a.progress.cleared[:2] = [True, True]
        a.request_start(3)
        if name == 'briefing':
            return a
        a.accept_briefing()
    elif name == 'level2':
        a.progress.unlocked = 2
        a.progress.cleared[0] = True
        a.request_start(2)
    else:
        a.request_start(1)
    if name in ('level2', 'level3'):
        for _ in range(120*4):
            a.update(1/120)
    elif name in ('carry', 'drop', 'win', 'loss'):
        a.game = documentation_scene(name)
        attempts = a.game.attempts
        if name in ('win', 'loss'):
            # Explicit layout fixtures also need matching accounting events.
            attempts = len(a.game.collected) + a.game.misses
            a.game.events = [('delivery', color) for color, _ in a.game.collected]
            a.game.events += [('miss', None)] * a.game.misses
        a.round_grab_costs = attempts * 50
        a.progress.coins -= a.round_grab_costs
        a.update(0)
    return a

