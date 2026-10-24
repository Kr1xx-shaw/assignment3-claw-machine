"""Exercise the real Pygame event loop with synthetic input, without a desktop.

This is an automated integration check, NOT a human usability study.
Run using a Python environment that has pygame installed.
"""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import types
import unittest
from unittest.mock import patch
import pygame
import main
import model


class EventLoopTests(unittest.TestCase):
    def test_real_clicks_deliver_pause_and_restart(self):
        game = model.Game(7)
        phase = 'aim'
        position = [350, 400]
        frames = 0
        paused_snapshot = None

        def event(kind, **kwargs):
            return [pygame.event.Event(kind, **kwargs)]

        def get_events():
            nonlocal phase, frames, paused_snapshot
            frames += 1
            if frames > 1500:
                raise AssertionError(f'UI flow timed out: {phase}, {game.state}')
            if phase == 'aim' and abs(game.claw_x-350)<1:
                phase = 'grabbing'
                return event(pygame.MOUSEBUTTONDOWN, button=1, pos=(350, 400))
            if phase == 'grabbing' and game.state == model.State.CARRY:
                phase = 'carry'
                position[:] = [model.BIN_CENTER, 400]
            if phase == 'grabbing' and game.misses:
                raise AssertionError('The expected real-physics catch did not occur.')
            if phase == 'carry' and abs(game.claw_x-model.BIN_CENTER)<1:
                phase = 'delivery'
                return event(pygame.MOUSEBUTTONDOWN, button=1, pos=(model.BIN_CENTER, 400))
            if phase == 'delivery' and len(game.collected)==1:
                phase = 'pause'
                return event(pygame.KEYDOWN, key=pygame.K_SPACE)
            if phase == 'pause':
                self.assertTrue(game.paused)
                paused_snapshot = [(b.x, b.y) for b in game.balls]
                phase = 'paused-click'
                return event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1240, 710))
            if phase == 'paused-click':
                self.assertEqual(paused_snapshot, [(b.x, b.y) for b in game.balls])
                self.assertEqual(game.attempts, 1)
                phase = 'restart-key'
                return event(pygame.KEYDOWN, key=pygame.K_r)
            if phase == 'restart-key':
                self.assertEqual(len(game.collected), 0)
                self.assertEqual(game.state, model.State.MOVE)
                self.assertFalse(game.paused)
                self.assertEqual(game.round_number, 2)
                phase = 'restart-button'
                return event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1320, 58))
            if phase == 'restart-button':
                self.assertEqual(game.round_number, 3)
                phase = 'finished'
                return event(pygame.QUIT)
            return []

        class Clock:
            def tick(self, fps):
                return 16

        with patch('sys.argv', ['main.py']), \
             patch('model.Game', return_value=game), \
             patch('pygame.display.Info', return_value=types.SimpleNamespace(current_w=1520, current_h=1020)), \
             patch('pygame.time.Clock', Clock), \
             patch('pygame.event.get', get_events), \
             patch('pygame.mouse.get_pos', lambda: tuple(position)):
            self.assertEqual(main.main(), 0)
        self.assertEqual(phase, 'finished')


if __name__ == '__main__':
    unittest.main()

