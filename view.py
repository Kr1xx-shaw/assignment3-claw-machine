"""Flat, resolution-independent game illustration drawn from primitives.

All labels are English. No generated bitmap is used as a gameplay background:
the gate, claw and balls are drawn at their actual simulation positions.
"""
import math
import pygame
import pygame.gfxdraw

from model import (
    WIDTH, HEIGHT, LEFT, RIGHT, CEILING, FLOOR,
    BIN_LEFT, BIN_RIGHT, BIN_TOP, BIN_CENTER,
    NOZZLE_LEFT, NOZZLE_RIGHT, NOZZLE_TOP,
    State, PALETTE, clamp,
)

INK = (27, 45, 66)
CREAM = (249, 247, 237)
PAPER = (255, 253, 246)
BLUE = (211, 236, 246)
MID_BLUE = (149, 193, 213)
STEEL = (170, 196, 206)
ORANGE = (249, 147, 80)
GREEN = (59, 158, 130)
RED = (218, 97, 91)
MUTED = (103, 124, 135)
ACTION_RECT = pygame.Rect(1102, 687, 282, 62)
RESTART_RECT = pygame.Rect(1254, 39, 154, 39)
REPLAY_RECT = pygame.Rect(362, 497, 364, 62)
ARENA_RECT = pygame.Rect(38, 132, 1016, 650)


def mix(a, b, fraction):
    return tuple(round(x + (y - x) * fraction) for x, y in zip(a, b))


class View:
    def __init__(self):
        pygame.font.init()
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.fonts = {}

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont('segoeui', size, bold=bold)
        return self.fonts[key]

    def text(self, text, x, y, size=20, color=INK, bold=False, center=False):
        image = self.font(size, bold).render(text, True, color)
        rect = image.get_rect(midtop=(round(x), round(y))) if center else image.get_rect(topleft=(round(x), round(y)))
        self.canvas.blit(image, rect)
        return rect

    def box(self, rect, fill, radius=14, border=INK, width=2, shadow=False):
        rect = pygame.Rect(rect)
        if shadow:
            pygame.draw.rect(self.canvas, (206, 214, 210), rect.move(0, 5), border_radius=radius)
        pygame.draw.rect(self.canvas, fill, rect, border_radius=radius)
        if border and width:
            pygame.draw.rect(self.canvas, border, rect, width, border_radius=radius)

    def line(self, a, b, color=INK, width=2):
        pygame.draw.line(self.canvas, color, a, b, width)

    def circle(self, x, y, r, color, border=True):
        x, y, r = round(x), round(y), round(r)
        if border:
            pygame.gfxdraw.filled_circle(self.canvas, x, y, r + 2, INK)
            pygame.gfxdraw.aacircle(self.canvas, x, y, r + 2, INK)
        pygame.gfxdraw.filled_circle(self.canvas, x, y, r, color)
        pygame.gfxdraw.aacircle(self.canvas, x, y, r, color)

    def ball(self, x, y, radius, color):
        self.circle(x, y, radius, color)
        # One flat shadow arc and one flat spot; no gradients or shiny textures.
        r = round(radius)
        pygame.draw.arc(self.canvas, mix(color, INK, .17),
                        pygame.Rect(round(x-r+3), round(y-r+3), 2*r-6, 2*r-6),
                        math.pi, 2*math.pi, max(3, r//6))
        self.circle(x - r * .30, y - r * .35, max(3, r * .20), mix(color, PAPER, .78), False)

    def dashed_circle(self, x, y, radius):
        for i in range(12):
            angle = i * math.tau / 12
            pygame.draw.arc(self.canvas, MID_BLUE,
                            pygame.Rect(x-radius, y-radius, 2*radius, 2*radius),
                            angle, angle+.27, 2)

    def draw(self, game, mouse=None):
        self.canvas.fill(CREAM)
        self.header(game)
        self.machine(game)
        self.sidebar(game, mouse)
        self.footer(game)
        if game.paused or game.terminal:
            self.overlay(game)
        return self.canvas

    def header(self, game):
        self.text('CLAW MACHINE', 34, 30, 36, bold=True)
        self.text('AIM WELL. CATCH THREE.', 37, 78, 13, MUTED, bold=True)
        for i, word in enumerate(('MOVE', 'GRAB', 'DROP'), 1):
            rect = pygame.Rect(450 + (i-1)*207, 39, 183, 46)
            active = i == game.stage and not game.terminal
            self.box(rect, ORANGE if active else BLUE, radius=23)
            self.text(f'{i}. {word}', rect.centerx, rect.y+8, 23, bold=True, center=True)
            if i < 3:
                x = rect.right + 9
                pygame.draw.lines(self.canvas, MUTED, False, ((x, 56), (x+7, 62), (x, 68)), 2)
        self.box(RESTART_RECT, PAPER, 19, MID_BLUE)
        self.text('RESTART  /  R', RESTART_RECT.centerx, RESTART_RECT.y+10, 14, bold=True, center=True)

    def machine(self, g):
        self.box((32, 118, 1024, 664), MID_BLUE, 22, shadow=True)
        self.box((44, 130, 1000, 640), BLUE, 15)
        old_clip = self.canvas.get_clip()
        self.canvas.set_clip(pygame.Rect(56, 143, 976, 625))
        # A few flat glass marks suggest a cabinet without disguising collision bounds.
        pygame.draw.polygon(self.canvas, (223, 243, 249), [(70, 192), (250, 192), (70, 382)])
        pygame.draw.polygon(self.canvas, (223, 243, 249), [(1029, 300), (1029, 372), (805, 595), (737, 595)])
        for x in range(338, 1010, 56):
            for y in range(349, 693, 56):
                self.circle(x, y, 1, (181, 217, 232), False)
        pygame.draw.rect(self.canvas, (192, 218, 222), (LEFT, FLOOR-2, RIGHT-LEFT, 28))
        self.line((LEFT, FLOOR), (RIGHT, FLOOR), INK, 3)
        # Small rightward floor arrows explain how settled balls return to the jet.
        for x in (355, 500, 645, 790):
            pygame.draw.lines(self.canvas, (141, 175, 181), False,
                              [(x, 756), (x+28, 756), (x+21, 752)], 2)
        self.nozzle(g)
        for b in g.balls:
            if b.mode == 'free':
                if len(b.trail) >= 3 and math.hypot(b.vx, b.vy) > 150:
                    points = b.trail[-5:]
                    pygame.draw.lines(self.canvas, mix(b.color, BLUE, .68), False, points, 3)
                self.ball(b.x, b.y, b.radius, b.color)
        self.bin(g)
        self.rail(g)
        self.claw(g)
        # Authorized deliveries pass through the REAL opening, drawn on top of its floor.
        for b in g.balls:
            if b.mode == 'delivery':
                self.ball(b.x, b.y, b.radius, b.color)
        if g.state == State.MOVE:
            self.aim_guide(g)
        if g.state == State.CARRY:
            color = GREEN if g.above_bin else MUTED
            self.text('CLICK TO DROP' if g.above_bin else 'CARRY LEFT TO DROP',
                      g.claw_x, g.claw_y+112, 13, color, True, True)
            if g.above_bin:
                for y in range(round(g.claw_y+147), int(BIN_TOP)-22, 23):
                    self.line((BIN_CENTER, y), (BIN_CENTER, y+10), GREEN, 3)
                pygame.draw.polygon(self.canvas, GREEN, [(BIN_CENTER-8, BIN_TOP-27), (BIN_CENTER+8, BIN_TOP-27), (BIN_CENTER, BIN_TOP-16)])
        self.canvas.set_clip(old_clip)

    def rail(self, g):
        self.box((80, 151, 930, 17), STEEL, 8, width=2)
        self.line((96, 157), (991, 157), PAPER, 2)
        self.box((71, 141, 21, 37), INK, 7, width=0)
        self.box((998, 141, 21, 37), INK, 7, width=0)
        self.box((g.claw_x-35, 139, 70, 43), (177, 206, 218), 9)
        self.box((g.claw_x-24, 147, 48, 23), PAPER, 4, MID_BLUE, 1)
        self.line((g.claw_x, 182), (g.claw_x, g.claw_y-17), INK, 5)
        for y in range(189, int(g.claw_y)-19, 10):
            self.line((g.claw_x-4, y), (g.claw_x+4, y+2), MUTED, 2)

    def claw(self, g):
        held = g.held_ball
        if held:
            self.ball(held.x, held.y, held.radius, held.color)
        self.box((g.claw_x-19, g.claw_y-19, 38, 31), STEEL, 7)
        for side in (-1, 1):
            a, b, c = g.jaw_points(side)
            points = [(round(x), round(y)) for x, y in (a, b, c)]
            pygame.draw.lines(self.canvas, INK, False, points, 14)
            pygame.draw.lines(self.canvas, PAPER, False, points, 8)
            for point in points:
                self.circle(*point, 4, STEEL)
            if held:
                self.circle(*points[-1], 3, GREEN, False)

    def bin(self, g):
        left, right, top = BIN_LEFT, BIN_RIGHT, BIN_TOP
        # This short bay ends at BIN_TOP: the entire area above is shared open space.
        self.box((left, top, right-left, FLOOR-top), PAPER, 8)
        self.box((left+14, top+58, right-left-28, FLOOR-top-72), (220, 237, 231), 7, MID_BLUE, 1)
        self.text('DROP', BIN_CENTER, top+17, 24, bold=True, center=True)
        self.text('GUARDED COLLECTION BAY', BIN_CENTER, top+49, 9, MUTED, True, True)
        for i, (color_index, _) in enumerate(g.collected):
            self.ball(left+43+i*54, FLOOR-37, 19, PALETTE[color_index][1])
        # Actual top opening extends between the side posts; moving lids retract outwards.
        self.box((left-4, top-6, 13, FLOOR-top+8), STEEL, 3)
        self.box((right-9, top-6, 13, FLOOR-top+8), STEEL, 3)
        opening_left, opening_right = left+9, right-9
        half = (opening_right-opening_left)/2
        gap = g.gate * (half-8)
        self.box((opening_left, top-8, max(8, half-gap), 13), STEEL, 3)
        self.box((BIN_CENTER+gap, top-8, max(8, half-gap), 13), STEEL, 3)
        if g.state == State.DROP:
            self.text('OPEN', BIN_CENTER, top-35, 12, GREEN, True, True)
            # Visible guard line: only the current delivered ball enters this slot.
            self.line((opening_left+4, top+5), (opening_right-4, top+5), (126, 196, 168), 2)
        else:
            self.text('OPENS FOR YOUR CATCH', BIN_CENTER, top-35, 11, MUTED, True, True)
            self.circle(BIN_CENTER, top-2, 3, GREEN, False)

    def nozzle(self, g):
        x = (NOZZLE_LEFT + NOZZLE_RIGHT)/2
        for offset in (-18, 0, 18):
            length = 46 + 15*math.sin(g.clock*4 + offset)
            if g.jet_flash:
                length += 30
            base = (x+offset, NOZZLE_TOP-9)
            tip = (x+offset-6, NOZZLE_TOP-length)
            self.line(base, tip, (111, 185, 203), 3)
            self.line(tip, (tip[0]-4, tip[1]+9), (111, 185, 203), 3)
            self.line(tip, (tip[0]+5, tip[1]+8), (111, 185, 203), 3)
        self.box((NOZZLE_LEFT, NOZZLE_TOP, NOZZLE_RIGHT-NOZZLE_LEFT, FLOOR-NOZZLE_TOP), STEEL, 8)
        self.box((NOZZLE_LEFT-7, FLOOR-10, NOZZLE_RIGHT-NOZZLE_LEFT+14, 13), PAPER, 5)
        self.box((NOZZLE_LEFT+5, NOZZLE_TOP-5, NOZZLE_RIGHT-NOZZLE_LEFT-10, 11), INK, 5, width=0)
        for dx in range(-26, 30, 9):
            self.line((x+dx, NOZZLE_TOP-4), (x+dx, NOZZLE_TOP+5), STEEL, 2)
        self.text('AIR JET', x, NOZZLE_TOP+13, 12, bold=True, center=True)

    def aim_guide(self, g):
        if g.claw_x <= BIN_RIGHT+58:
            return
        for y in range(round(g.claw_y+110), int(FLOOR)-18, 22):
            self.line((g.claw_x, y), (g.claw_x, y+5), (164, 199, 210), 2)
        self.line((g.claw_x-13, FLOOR-10), (g.claw_x+13, FLOOR-10), MUTED, 2)

    def sidebar(self, g, mouse):
        self.box((1080, 118, 328, 664), PAPER, 22, shadow=True)
        self.text('YOUR COLLECTION', 1244, 146, 23, bold=True, center=True)
        self.text('Catch something worth keeping.', 1244, 179, 14, MUTED, center=True)
        self.text('COLLECTED', 1104, 213, 14, MUTED, True)
        self.text(f'{len(g.collected)} / 3', 1329, 204, 24, bold=True)
        for i in range(3):
            y = 252 + i*96
            filled = i < len(g.collected)
            self.box((1102, y, 282, 82), (234, 242, 235) if filled else (239, 244, 244), 14, MID_BLUE, 1)
            if filled:
                color_index, _ = g.collected[i]
                name, color = PALETTE[color_index]
                self.ball(1147, y+41, 23, color)
                self.text(name, 1190, y+18, 17, bold=True)
                self.text('Safely delivered', 1190, y+43, 13, MUTED)
                self.text(f'0{i+1}', 1348, y+31, 13, MUTED)
            else:
                self.dashed_circle(1147, y+41, 24)
                self.text(f'SLOT 0{i+1}', 1190, y+19, 16, MUTED, True)
                self.text('Waiting for your catch', 1190, y+43, 12, MUTED)
        self.line((1104, 548), (1383, 548), MID_BLUE, 1)
        self.text('MISSES', 1104, 567, 15, bold=True)
        self.text(f'{g.misses} / 3', 1331, 561, 22, bold=True)
        for i in range(3):
            x = 1120+i*41
            self.circle(x, 618, 13, RED if i<g.misses else PAPER, border=True)
            if i < g.misses:
                self.line((x-4, 614), (x+4, 622), PAPER, 2)
                self.line((x+4, 614), (x-4, 622), PAPER, 2)
        self.text('Collect 3 to win. 3 misses end the round.', 1104, 649, 12, MUTED)

        if g.terminal:
            label, enabled = 'PLAY AGAIN', True
        elif g.paused:
            label, enabled = 'PAUSED', False
        elif g.state == State.MOVE:
            label, enabled = 'GRAB', True
        elif g.state == State.CARRY:
            label, enabled = ('DROP BALL' if g.above_bin else 'MOVE LEFT TO DROP'), True
        else:
            label, enabled = {State.LOWER:'LOWERING...', State.CLOSE:'CLOSING...', State.LIFT:'LIFTING...', State.DROP:'DELIVERING...'}[g.state], False
        hovered = mouse and ACTION_RECT.collidepoint(mouse)
        fill = ORANGE if enabled else (221, 227, 225)
        if enabled and hovered:
            fill = mix(fill, PAPER, .20)
        self.box(ACTION_RECT, fill, 14)
        self.text(label, ACTION_RECT.centerx, ACTION_RECT.y+17, 21 if len(label)<16 else 17, bold=True, center=True)

    def footer(self, g):
        self.box((32, 806, 1376, 65), PAPER, 16)
        self.circle(57, 831, 5, ORANGE if g.paused else GREEN, False)
        self.text('Paused. Press SPACE to continue.' if g.paused else g.message, 74, 816, 18, bold=True)
        self.text('MOUSE to aim   /   CLICK to grab or drop   /   SPACE to pause   /   R to restart', 74, 845, 13, MUTED)
        self.text(f'ROUND {g.round_number:02}', 1313, 848, 11, MUTED, True)

    def overlay(self, g):
        veil = pygame.Surface((1000, 640), pygame.SRCALPHA)
        veil.fill((230, 241, 240, 208))
        self.canvas.blit(veil, (44, 130))
        rect = pygame.Rect(242, 315, 604, 280)
        self.box(rect, PAPER, 24, shadow=True)
        if g.paused:
            title, subtitle, hint = 'TAKE A BREATHER', 'Your round is safely paused.', 'Press SPACE to continue'
            self.text(title, 544, 359, 33, bold=True, center=True)
            self.text(subtitle, 544, 417, 20, MUTED, center=True)
            self.text(hint, 544, 491, 18, GREEN, True, True)
        else:
            won = g.state == State.WON
            title = 'COLLECTION COMPLETE!' if won else 'OUT OF GRABS'
            self.text(title, 544, 357, 31, GREEN if won else RED, True, True)
            miss_word = 'miss' if g.misses == 1 else 'misses'
            self.text(f'{len(g.collected)} collected  /  {g.misses} {miss_word}', 544, 416, 20, MUTED, center=True)
            self.box(REPLAY_RECT, ORANGE, 15)
            self.text('PLAY AGAIN', REPLAY_RECT.centerx, REPLAY_RECT.y+17, 22, bold=True, center=True)

