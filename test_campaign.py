"""Behavior tests for paid entries, real deliveries, unlocks and safe persistence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from campaign import Campaign, Progress
from model import Ball, Game, State, BIN_CENTER, FIXED_DT
from test_game import advance_until


def step_until(app, predicate, limit=2000):
    for _ in range(limit):
        app.update(FIXED_DT)
        if predicate():
            return
    raise AssertionError(f'Timed out: {app.screen}, {app.game.state}')


def deliver(app, color=0, identity=99):
    """Start at verified opposing contact, then use real lift/carry/drop physics."""
    g = app.game
    g.claw_x, g.claw_y, g.close_amount = 500, 500, .62
    g.set_state(State.CLOSE)
    ball = Ball(identity, 500, 563, color_index=color)
    g.balls = [ball]
    assert g._secure(ball)
    step_until(app, lambda: g.state == State.CARRY)
    g.aim(BIN_CENTER)
    step_until(app, lambda: abs(g.claw_x-BIN_CENTER) < .1)
    before = app.progress.coins
    g.action()
    assert app.progress.coins == before
    step_until(app, lambda: g.state in (State.MOVE, State.WON))


class EconomyTests(unittest.TestCase):
    def test_start_menu_is_free_and_double_start_cannot_charge_twice(self):
        a = Campaign(seed=7)
        self.assertIsNone(a.game)
        a.update(10)
        self.assertEqual(a.progress.coins, 500)
        self.assertFalse(a.request_start(2))
        self.assertTrue(a.request_start(1))
        self.assertFalse(a.request_start(1))
        self.assertEqual(a.progress.coins, 300)
        a.game.toggle_pause()
        a.update(10)
        self.assertEqual(a.progress.coins, 300)

    def test_paid_retry_cancel_and_confirm_preserve_color_history(self):
        a = Campaign(seed=7)
        a.request_start()
        deliver(a)
        self.assertEqual(a.progress.coins, 400)
        previous = a.game
        a.request_retry()
        a.update(20)
        a.cancel()
        self.assertIs(a.game, previous)
        self.assertEqual(a.progress.coins, 400)
        a.request_retry()
        a.request_start(1)
        self.assertIsNot(a.game, previous)
        self.assertEqual(a.progress.coins, 200)
        self.assertEqual(a.progress.colors[0], 1)
        self.assertEqual(a.game.collected, [])

    def test_only_real_delivery_pays_once_and_same_color_carries_to_next_level(self):
        a = Campaign(seed=7)
        a.request_start()
        for i in range(3):
            deliver(a, identity=100+i)
        self.assertEqual(a.round_rewards, [100, 150, 200])
        self.assertEqual(a.progress.coins, 750)
        self.assertEqual(a.progress.unlocked, 2)
        self.assertEqual(a.screen, 'result')
        a.update(20)
        self.assertEqual(a.progress.coins, 750)
        a.request_start(2)
        self.assertEqual(a.progress.coins, 550)
        self.assertEqual(a.game.balls, [])
        deliver(a)
        self.assertEqual(a.round_rewards, [250])
        self.assertEqual(a.progress.coins, 800)

    def test_each_empty_attempt_deducts_once_and_three_end_the_round(self):
        a = Campaign(seed=7)
        a.request_start()
        a.game.balls = []
        for count in range(1, 4):
            for _ in range(10):
                a.game.action()
            step_until(a, lambda: a.game.state in (State.MOVE, State.LOST))
            self.assertEqual(a.progress.coins, 300-count*50)
            self.assertEqual(a.game.misses, count)
        self.assertEqual(a.screen, 'result')
        self.assertFalse(a.request_start())
        self.assertEqual(a.screen, 'broke')
        self.assertEqual(a.progress.coins, 150)

    def test_zero_balance_does_not_abort_paid_round_or_prevent_earning(self):
        a = Campaign(seed=7)
        a.progress.coins = 200
        a.request_start()
        a.game.balls = []
        a.game.action()
        step_until(a, lambda: a.game.state == State.MOVE)
        self.assertEqual(a.progress.coins, 0)
        self.assertEqual(a.screen, 'play')
        deliver(a)
        self.assertEqual(a.progress.coins, 100)

    def test_level_three_requires_briefing_each_entry_and_charges_only_at_start(self):
        a = Campaign(seed=7)
        a.progress.unlocked = 3
        a.progress.cleared[:2] = [True, True]
        a.request_start(3)
        self.assertEqual(a.screen, 'briefing')
        self.assertEqual(a.progress.coins, 500)
        a.update(5)
        self.assertIsNone(a.game)
        a.cancel()
        self.assertEqual(a.progress.coins, 500)
        a.request_start(3)
        self.assertTrue(a.accept_briefing())
        self.assertFalse(a.accept_briefing())
        self.assertEqual(a.progress.coins, 300)
        a.request_retry()
        a.request_start(3)
        self.assertEqual(a.screen, 'briefing')
        self.assertEqual(a.progress.coins, 300)
        a.accept_briefing()
        self.assertEqual(a.progress.coins, 100)

    def test_campaign_can_clear_all_levels_and_reset_clears_every_record(self):
        a = Campaign(seed=7)
        for level in range(1, 4):
            a.request_start(level)
            if level == 3:
                a.accept_briefing()
            for i in range(3):
                deliver(a, identity=100+i)
            self.assertEqual(a.game.state, State.WON)
        self.assertEqual(a.progress.cleared, [True]*3)
        self.assertEqual(a.progress.colors[0], 9)
        self.assertEqual(a.progress.coins, 2600)
        before = copy.deepcopy(a.progress)
        a.ask_reset()
        a.cancel()
        self.assertEqual(a.progress, before)
        a.ask_reset()
        a.confirm_reset()
        self.assertEqual(a.progress, Progress())
        self.assertIsNone(a.game)
        self.assertEqual(a.screen, 'menu')


class StorageTests(unittest.TestCase):
    def test_paid_entry_and_rewards_survive_reopen_and_reset_is_saved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'progress.json'
            a = Campaign(path, seed=7)
            a.request_start()
            deliver(a)
            b = Campaign(path)
            self.assertEqual(b.progress, a.progress)
            self.assertEqual(b.screen, 'menu')
            self.assertIsNone(b.game)
            b.request_start()
            self.assertEqual(b.progress.coins, 200)
            b.ask_reset()
            b.confirm_reset()
            self.assertEqual(Campaign(path).progress, Progress())

    def test_bad_save_is_not_silently_overwritten_and_requires_explicit_reset(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'progress.json'
            for content in ('{broken', '[]', '{"version":1,"progress":{"coins":-1}}'):
                path.write_text(content)
                a = Campaign(path)
                self.assertTrue(a.load_blocked)
                self.assertFalse(a.request_start())
                self.assertEqual(path.read_text(), content)
                a.ask_reset()
                a.confirm_reset()
                self.assertFalse(Campaign(path).load_blocked)

    def test_write_failure_keeps_game_playable_and_warns(self):
        a = Campaign('unused.json', seed=7)
        with patch('pathlib.Path.mkdir', side_effect=OSError('read only')):
            self.assertTrue(a.request_start())
            self.assertIn('memory', a.save_error)
            self.assertEqual(a.progress.coins, 300)


class StreamTests(unittest.TestCase):
    def test_empty_start_left_jets_right_recycler_no_misses(self):
        for level in (2, 3):
            g = Game(7, level)
            self.assertEqual(g.balls, [])
            for _ in range(120*30):
                g.update(FIXED_DT)
            self.assertGreater(g.spawn_count, 20)
            self.assertLess(len(g.balls), 18)
            self.assertTrue(all(b.x < 972 for b in g.balls))
            self.assertEqual(g.misses, 0)
            self.assertEqual(g.collected, [])
            self.assertEqual(g.events, [])

    def test_stream_levels_allow_actual_physics_catch_and_miss(self):
        for level in (2, 3):
            outcomes = []
            for delay, x in ((1.6, 350), (0, 600)):
                g = Game(7, level)
                g.aim(x)
                for _ in range(round(delay*120)):
                    g.update(FIXED_DT)
                g.action()
                advance_until(g, lambda: g.state in (State.CARRY, State.MOVE))
                outcomes.append(g.state)
                if g.state == State.CARRY:
                    self.assertEqual(g.held_ball.kind, 'ball')
                    self.assertTrue(g.grip_confirmed)
            self.assertEqual(outcomes, [State.CARRY, State.MOVE])

    def test_bullets_cannot_be_held_even_at_valid_ball_contact(self):
        g = Game(7, 3)
        g.claw_x, g.claw_y, g.close_amount = 500, 500, .62
        b = Ball(100, 500, 563, kind='bullet')
        self.assertTrue(g.finger_contact(b, -1))
        self.assertTrue(g.finger_contact(b, 1))
        self.assertFalse(g._secure(b))
        for _ in range(120*8):
            g.update(FIXED_DT)
        self.assertTrue(any(b.kind == 'bullet' for b in g.balls))
        self.assertTrue(any(b.kind == 'ball' for b in g.balls))


if __name__ == '__main__':
    unittest.main()
