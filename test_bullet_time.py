"""Limited hold-to-slow control, simulation timing and real keyboard events."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import types
import unittest
from unittest.mock import patch
import pygame

import main
from campaign import Campaign
from model import Game, Ball, State, FIXED_DT


def advance(game, frames):
    for _ in range(frames):
        game.update(FIXED_DT)


class BulletTimeTests(unittest.TestCase):
    def test_only_level_three_has_three_separate_activations(self):
        for level in (1, 2):
            g = Game(7, level)
            self.assertFalse(g.start_bullet_time())
            self.assertEqual(g.bullet_time_left, 0)
        g = Game(7, 3)
        for expected in (2, 1, 0):
            self.assertTrue(g.start_bullet_time())
            for _ in range(10):
                self.assertFalse(g.start_bullet_time())
            self.assertEqual(g.bullet_time_left, expected)
            self.assertTrue(g.bullet_time_active)
            g.end_bullet_time()
            self.assertFalse(g.bullet_time_active)
        self.assertFalse(g.start_bullet_time())
        self.assertEqual(g.bullet_time_left, 0)

    def test_ball_and_bullet_travel_83_percent_while_claw_keeps_full_speed(self):
        normal, slow = Game(7, 3), Game(7, 3)
        for g in (normal, slow):
            g.spawn_timer = 100
            g.balls = [Ball(50, 400, 350, vx=200), Ball(51, 400, 480, vx=240, kind='bullet')]
            g.aim(900)
        slow.start_bullet_time()
        advance(normal, 30)
        advance(slow, 30)
        for a, b in zip(normal.balls, slow.balls):
            self.assertAlmostEqual((b.x-400)/(a.x-400), .83, places=10)
            self.assertEqual(a.vx, b.vx)
        self.assertAlmostEqual(normal.claw_x, slow.claw_x)
        slow.end_bullet_time()
        before = [b.x for b in slow.balls]
        advance(slow, 30)
        self.assertAlmostEqual(slow.balls[0].x-before[0], 50)
        self.assertAlmostEqual(slow.balls[1].x-before[1], 60)

    def test_stream_launches_follow_slow_world_time(self):
        normal, slow = Game(7, 3), Game(7, 3)
        normal.spawn_timer = slow.spawn_timer = .5
        slow.start_bullet_time()
        advance(normal, 61)
        advance(slow, 61)
        self.assertEqual(normal.spawn_count, 1)
        self.assertEqual(slow.spawn_count, 0)
        advance(slow, 13)
        self.assertEqual(slow.spawn_count, 1)

    def test_pause_and_result_end_effect_without_refunding_or_auto_restart(self):
        g = Game(7, 3)
        g.start_bullet_time()
        g.toggle_pause()
        snapshot = [(b.x, b.y) for b in g.balls]
        advance(g, 120)
        self.assertEqual(snapshot, [(b.x, b.y) for b in g.balls])
        self.assertFalse(g.bullet_time_active)
        self.assertFalse(g.start_bullet_time())
        self.assertEqual(g.bullet_time_left, 2)
        g.toggle_pause()
        self.assertFalse(g.bullet_time_active)
        g.start_bullet_time()
        g.set_state(State.WON)
        self.assertFalse(g.bullet_time_active)
        self.assertFalse(g.start_bullet_time())

    def test_retry_cancels_effect_and_new_paid_round_restores_three_uses(self):
        a = Campaign(seed=7)
        a.progress.unlocked = 3
        a.request_start(3)
        a.accept_briefing()
        a.game.start_bullet_time()
        self.assertEqual(a.progress.coins, 300)
        a.request_retry()
        self.assertFalse(a.game.bullet_time_active)
        a.cancel()
        self.assertEqual(a.game.bullet_time_left, 2)
        self.assertFalse(a.game.bullet_time_active)
        a.request_retry()
        a.request_start(3)
        a.accept_briefing()
        self.assertEqual(a.game.bullet_time_left, 3)
        self.assertFalse(a.game.bullet_time_active)
        self.assertEqual(a.progress.coins, 100)

    def test_confirmed_hold_is_stable_during_slow_time_and_release(self):
        g = Game(7, 3)
        g.spawn_timer = 100
        g.claw_x, g.claw_y, g.close_amount = 500, 500, .62
        g.set_state(State.CLOSE)
        ball = Ball(50, 500, 563)
        g.balls = [ball]
        self.assertTrue(g._secure(ball))
        g.start_bullet_time()
        advance(g, 240)
        self.assertEqual(g.state, State.CARRY)
        g.aim(800)
        advance(g, 120)
        g.end_bullet_time()
        advance(g, 120)
        self.assertIs(g.held_ball, ball)
        self.assertAlmostEqual(ball.x-g.claw_x, g.held_offset[0])
        self.assertAlmostEqual(ball.y-g.claw_y, g.held_offset[1])


class KeyboardTests(unittest.TestCase):
    def test_real_space_hold_repeat_release_esc_and_focus_loss(self):
        a = Campaign(seed=7)
        a.progress.unlocked = 3
        a.request_start(3)
        a.accept_briefing()
        g = a.game
        phase = 0

        def key(kind, key):
            return [pygame.event.Event(kind, key=key)]

        def events():
            nonlocal phase
            phase += 1
            if phase == 1:
                return key(pygame.KEYDOWN, pygame.K_SPACE)
            if phase == 2:
                self.assertTrue(g.bullet_time_active)
                self.assertFalse(g.paused)
                self.assertEqual(g.bullet_time_left, 2)
                return key(pygame.KEYDOWN, pygame.K_SPACE)  # autorepeat
            if phase == 3:
                self.assertEqual(g.bullet_time_left, 2)
                return key(pygame.KEYUP, pygame.K_SPACE)
            if phase == 4:
                self.assertFalse(g.bullet_time_active)
                return key(pygame.KEYDOWN, pygame.K_SPACE)
            if phase == 5:
                self.assertTrue(g.bullet_time_active)
                self.assertEqual(g.bullet_time_left, 1)
                return key(pygame.KEYDOWN, pygame.K_ESCAPE)
            if phase == 6:
                self.assertTrue(g.paused)
                self.assertFalse(g.bullet_time_active)
                return key(pygame.KEYUP, pygame.K_SPACE)
            if phase == 7:
                return key(pygame.KEYDOWN, pygame.K_SPACE)
            if phase == 8:
                self.assertTrue(g.paused)
                self.assertEqual(g.bullet_time_left, 1)
                return key(pygame.KEYUP, pygame.K_SPACE)
            if phase == 9:
                return key(pygame.KEYDOWN, pygame.K_ESCAPE)
            if phase == 10:
                self.assertFalse(g.paused)
                return key(pygame.KEYDOWN, pygame.K_SPACE)
            if phase == 11:
                self.assertTrue(g.bullet_time_active)
                self.assertEqual(g.bullet_time_left, 0)
                return [pygame.event.Event(pygame.WINDOWFOCUSLOST)]
            if phase == 12:
                self.assertTrue(g.paused)
                self.assertFalse(g.bullet_time_active)
                return key(pygame.KEYDOWN, pygame.K_ESCAPE)
            if phase == 13:
                return key(pygame.KEYDOWN, pygame.K_SPACE)
            if phase == 14:
                self.assertFalse(g.bullet_time_active)
                self.assertFalse(g.paused)
                self.assertEqual(g.bullet_time_left, 0)
                self.assertEqual(a.progress.coins, 300)
                return [pygame.event.Event(pygame.QUIT)]
            raise AssertionError('Keyboard flow did not finish.')

        class Clock:
            def tick(self, fps):
                return 16

        with patch('sys.argv', ['main.py']), \
             patch('campaign.Campaign', return_value=a), \
             patch('pygame.display.Info', return_value=types.SimpleNamespace(current_w=1520, current_h=1020)), \
             patch('pygame.time.Clock', Clock), \
             patch('pygame.event.get', events), \
             patch('pygame.mouse.get_pos', return_value=(600, 400)):
            self.assertEqual(main.main(), 0)
        self.assertEqual(phase, 14)

    def test_space_never_pauses_level_one_or_two(self):
        for level in (1, 2):
            a = Campaign(seed=7)
            a.progress.unlocked = level
            a.request_start(level)
            frames = 0

            def events():
                nonlocal frames
                frames += 1
                if frames == 1:
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)]
                self.assertFalse(a.game.paused)
                self.assertFalse(a.game.bullet_time_active)
                return [pygame.event.Event(pygame.QUIT)]

            with patch('sys.argv', ['main.py']), \
                 patch('campaign.Campaign', return_value=a), \
                 patch('pygame.event.get', events):
                self.assertEqual(main.main(), 0)


if __name__ == '__main__':
    unittest.main()
