"""Deterministic game rules and a small circle/segment physics simulation.

No display or third-party package is needed to test this module.
The held-ball constraint is created only after opposing finger contacts.
"""
from dataclasses import dataclass, field
from enum import Enum
import math
import random


WIDTH, HEIGHT = 1440, 900
LEFT, RIGHT, CEILING, FLOOR = 58.0, 1030.0, 190.0, 746.0
BIN_LEFT, BIN_RIGHT, BIN_TOP = 78.0, 274.0, 554.0
BIN_CENTER = (BIN_LEFT + BIN_RIGHT) / 2
NOZZLE_LEFT, NOZZLE_RIGHT, NOZZLE_TOP = 910.0, 994.0, 699.0
REST_Y, MAX_Y = 230.0, FLOOR - 84.0
RADIUS, GRAVITY, FINGER_RADIUS = 24.0, 365.0, 5.0
FIXED_DT = 1 / 120
BULLET_TIME_SCALE = 0.83
BULLET_TIME_USES = 3
PALETTE = (
    ("CORAL", (248, 111, 106)), ("SKY", (72, 152, 234)),
    ("LEMON", (249, 201, 78)), ("MINT", (75, 190, 161)),
    ("LILAC", (167, 133, 211)), ("PEACH", (246, 163, 95)),
)


class State(str, Enum):
    MOVE = "move"
    LOWER = "lower"
    CLOSE = "close"
    LIFT = "lift"
    CARRY = "carry"
    DROP = "drop"
    WON = "won"
    LOST = "lost"


@dataclass
class Ball:
    id: int
    x: float
    y: float
    vx: float = 0
    vy: float = 0
    radius: float = RADIUS
    color_index: int = 0
    mode: str = "free"
    jet_cooldown: float = 0
    trail: list = field(default_factory=list)
    kind: str = "ball"

    @property
    def color(self):
        return PALETTE[self.color_index % len(PALETTE)][1]

    @property
    def name(self):
        return PALETTE[self.color_index % len(PALETTE)][0]


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def approach(value, goal, distance):
    return value + clamp(goal - value, -distance, distance)


def closest_on_segment(x, y, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = clamp(((x - a[0]) * dx + (y - a[1]) * dy) / length2, 0, 1) if length2 else 0
    return a[0] + dx * t, a[1] + dy * t


def distance_to_segment(x, y, a, b):
    px, py = closest_on_segment(x, y, a, b)
    return math.hypot(x - px, y - py)


class Game:
    """A round: aim -> lower/close/lift -> carry -> guarded delivery.

    A stable two-finger geometric grip creates a simplified kinematic hold.
    There are no dice rolls, nearest-ball teleports, or automatic successes.
    """
    def __init__(self, seed=None, level=1):
        self.level = level
        self.seed = seed
        self.round_number = 0
        self.reset()

    def reset(self):
        self.round_number += 1
        self.rng = random.Random(None if self.seed is None else self.seed + self.round_number - 1)
        self.balls = []
        for row in range(2):
            for col in range(7):
                self.balls.append(Ball(
                    id=row * 7 + col,
                    x=340 + col * 88 + self.rng.uniform(-8, 8),
                    y=470 + row * 99 + self.rng.uniform(-10, 10),
                    vx=self.rng.uniform(-55, 65), vy=self.rng.uniform(-35, 15),
                    color_index=(row * 7 + col) % len(PALETTE),
                ))
        if self.level > 1:
            self.balls = []
        self.spawn_timer = 0.8
        self.spawn_count = 0
        self.events = []
        self.state = State.MOVE
        self.claw_x, self.claw_y, self.target_x = 600.0, REST_Y, 600.0
        self.close_amount = 0.0
        self.held_id = None
        self.held_offset = (0.0, 61.0)
        self.delivery_id = None
        self.collected = []
        self.misses = 0
        self.attempts = 0
        self.paused = False
        self.bullet_time_left = BULLET_TIME_USES if self.level == 3 else 0
        self.bullet_time_held = False
        self.clock = 0.0
        self.state_time = 0.0
        self.accumulator = 0.0
        self.gate = 0.0
        self.jet_flash = 0.0
        self.message = "Aim with your mouse. Click when a ball is in reach."
        self.contact_left = False
        self.contact_right = False
        self.grip_confirmed = False

    @property
    def held_ball(self):
        return next((b for b in self.balls if b.id == self.held_id), None)

    @property
    def terminal(self):
        return self.state in (State.WON, State.LOST)

    @property
    def bullet_time_active(self):
        return self.level == 3 and self.bullet_time_held and not self.paused and not self.terminal

    def start_bullet_time(self):
        if self.level != 3 or self.paused or self.terminal or self.bullet_time_held or self.bullet_time_left <= 0:
            return False
        self.bullet_time_left -= 1
        self.bullet_time_held = True
        return True

    def end_bullet_time(self):
        self.bullet_time_held = False

    def set_paused(self, paused):
        self.paused = paused
        self.accumulator = 0.0
        if paused:
            self.end_bullet_time()

    @property
    def can_start_grab(self):
        return not self.paused and self.state == State.MOVE and self.claw_x >= BIN_RIGHT + 58

    @property
    def above_bin(self):
        ball = self.held_ball
        return bool(ball and BIN_LEFT + 18 + ball.radius <= ball.x <= BIN_RIGHT - 18 - ball.radius)

    @property
    def stage(self):
        if self.state == State.MOVE:
            return 1
        if self.state in (State.LOWER, State.CLOSE, State.LIFT):
            return 2
        return 3 if self.state in (State.CARRY, State.DROP, State.WON) else 2

    def set_state(self, state):
        self.state = state
        self.state_time = 0.0
        if self.terminal:
            self.end_bullet_time()

    def aim(self, x):
        if not self.paused and self.state in (State.MOVE, State.CARRY):
            self.target_x = clamp(x, LEFT + 60, RIGHT - 60)

    def action(self):
        if self.terminal:
            self.reset()
            return
        if self.paused:
            return
        if self.state == State.MOVE:
            # A grab cannot start over the protected collector.
            if self.claw_x < BIN_RIGHT + 58:
                self.message = "The left bay is for delivery. Move right to grab."
                return
            self.attempts += 1
            self.grip_confirmed = False
            self.contact_left = self.contact_right = False
            self.set_state(State.LOWER)
            self.message = "Claw lowering. Watch the ball enter between the fingers."
        elif self.state == State.CARRY:
            if not self.above_bin:
                self.message = "Carry your ball LEFT, above the marked DROP opening."
                return
            ball = self.held_ball
            if not ball or not self.grip_confirmed:
                return
            self.delivery_id = ball.id
            ball.mode = "delivery"
            ball.vx = ball.vy = 0.0
            self.held_id = None
            self.set_state(State.DROP)
            self.message = "Hatch open. A catch counts when it reaches the collection tray."
        # Busy clicks have no effect and can never add extra attempts/misses.

    def toggle_pause(self):
        if not self.terminal:
            self.set_paused(not self.paused)

    def jaw_points(self, side):
        p = self.close_amount
        return (
            (self.claw_x + side * 13, self.claw_y),
            (self.claw_x + side * (53 - 22 * p), self.claw_y + 35),
            (self.claw_x + side * (43 - 35 * p), self.claw_y + 81),
        )

    def finger_contact(self, ball, side):
        points = self.jaw_points(side)
        # Only the lower inward finger can support a ball. The upper arm cannot grab.
        return distance_to_segment(ball.x, ball.y, points[1], points[2]) <= ball.radius + FINGER_RADIUS + 1.5

    def valid_grip(self, ball):
        dx, dy = ball.x - self.claw_x, ball.y - self.claw_y
        tip_gap = 2 * (43 - 35 * self.close_amount - FINGER_RADIUS)
        return (
            ball.mode == "free" and ball.kind == "ball" and self.close_amount >= 0.35
            and abs(dx) <= ball.radius * 0.75
            and 36 <= dy <= 75
            and self.claw_y + 81 > ball.y + ball.radius * 0.25
            and tip_gap < ball.radius * 1.85
            and self.finger_contact(ball, -1) and self.finger_contact(ball, 1)
        )

    def _secure(self, ball):
        if not self.valid_grip(ball):
            return False
        self.held_id = ball.id
        self.held_offset = (ball.x - self.claw_x, ball.y - self.claw_y)
        ball.mode = "held"
        ball.vx = ball.vy = 0.0
        self.contact_left = self.contact_right = True
        self.grip_confirmed = True
        self.message = "Both fingers made contact. Lifting your catch."
        return True

    def update(self, elapsed):
        if self.paused or self.terminal:
            return
        self.accumulator += min(max(elapsed, 0.0), 0.1)
        while self.accumulator >= FIXED_DT:
            self._step(FIXED_DT)
            self.accumulator -= FIXED_DT
            if self.terminal:
                self.accumulator = 0.0
                break

    def _step(self, dt):
        world_dt = dt * (BULLET_TIME_SCALE if self.bullet_time_active else 1)
        if self.level > 1:
            self._spawn_stream(world_dt)
        self.clock += dt
        self.state_time += dt
        self.jet_flash = max(0.0, self.jet_flash - dt)
        self.gate = approach(self.gate, float(self.state == State.DROP), dt * 5)
        if self.state in (State.MOVE, State.CARRY):
            self.claw_x = approach(self.claw_x, self.target_x, 510 * dt)
        if self.state == State.MOVE:
            self.close_amount = approach(self.close_amount, 0, 4 * dt)
        elif self.state == State.LOWER:
            self.claw_y = min(MAX_Y, self.claw_y + 255 * dt)
            # Close when a real ball enters the open pocket, or at the bottom.
            inside = any(b.mode == "free" and abs(b.x - self.claw_x) < 29
                         and abs(b.y - self.claw_y - 58) < 11 for b in self.balls)
            if self.claw_y >= MAX_Y or (self.state_time > 0.20 and inside):
                self.set_state(State.CLOSE)
                self.message = "Closing fingers. Contact and timing decide the catch."
        elif self.state == State.CLOSE:
            if self.held_id is None:
                closing_time = .38 if self.level == 1 else .12
                self.close_amount = min(1.0, self.close_amount + dt / closing_time)
            if self.state_time > 0.48:
                self.set_state(State.LIFT)
                if self.held_id is None:
                    self.message = "Empty grip. Returning to the rail."
        elif self.state == State.LIFT:
            self.claw_y = max(REST_Y, self.claw_y - 310 * dt)
        elif self.state == State.DROP:
            self.close_amount = approach(self.close_amount, 0, dt * 5)

        held = self.held_ball
        if held:
            held.x = self.claw_x + self.held_offset[0]
            held.y = self.claw_y + self.held_offset[1]

        for b in list(self.balls):
            if b.mode == "held":
                continue
            ball_dt = dt if b.mode == "delivery" else world_dt
            b.jet_cooldown = max(0.0, b.jet_cooldown - ball_dt)
            b.vy = min(800, b.vy + (GRAVITY if self.level == 1 or b.mode == "delivery" else (0 if b.kind == "bullet" else 22)) * ball_dt)
            b.x += b.vx * ball_dt
            b.y += b.vy * ball_dt
            if b.mode == "delivery":
                self._delivery(b)
                continue
            if self.level > 1:
                if b.x >= 972:
                    self.balls.remove(b)
                    continue
                self._stream_walls(b)
            else:
                self._walls(b, ball_dt)
                self._nozzle(b)
            self._bin_guard(b)

        free = [b for b in self.balls if b.mode == "free" and b.kind == "ball"]
        for _ in range(2):
            for i, a in enumerate(free):
                for b in free[i + 1:]:
                    self._pair(a, b)
            for b in free:
                self._bin_guard(b)
                b.x = clamp(b.x, LEFT + b.radius, RIGHT - b.radius)
                b.y = clamp(b.y, CEILING + b.radius, FLOOR - b.radius)

        if self.state in (State.CLOSE, State.LIFT) and self.held_id is None:
            # Evaluate actual opposing contacts before resolving penetrations.
            # A supported ball may settle into a valid grip during the lift.
            for b in free:
                if self._secure(b):
                    break
        if self.state in (State.LOWER, State.CLOSE, State.LIFT):
            for b in free:
                if b.mode != "free":
                    continue
                for side in (-1, 1):
                    points = self.jaw_points(side)
                    self._finger_collision(b, points[0], points[1])
                    self._finger_collision(b, points[1], points[2])

        # Resolve the top arrival after checking contacts, including this last
        # lift step. A confirmed hold remains locked until an authorized DROP.
        if self.state == State.LIFT and self.claw_y <= REST_Y:
            if self.held_id is not None:
                self.set_state(State.CARRY)
                self.target_x = self.claw_x
                self.message = "Caught! Move LEFT to DROP, then click to release."
            else:
                self.misses += 1
                self.events.append(("miss", None))
                self.set_state(State.LOST if self.misses == 3 else State.MOVE)
                self.message = "Three empty grabs. Try a new round." if self.terminal else "Missed this time. Aim ahead of a moving ball."
        for b in free:
            if int(self.clock * 120) % 4 == 0:
                b.trail.append((b.x, b.y))
                del b.trail[:-7]

    @property
    def jet_heights(self):
        return (350, 420, 490) if self.level == 2 else (335, 430, 510)

    def _spawn_stream(self, dt):
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return
        self.spawn_timer += 1.05 if self.level == 2 else .78
        lane = self.spawn_count % 3
        # Every fourth launch is a bullet; regular balls always remain available.
        bullet = self.level == 3 and self.spawn_count % 4 == 3
        speed = self.rng.uniform(320, 380) if self.level == 2 else self.rng.uniform(540, 640)
        self.balls.append(Ball(
            1000 + self.spawn_count, 166, self.jet_heights[lane],
            vx=speed + (140 if bullet else 0),
            vy=0 if self.level == 2 or bullet else (-35, 5, -20)[lane],
            radius=15 if bullet else RADIUS,
            color_index=self.spawn_count % len(PALETTE), kind="bullet" if bullet else "ball",
        ))
        self.spawn_count += 1

    def _stream_walls(self, b):
        # Floor and bay deflections still feed the full-height recycler.
        if b.x < LEFT + b.radius:
            b.x, b.vx = LEFT + b.radius, abs(b.vx)
        if b.y < CEILING + b.radius:
            b.y, b.vy = CEILING + b.radius, abs(b.vy)
        if b.y > FLOOR - b.radius:
            b.y, b.vy = FLOOR - b.radius, -abs(b.vy) * .35
            b.vx = max(b.vx, 95 if self.level == 2 else 150)

    def _walls(self, b, dt):
        r = b.radius
        if b.x < LEFT + r:
            b.x, b.vx = LEFT + r, abs(b.vx) * 0.82
        elif b.x > RIGHT - r:
            b.x, b.vx = RIGHT - r, -abs(b.vx) * 0.82
        if b.y < CEILING + r:
            b.y, b.vy = CEILING + r, abs(b.vy) * 0.7
        if b.y >= FLOOR - r:
            b.y = FLOOR - r
            b.vy = -abs(b.vy) * 0.72 if abs(b.vy) > 32 else 0
            # A gentle rightward floor drift feeds the air jet after settling.
            b.vx = min(135, b.vx * 0.998 + 24 * dt)

    def _bin_guard(self, b):
        """The guarded bay is solid to ordinary balls even during authorized delivery.

        Only the single previously gripped delivery ball has permission to enter.
        The opening is well below the overhead carry corridor.
        """
        x = clamp(b.x, BIN_LEFT, BIN_RIGHT)
        y = clamp(b.y, BIN_TOP, FLOOR + 20)
        dx, dy = b.x - x, b.y - y
        distance = math.hypot(dx, dy)
        if distance >= b.radius:
            return
        if distance < 1e-8:
            # Defensive resolution, including loaded test/paused-overlap states.
            if b.y - BIN_TOP < BIN_RIGHT - b.x:
                b.y, b.vy = BIN_TOP - b.radius, -abs(b.vy) * 0.7
            else:
                b.x, b.vx = BIN_RIGHT + b.radius, abs(b.vx) * 0.7
            return
        nx, ny = dx / distance, dy / distance
        b.x += nx * (b.radius - distance)
        b.y += ny * (b.radius - distance)
        speed = b.vx * nx + b.vy * ny
        if speed < 0:
            b.vx -= 1.7 * speed * nx
            b.vy -= 1.7 * speed * ny
        # Balls resting on the lid roll back toward the arena.
        if ny < -0.5:
            b.vx = max(b.vx, 45)

    def _nozzle(self, b):
        px = clamp(b.x, NOZZLE_LEFT, NOZZLE_RIGHT)
        py = clamp(b.y, NOZZLE_TOP, FLOOR + 8)
        if math.hypot(b.x - px, b.y - py) <= b.radius + 2 and b.jet_cooldown <= 0:
            b.y = min(b.y, NOZZLE_TOP - b.radius - 2)
            b.vy = -self.rng.uniform(540, 635)
            b.vx = -self.rng.uniform(110, 210)
            b.jet_cooldown = 0.65
            self.jet_flash = 0.38

    @staticmethod
    def _pair(a, b):
        dx, dy = b.x - a.x, b.y - a.y
        distance = math.hypot(dx, dy)
        radii = a.radius + b.radius
        if distance >= radii:
            return
        nx, ny = (dx / distance, dy / distance) if distance > 1e-8 else (1.0, 0.0)
        correction = (radii - distance) / 2 + 0.005
        a.x -= nx * correction
        a.y -= ny * correction
        b.x += nx * correction
        b.y += ny * correction
        relative = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
        if relative < 0:
            impulse = -(1 + 0.82) * relative / 2
            a.vx -= impulse * nx
            a.vy -= impulse * ny
            b.vx += impulse * nx
            b.vy += impulse * ny

    @staticmethod
    def _finger_collision(ball, a, b):
        px, py = closest_on_segment(ball.x, ball.y, a, b)
        dx, dy = ball.x - px, ball.y - py
        distance = math.hypot(dx, dy)
        limit = ball.radius + FINGER_RADIUS
        if not 1e-6 < distance < limit:
            return
        nx, ny = dx / distance, dy / distance
        ball.x += nx * (limit - distance)
        ball.y += ny * (limit - distance)
        speed = ball.vx * nx + ball.vy * ny
        if speed < 0:
            ball.vx -= 1.2 * speed * nx
            ball.vy -= 1.2 * speed * ny

    def _delivery(self, ball):
        # A tag alone is insufficient: the current verified grip must authorize it.
        if ball.id != self.delivery_id or not self.grip_confirmed or self.state != State.DROP:
            ball.mode = "free"
            self._bin_guard(ball)
            return
        ball.x = clamp(ball.x, BIN_LEFT + 18 + ball.radius, BIN_RIGHT - 18 - ball.radius)
        if ball.y >= FLOOR - ball.radius - 14:
            self.collected.append((ball.color_index, ball.id))
            self.events.append(("delivery", ball.color_index))
            self.balls.remove(ball)
            self.delivery_id = None
            self.grip_confirmed = False
            self.gate = 0
            self.set_state(State.WON if len(self.collected) == 3 else State.MOVE)
            self.message = "Three collected. Your collection is complete!" if self.terminal else "Delivered! Move back into the arena for your next catch."

