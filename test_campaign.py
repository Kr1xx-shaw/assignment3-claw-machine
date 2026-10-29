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
    g.claw_x = 500
    app.action()
    assert g.state == State.LOWER
    g.claw_x, g.claw_y, g.close_amount = 500, 500, .62
    g.set_state(State.CLOSE)
    ball = Ball(identity, 500, 563, color_index=color)
    g.balls = [ball]
    assert g._secure(ball)
    step_until(app, lambda: g.state == State.CARRY)
    g.aim(BIN_CENTER)
    step_until(app, lambda: abs(g.claw_x-BIN_CENTER) < .1)
    before = app.progress.coins
    app.action()
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
        self.assertEqual(a.progress.coins, 350)
        previous = a.game
        a.request_retry()
        a.update(20)
        a.cancel()
        self.assertIs(a.game, previous)
        self.assertEqual(a.progress.coins, 350)
        a.request_retry()
        a.request_start(1)
        self.assertIsNot(a.game, previous)
        self.assertEqual(a.progress.coins, 150)
        self.assertEqual(a.progress.colors[0], 1)
        self.assertEqual(a.game.collected, [])

    def test_only_real_delivery_pays_once_and_same_color_carries_to_next_level(self):
        a = Campaign(seed=7)
        a.request_start()
        for i in range(3):
            deliver(a, identity=100+i)
        self.assertEqual(a.round_rewards, [100, 200, 200])
        self.assertEqual(a.progress.coins, 650)
        self.assertEqual(a.progress.unlocked, 2)
        self.assertEqual(a.screen, 'result')
        a.update(20)
        self.assertEqual(a.progress.coins, 650)
        a.request_start(2)
        self.assertEqual(a.progress.coins, 450)
        self.assertEqual(a.game.balls, [])
        deliver(a)
        self.assertEqual(a.round_rewards, [200])
        self.assertEqual(a.progress.coins, 600)

    def test_different_color_keeps_its_first_reward(self):
        a = Campaign(seed=7)
        a.request_start()
        for identity, color in enumerate((0, 0, 1), 100):
            deliver(a, color=color, identity=identity)
        self.assertEqual(a.round_rewards, [100, 200, 100])
        self.assertEqual(a.next_reward(0), 200)
        self.assertEqual(a.next_reward(1), 200)
        self.assertEqual(a.next_reward(2), 100)

    def test_each_empty_attempt_deducts_once_and_three_end_the_round(self):
        a = Campaign(seed=7)
        a.request_start()
        a.game.balls = []
        for count in range(1, 4):
            for _ in range(10):
                a.action()
            step_until(a, lambda: a.game.state in (State.MOVE, State.LOST))
            self.assertEqual(a.progress.coins, 300-count*100)
            self.assertEqual(a.game.misses, count)
        self.assertEqual(a.screen, 'result')
        self.assertFalse(a.request_start())
        self.assertEqual(a.screen, 'broke')
        self.assertEqual(a.progress.coins, 0)

    def test_last_fifty_coins_allow_a_complete_grab_and_delivery(self):
        a = Campaign(seed=7)
        a.progress.coins = 250
        a.request_start()
        deliver(a)
        self.assertEqual(a.progress.coins, 100)
        self.assertEqual(a.round_grab_costs, 50)
        self.assertEqual(a.screen, 'play')

    def test_fee_is_immediate_persisted_and_only_for_valid_lowering(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'progress.json'
            a = Campaign(path, seed=7)
            a.request_start()
            a.game.claw_x = BIN_CENTER
            a.action()
            self.assertEqual(a.progress.coins, 300)
            a.game.claw_x = 600
            a.game.toggle_pause()
            a.action()
            self.assertEqual(a.progress.coins, 300)
            a.game.toggle_pause()
            a.action()
            self.assertEqual(a.progress.coins, 250)
            self.assertEqual(Campaign(path).progress.coins, 250)
            for _ in range(20):
                a.action()
            self.assertEqual(a.progress.coins, 250)
            self.assertEqual(a.game.attempts, 1)
            self.assertEqual(a.round_grab_costs, 50)

    def test_insufficient_grab_funds_block_without_overdraft(self):
        a = Campaign(seed=7)
        a.progress.coins = 249
        self.assertFalse(a.request_start())
        self.assertEqual(a.progress.coins, 249)
        self.assertEqual(a.required_coins, 250)
        a.ask_reset()
        a.confirm_reset()
        a.request_start()
        a.progress.coins = 49
        a.action()
        self.assertEqual(a.screen, 'broke')
        self.assertEqual(a.required_coins, 50)
        self.assertEqual(a.progress.coins, 49)
        self.assertEqual(a.game.attempts, 0)

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
        self.assertEqual(a.progress.coins, 1150)
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
            self.assertEqual(b.progress.coins, 150)
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
            timing = (1.2, 350) if level == 2 else (1, 350)
            for delay, x in (timing, (0, 600)):
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

    def test_level_two_is_moderate_and_level_three_stays_fast(self):
        for level, low, high in ((2, 320, 380), (3, 540, 640)):
            g = Game(7, level)
            g._spawn_stream(1)
            ball = g.balls[0]
            self.assertGreaterEqual(ball.vx, low)
            self.assertLessEqual(ball.vx, high)
            self.assertLess((972-ball.x)/ball.vx, 2.6)
            identity = ball.id
            for _ in range(120*3):
                g.update(FIXED_DT)
            self.assertFalse(any(b.id == identity for b in g.balls))

    def test_bullets_cannot_be_held_even_at_valid_ball_contact(self):
        g = Game(7, 3)
        g.claw_x, g.claw_y, g.close_amount = 500, 500, .62
        b = Ball(100, 500, 563, kind='bullet')
        self.assertTrue(g.finger_contact(b, -1))
        self.assertTrue(g.finger_contact(b, 1))
        self.assertFalse(g._secure(b))
        seen = set()
        for _ in range(120*8):
            g.update(FIXED_DT)
            seen.update(b.kind for b in g.balls)
        self.assertEqual(seen, {'bullet', 'ball'})


if __name__ == '__main__':
    unittest.main()
