"""Behavioral checks for the rules that matter to this project.

Run with: python -m unittest -v test_game
Only the Python standard library is required.
"""
import copy
import unittest

from model import (
    Game, Ball, State, BIN_CENTER, BIN_LEFT, BIN_RIGHT, BIN_TOP,
    FLOOR, RADIUS, REST_Y, NOZZLE_TOP, NOZZLE_LEFT, FIXED_DT,
)


def advance_until(game, predicate, seconds=12):
    for _ in range(int(seconds / FIXED_DT)):
        game.update(FIXED_DT)
        if predicate():
            return
    raise AssertionError(f'Timed out in {game.state}')


class GripTests(unittest.TestCase):
    def setUp(self):
        self.g = Game(11)
        self.g.claw_x, self.g.claw_y = 500, 500
        self.g.close_amount = .62
        self.g.state = State.CLOSE

    def test_two_opposing_fingers_can_secure_a_ball(self):
        ball = Ball(100, 500, 563)
        self.g.balls = [ball]
        self.assertTrue(self.g.finger_contact(ball, -1))
        self.assertTrue(self.g.finger_contact(ball, 1))
        self.assertTrue(self.g._secure(ball))
        self.assertEqual(ball.mode, 'held')
        self.assertEqual(self.g.held_id, ball.id)
        self.assertEqual(self.g.collected, [])  # gripping is NOT scoring

    def test_touching_only_one_finger_does_not_grab(self):
        ball = Ball(100, 538, 558)
        self.assertTrue(self.g.finger_contact(ball, 1))
        self.assertFalse(self.g.finger_contact(ball, -1))
        self.assertFalse(self.g._secure(ball))

    def test_far_ball_and_ball_above_pocket_cannot_be_grabbed(self):
        self.assertFalse(self.g._secure(Ball(100, 600, 563)))
        self.assertFalse(self.g._secure(Ball(101, 500, 510)))
        self.assertIsNone(self.g.held_id)

    def test_open_claw_never_magnetically_attaches(self):
        self.g.close_amount = 0
        self.assertFalse(self.g._secure(Ball(100, 500, 563)))

    def test_supported_ball_can_lock_on_last_lift_step_and_stay_held_at_top(self):
        g = Game(11)
        g.claw_x = g.target_x = 500
        g.claw_y = REST_Y + 2.5
        g.close_amount = 1
        g.set_state(State.LIFT)
        ball = Ball(100, 500, g.claw_y+37, vy=-310)
        g.balls = [ball]
        self.assertTrue(g.finger_contact(ball, -1))
        self.assertTrue(g.finger_contact(ball, 1))
        g.update(FIXED_DT)
        self.assertEqual(g.state, State.CARRY)
        self.assertIs(g.held_ball, ball)
        self.assertEqual(g.misses, 0)
        for x in (900, BIN_CENTER, 700, BIN_CENTER):
            g.aim(x)
            advance_until(g, lambda: abs(g.claw_x-x)<.1)
            self.assertEqual(ball.mode, 'held')
            self.assertAlmostEqual(ball.y-g.claw_y, g.held_offset[1])
        for _ in range(120*5):
            g.update(FIXED_DT)
        self.assertEqual(g.state, State.CARRY)
        self.assertIs(g.held_ball, ball)

    def test_lifting_does_not_lock_single_finger_contacts_or_bullets(self):
        for dx, kind in ((38, 'ball'), (0, 'bullet')):
            g = Game(11)
            g.claw_x, g.claw_y = 500, 500
            g.close_amount = .62
            g.set_state(State.LIFT)
            g.balls = [Ball(100, 500+dx, 563, kind=kind)]
            g.update(FIXED_DT)
            self.assertIsNone(g.held_id)

    def test_real_round_supported_ball_is_secured_during_lift(self):
        # This replay previously lifted a two-finger-supported free ball, then
        # returned empty because its center stayed just outside the old pocket.
        g = Game(11)
        g.aim(830)
        for _ in range(round(1.6/FIXED_DT)):
            g.update(FIXED_DT)
        g.action()
        advance_until(g, lambda: g.state in (State.CARRY, State.MOVE))
        self.assertEqual(g.state, State.CARRY)
        self.assertTrue(g.grip_confirmed)
        self.assertEqual(g.misses, 0)

    def test_real_round_can_produce_successes_and_misses(self):
        results = []
        for x in (350, 430, 590, 900):
            g = Game(7)
            g.claw_x = g.target_x = x
            g.action()
            advance_until(g, lambda: g.state in (State.CARRY, State.MOVE))
            results.append(g.state)
        self.assertIn(State.CARRY, results)
        self.assertIn(State.MOVE, results)


class RoundTests(unittest.TestCase):
    def capture_at_known_contact(self, g, identity):
        g.claw_x, g.claw_y = 500, 500
        g.close_amount = .62
        ball = Ball(identity, 500, 563, color_index=identity % 6)
        g.balls = [ball]
        g.set_state(State.CLOSE)
        self.assertTrue(g._secure(ball))
        advance_until(g, lambda: g.state == State.CARRY)
        return ball

    def deliver(self, g):
        g.aim(BIN_CENTER)
        advance_until(g, lambda: abs(g.claw_x-BIN_CENTER) < .1)
        self.assertTrue(g.above_bin)
        g.action()
        self.assertEqual(g.state, State.DROP)
        advance_until(g, lambda: g.state in (State.MOVE, State.WON))

    def test_overhead_route_and_drop_award_exactly_once(self):
        g = Game(3)
        self.capture_at_known_contact(g, 50)
        self.assertLess(g.held_ball.y + g.held_ball.radius, BIN_TOP)
        g.aim(BIN_CENTER)
        advance_until(g, lambda: abs(g.claw_x-BIN_CENTER) < .1)
        g.action()
        self.assertEqual(len(g.collected), 0)
        for _ in range(20):
            g.action()  # rapid repeated clicks during delivery
        advance_until(g, lambda: g.state == State.MOVE)
        self.assertEqual(len(g.collected), 1)
        for _ in range(400):
            g.update(FIXED_DT)
        self.assertEqual(len(g.collected), 1)
        self.assertEqual(g.misses, 0)

    def test_unaligned_click_keeps_ball_held(self):
        g = Game(3)
        b = self.capture_at_known_contact(g, 50)
        g.action()
        self.assertEqual(g.state, State.CARRY)
        self.assertEqual(g.held_id, b.id)
        self.assertEqual(g.misses, 0)

    def test_three_valid_deliveries_win_and_restart_clears_all(self):
        g = Game(3)
        for i in range(3):
            self.capture_at_known_contact(g, 100+i)
            self.deliver(g)
        self.assertEqual(g.state, State.WON)
        self.assertEqual(len(g.collected), 3)
        g.action()
        self.assertEqual(g.state, State.MOVE)
        self.assertEqual((g.misses, g.attempts, len(g.collected)), (0, 0, 0))
        self.assertIsNone(g.held_id)
        self.assertIsNone(g.delivery_id)
        self.assertFalse(g.paused)
        self.assertEqual(g.gate, 0)
        self.assertEqual(len(g.balls), 14)

    def test_three_empty_grabs_lose_busy_clicks_do_not_add_attempts(self):
        g = Game(3)
        g.balls = []
        for expected in range(1, 4):
            g.action()
            for _ in range(20):
                g.action()
            self.assertEqual(g.attempts, expected)
            advance_until(g, lambda: g.state in (State.MOVE, State.LOST))
            self.assertEqual(g.misses, expected)
        self.assertEqual(g.state, State.LOST)

    def test_pause_freezes_everything_including_the_current_attempt(self):
        g = Game(3)
        g.action()
        g.toggle_pause()
        before = copy.deepcopy(g.__dict__)
        g.aim(300)
        g.action()
        g.update(.1)
        self.assertEqual((g.clock, g.claw_y, g.attempts), (before['clock'], before['claw_y'], before['attempts']))
        self.assertEqual([(b.x, b.y) for b in g.balls], [(b.x, b.y) for b in before['balls']])

    def test_restart_mid_grab_removes_stale_hold(self):
        g = Game(3)
        self.capture_at_known_contact(g, 50)
        g.reset()
        self.assertIsNone(g.held_id)
        self.assertEqual(g.state, State.MOVE)
        self.assertTrue(all(b.mode == 'free' for b in g.balls))


class EnvironmentTests(unittest.TestCase):
    def test_free_ball_cannot_enter_closed_or_open_guarded_bay(self):
        for opened in (False, True):
            g = Game(5)
            g.gate = float(opened)
            if opened:
                g.state, g.delivery_id, g.grip_confirmed = State.DROP, 999, True
            b = Ball(20, BIN_CENTER, BIN_TOP-80, vy=200)
            g.balls = [b]
            for _ in range(240):
                g.update(FIXED_DT)
                self.assertFalse(BIN_LEFT < b.x < BIN_RIGHT and b.y > BIN_TOP,
                                 'A free ball entered the protected collector.')
            self.assertEqual(g.collected, [])

    def test_forged_delivery_tag_cannot_score(self):
        g = Game(5)
        b = Ball(20, BIN_CENTER, FLOOR-30, mode='delivery')
        g.balls = [b]
        g.update(FIXED_DT)
        self.assertEqual(g.collected, [])
        self.assertEqual(b.mode, 'free')

    def test_nozzle_contact_pushes_upward_and_into_arena(self):
        g = Game(5)
        b = Ball(20, NOZZLE_LEFT+20, NOZZLE_TOP-RADIUS+1, vy=40)
        g.balls = [b]
        g.update(FIXED_DT)
        self.assertLess(b.vy, -500)
        self.assertLess(b.vx, 0)
        self.assertGreater(b.jet_cooldown, 0)

    def test_distant_ball_does_not_receive_jet_force(self):
        g = Game(5)
        b = Ball(20, 600, 400, vy=0)
        g.balls = [b]
        g.update(FIXED_DT)
        self.assertGreater(b.vy, 0)
        self.assertEqual(b.jet_cooldown, 0)

    def test_ball_collision_separates_and_reverses_approaching_velocities(self):
        a, b = Ball(1, 400, 500, vx=60), Ball(2, 446, 500, vx=-60)
        Game._pair(a, b)
        self.assertGreaterEqual(b.x-a.x, a.radius+b.radius)
        self.assertLess(a.vx, 0)
        self.assertGreater(b.vx, 0)

    def test_fixed_step_is_consistent_across_render_frame_rates(self):
        a, b = Game(5), Game(5)
        for _ in range(120):
            a.update(1/60)
        for _ in range(240):
            b.update(1/120)
        for first, second in zip(a.balls, b.balls):
            self.assertAlmostEqual(first.x, second.x, places=6)
            self.assertAlmostEqual(first.y, second.y, places=6)


if __name__ == '__main__':
    unittest.main()

