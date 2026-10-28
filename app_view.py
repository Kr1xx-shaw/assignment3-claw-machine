"""English campaign screens, drawn with the same flat illustration primitives."""
import pygame

from campaign import ENTRY_COST, LEVEL_NAMES
from model import State, PALETTE
from view import View, INK, CREAM, PAPER, BLUE, MID_BLUE, ORANGE, GREEN, RED, MUTED, STEEL, mix


class AppView(View):
    def __init__(self):
        super().__init__()
        self.buttons = {}
        self.app = None
        self.mouse = None

    def button(self, name, label, rect, fill=ORANGE, enabled=True, size=21):
        rect = pygame.Rect(rect)
        color = fill if enabled else (224, 229, 225)
        if enabled and self.mouse and rect.collidepoint(self.mouse):
            color = mix(color, PAPER, .22)
        self.box(rect, color, 14, INK if enabled else MID_BLUE)
        self.text(label, rect.centerx, rect.centery-size*.72, size, INK if enabled else MUTED, True, True)
        if enabled:
            self.buttons[name] = rect

    def hit(self, point):
        return next((name for name, rect in self.buttons.items() if rect.collidepoint(point)), None)

    def draw_app(self, app, mouse=None):
        self.app, self.mouse = app, mouse
        self.buttons = {}
        self.canvas.fill(CREAM)
        if app.screen == 'play':
            self.header(app.game)
            self.machine(app.game)
            self.sidebar(app.game, mouse)
            self.footer(app.game)
            if app.game.paused:
                self.pause_panel()
        elif app.screen == 'menu':
            self.menu()
        elif app.screen == 'result':
            self.result()
        elif app.screen == 'help':
            self.help_page()
        elif app.screen == 'briefing':
            self.briefing()
        elif app.screen == 'retry':
            self.dialog('RETRY THIS LEVEL?', 'The current round will end. A new entry costs 200 coins.',
                        'Your wallet and color collection will be kept.', 'CONFIRM RETRY / 200', 'retry_confirm')
        elif app.screen == 'reset':
            self.dialog('START FROM SCRATCH?', 'This erases your wallet, unlocked levels and all records.',
                        'You will return to Level 1 with 500 coins.', 'RESET EVERYTHING', 'reset_confirm', RED)
        elif app.screen == 'broke':
            self.broke()
        if app.save_error:
            self.box((32, 855, 1376, 32), PAPER, 8, RED)
            self.text(app.save_error, 48, 859, 15, RED, True)
        return self.canvas

    def wallet(self, x=1110, y=28):
        self.box((x, y, 285, 68), PAPER, 18)
        self.circle(x+36, y+34, 18, (249, 201, 78))
        self.text('C', x+36, y+19, 22, bold=True, center=True)
        self.text('WALLET', x+68, y+10, 12, MUTED, True)
        self.text(f'{self.app.progress.coins:,} COINS', x+68, y+29, 22, bold=True)

    def top(self, subtitle):
        self.text('CLAW MACHINE', 48, 28, 38, bold=True)
        self.text(subtitle, 50, 79, 14, MUTED, True)
        self.wallet()

    def menu_title(self):
        # Cache the curved lettering so the decorative title costs one blit per frame.
        if not hasattr(self, '_menu_title'):
            layer = pygame.Surface((1000, 142), pygame.SRCALPHA)
            font = self.font(180, True)
            word = 'CLAW MACHINE'
            total = font.size(word)[0]/2
            offset = (1000-total)/2
            for index, char in enumerate(word):
                left = font.size(word[:index])[0]/2
                width = font.size(char)[0]/2
                t = (left+width/2)/total*2-1
                angle = -t*10
                center = (round(offset+left+width/2), round(64+13*t*t))
                for color, dy in ((BLUE, 10), (INK, 0)):
                    glyph = pygame.transform.rotate(font.render(char, True, color), angle)
                    glyph = pygame.transform.smoothscale(glyph, (max(1, glyph.get_width()//2), max(1, glyph.get_height()//2)))
                    layer.blit(glyph, glyph.get_rect(center=(center[0], center[1]+dy)))
            self._menu_title = layer
        self.canvas.blit(self._menu_title, (220, 0))

    def menu_claw(self, x, y, scale=1):
        def point(dx, dy):
            return (round(x+dx*scale), round(y+dy*scale))
        self.box((x-14*scale, y-12*scale, 28*scale, 24*scale), STEEL, max(3, round(5*scale)))
        self.ball(x, y+64*scale, 28*scale, PALETTE[0][1])
        for side in (-1, 1):
            points = [point(side*10, 10), point(side*45, 40), point(side*31, 75)]
            pygame.draw.lines(self.canvas, INK, False, points, max(4, round(11*scale)))
            pygame.draw.lines(self.canvas, STEEL, False, points, max(2, round(6*scale)))
            self.circle(*point(side*45, 40), max(2, round(4*scale)), STEEL)

    def level_icon(self, index, x, y):
        if index == 0:
            self.line((x, y-37), (x, y-17), INK, 5)
            self.menu_claw(x, y-13, .70)
        elif index == 1:
            self.ball(x, y-8, 22, PALETTE[1][1])
            for dx in (-15, 0, 15):
                self.line((x+dx, y+26), (x+dx, y+49), INK, 3)
            self.circle(x-23, y+54, 10, BLUE)
            self.circle(x+23, y+54, 10, BLUE)
        else:
            self.circle(x, y+10, 32, BLUE)
            self.circle(x, y+10, 16, PALETTE[2][1])
            for dx, dy in ((-42, 0), (42, 0), (0, -42), (0, 42)):
                self.line((x+dx, y+10+dy), (x+dx*.65, y+10+dy*.65), INK, 4)

    def menu(self):
        a = self.app
        self.menu_title()
        self.text('M O V E .  G R A B .  D R O P .', 720, 136, 25, bold=True, center=True)

        # Compact wallet replaces the old concept's BEST SCORE badge.
        self.box((1186, 24, 222, 52), BLUE, 19, INK, 3)
        self.circle(1214, 50, 12, PALETTE[2][1])
        self.text(f'{a.progress.coins:,} COINS', 1311, 34, 20, bold=True, center=True)
        self.button('reset', 'RESET ALL', (1283, 90, 125, 32), PAPER, size=13)

        self.box((493, 182, 454, 18), STEEL, 5, INK, 4)
        self.box((692, 177, 56, 29), BLUE, 6, INK, 4)
        self.line((720, 207), (720, 232), INK, 9)
        self.line((720, 207), (720, 232), STEEL, 4)
        self.menu_claw(720, 246, 1.15)
        for side in (-1, 1):
            self.line((720+side*84, 277), (720+side*95, 265), PALETTE[2][1], 5)
            self.line((720+side*95, 294), (720+side*105, 289), PALETTE[2][1], 5)

        # Open collection tray, with its front panel masking the lower balls.
        pygame.draw.ellipse(self.canvas, BLUE, (520, 438, 400, 24))
        for points in (((574, 350), (592, 340), (592, 449), (574, 449)),
                       ((848, 340), (866, 350), (866, 449), (848, 449))):
            pygame.draw.polygon(self.canvas, BLUE, points)
            pygame.draw.polygon(self.canvas, INK, points, 4)
        for x, y, color in ((653, 388, 1), (720, 403, 2), (787, 385, 3)):
            self.ball(x, y, 33, PALETTE[color][1])
        self.box((589, 411, 262, 42), STEEL, 6, INK, 4)
        for x in (603, 837):
            self.circle(x, 425, 3, INK, False)

        enough = a.progress.coins >= ENTRY_COST and not a.load_blocked
        play = pygame.Rect(530, 476, 380, 80)
        self.box(play.move(0, 6), PALETTE[2][1] if enough else STEEL, 29, width=0)
        if enough:
            self.buttons['start'] = play
        self.box(play, mix(ORANGE, PAPER, .18) if enough and self.mouse and play.collidepoint(self.mouse) else (ORANGE if enough else (224, 229, 225)), 29, INK, 4)
        self.text('PLAY' if enough else 'NOT ENOUGH COINS', 720, 478 if enough else 491, 43 if enough else 22, bold=True, center=True)
        self.text(f'LEVEL 0{a.selected} / 200 COINS', 720, 532, 13, MUTED, True, True)
        self.button('help', 'HOW TO PLAY', (597, 573, 246, 45), BLUE, size=20)
        self.text('Collect 3 to win. 3 misses end the round.', 720, 630, 20, bold=True, center=True)
        if enough:
            self.text('Same color: 100 > 150 > 200+ coins  /  Empty grab: -50', 720, 659, 14, MUTED, center=True)
        else:
            self.text('RESET ALL restores 500 coins and clears all progress.', 720, 659, 15, RED, True, True)

        for i, name in enumerate(LEVEL_NAMES):
            x, y = 180+i*370, 694
            unlocked = i+1 <= a.progress.unlocked and not a.load_blocked
            selected = i+1 == a.selected
            border = ORANGE if selected else MUTED
            fill = PAPER if selected else BLUE
            self.box((x, y+5, 340, 153), PALETTE[2][1] if selected else STEEL, 20, width=0)
            self.box((x, y, 340, 153), fill, 20, border, 4)
            self.text(f'0{i+1}', x+23, y+8, 43, bold=True)
            self.text(name, x+24, y+60, 19, bold=True)
            self.level_icon(i, x+270, y+47)
            label = ('CLEARED' if a.progress.cleared[i] else 'READY') if unlocked else 'LOCKED'
            self.box((x+23, y+91, 125, 28), PALETTE[2][1] if unlocked else STEEL, 14, width=0)
            self.text(label, x+85, y+94, 14, bold=True, center=True)
            self.circle(x+31, y+135, 6, PALETTE[2][1])
            self.text(f'BEST EARNED  {a.progress.best[i]:,} COINS', x+45, y+125, 12, MUTED, True)
            if unlocked:
                self.buttons[f'level_{i+1}'] = pygame.Rect(x, y, 340, 153)
        self.text('Select a level below PLAY. Your wallet and progress save automatically.', 720, 870, 12, MUTED, center=True)

    def header(self, game):
        self.text('CLAW MACHINE', 34, 24, 31, bold=True)
        self.text(f'LEVEL 0{game.level} / {LEVEL_NAMES[game.level-1]}', 36, 72, 14, MUTED, True)
        for i, word in enumerate(('MOVE', 'GRAB', 'DROP'), 1):
            x = 410 + (i-1)*149
            self.box((x, 32, 135, 49), ORANGE if i == game.stage else BLUE, 24)
            self.text(f'{i}. {word}', x+67, 42, 20, bold=True, center=True)
        self.button('retry', 'RETRY / 200', (870, 36, 183, 43), PAPER, size=16)
        self.wallet(1102, 24)

    def sidebar(self, g, mouse):
        a = self.app
        self.box((1080, 118, 328, 664), PAPER, 22, shadow=True)
        self.text('YOUR COLLECTION', 1244, 141, 23, bold=True, center=True)
        self.text(f'{len(g.collected)} / 3 DELIVERED', 1244, 179, 16, MUTED, True, True)
        for i in range(3):
            y = 221+i*89
            self.box((1102, y, 282, 77), (234, 242, 235) if i < len(g.collected) else (239, 244, 244), 13, MID_BLUE, 1)
            if i < len(g.collected):
                ci, _ = g.collected[i]
                self.ball(1140, y+38, 23, PALETTE[ci][1])
                self.text(f'{PALETTE[ci][0]} x{a.progress.colors[ci]}', 1178, y+12, 17, bold=True)
                reward = a.round_rewards[i] if i < len(a.round_rewards) else 100
                self.text(f'+{reward} COINS', 1178, y+41, 15, GREEN, True)
            else:
                self.dashed_circle(1140, y+38, 23)
                self.text(f'CATCH 0{i+1}', 1178, y+24, 17, MUTED, True)
        self.text(f'MISSES  {g.misses} / 3', 1104, 505, 20, bold=True)
        for i in range(3):
            self.circle(1288+i*34, 519, 10, RED if i < g.misses else PAPER)
        self.text('Empty grab: -50 coins', 1104, 540, 15, MUTED)
        self.text(f'Earned  +{a.round_earnings}    Lost  -{a.round_penalties}', 1104, 576, 16, GREEN, True)
        self.text('NEXT REWARD BY COLOR', 1104, 615, 11, MUTED, True)
        for i in range(6):
            x = 1121+i*47
            self.circle(x, 645, 9, PALETTE[i][1])
            self.text(str(100+50*a.progress.colors[i]), x, 661, 11, MUTED, center=True)
        if g.paused:
            label, enabled = 'PAUSED', False
        elif g.state == State.MOVE:
            label, enabled = 'GRAB', True
        elif g.state == State.CARRY:
            label, enabled = ('DROP BALL' if g.above_bin else 'MOVE LEFT TO DROP'), True
        else:
            label, enabled = {State.LOWER:'LOWERING...', State.CLOSE:'CLOSING...', State.LIFT:'LIFTING...', State.DROP:'DELIVERING...'}.get(g.state, 'FINISHED'), False
        self.button('action', label, (1102, 700, 282, 56), enabled=enabled, size=18)

    def footer(self, g):
        a = self.app
        self.box((32, 798, 1376, 53), PAPER, 14)
        message = a.notice if a.notice_time > 0 else g.message
        self.text(message, 50, 806, 17, GREEN if message.startswith('+') else INK, True)
        self.text('MOUSE aim / CLICK grab or drop / SPACE pause / R paid retry', 50, 831, 12, MUTED)
        self.text(f'ENTRY PAID: 200', 1225, 831, 12, MUTED, True)

    def pause_panel(self):
        self.box((270, 315, 570, 220), PAPER, 24, shadow=True)
        self.text('TAKE A BREATHER', 555, 347, 32, bold=True, center=True)
        self.text('Your round is paused. No extra entry charge.', 555, 398, 18, MUTED, center=True)
        self.button('resume', 'RESUME', (385, 450, 340, 56))

    def result(self):
        a, g = self.app, self.app.game
        won = g.state == State.WON
        self.top('ROUND SUMMARY')
        self.box((220, 153, 1000, 630), PAPER, 28, shadow=True)
        title = 'ALL THREE LEVELS CLEARED!' if won and g.level == 3 else ('LEVEL COMPLETE!' if won else 'OUT OF GRABS')
        self.text(title, 720, 190, 38, GREEN if won else RED, True, True)
        self.text(f'LEVEL {g.level} / {LEVEL_NAMES[g.level-1]}', 720, 250, 20, MUTED, True, True)
        for i in range(3):
            x = 620+i*100
            if i < len(g.collected):
                self.ball(x, 330, 29, PALETTE[g.collected[i][0]][1])
            else:
                self.dashed_circle(x, 330, 29)
        self.text(f'{len(g.collected)} delivered / {g.misses} empty grabs', 720, 381, 20, MUTED, center=True)
        self.text(f'ENTRY  -200       REWARDS  +{a.round_earnings}       MISSES  -{a.round_penalties}', 720, 433, 21, bold=True, center=True)
        net = a.round_earnings-a.round_penalties-200
        self.text(f'ROUND TOTAL  {net:+,} COINS', 720, 477, 27, GREEN if net >= 0 else RED, True, True)
        enough = a.progress.coins >= 200
        if enough:
            if won and g.level < 3:
                self.button('next', 'NEXT LEVEL / 200 COINS', (395, 551, 650, 62))
            else:
                self.button('start', 'PLAY AGAIN / 200 COINS', (395, 551, 650, 62))
            self.button('menu', 'MAIN MENU', (395, 633, 650, 55), BLUE)
        else:
            self.text('Not enough coins for another entry. Reset to start over.', 720, 545, 19, RED, True, True)
            self.button('reset', 'RESET ALL', (395, 599, 650, 62), ORANGE)
        self.text('Wallet and color bonuses carry over between levels.', 720, 730, 17, MUTED, center=True)

    def help_page(self):
        self.top('HOW TO PLAY')
        rows = [
            ('01 / MOVE', 'Move your mouse inside the cabinet. Aim ahead of a moving ball.'),
            ('02 / GRAB', 'Click to lower the claw. Both fingers must touch a ball to hold it.'),
            ('03 / DROP', 'Carry LEFT above the short bay. Click to open the hatch and deliver.'),
            ('COINS', 'Start with 500. Each level entry or retry costs 200. An empty grab costs 50.'),
            ('COLOR BONUS', 'Each color pays 100, then 150, then 200, increasing by 50 each time.'),
            ('PROGRESS', 'Deliver 3 to clear a level. Make 3 empty grabs and the round ends.'),
            ('RESET ALL', 'Below 200 coins? Reset all funds, levels and records to start over.'),
        ]
        for i, (title, body) in enumerate(rows):
            y = 145+i*80
            self.box((65, y, 1310, 66), PAPER, 14, MID_BLUE, 1)
            self.text(title, 88, y+20, 19, bold=True)
            self.text(body, 303, y+20, 18, MUTED)
        self.text('Recycled balls do not count as misses. Closing a round forfeits its entry fee.', 720, 730, 18, MUTED, center=True)
        self.button('back', 'BACK', (520, 779, 400, 57))

    def briefing(self):
        self.top('LEVEL 03 / READ BEFORE YOU START')
        self.text('WATCH THE STREAM', 720, 155, 46, bold=True, center=True)
        self.text('Faster launches. Different jet angles. Some objects cannot be caught.', 720, 225, 23, MUTED, center=True)
        self.box((230, 291, 450, 270), BLUE, 24)
        self.ball(455, 374, 47, PALETTE[0][1])
        self.text('ROUND BALLS', 455, 449, 25, GREEN, True, True)
        self.text('Catch and deliver for coins.', 455, 497, 19, MUTED, center=True)
        self.box((760, 291, 450, 270), (240, 225, 215), 24)
        self.bullet(985, 374, 2.2)
        self.text('BULLETS', 985, 449, 25, RED, True, True)
        self.text('Cannot be grabbed. Let them pass.', 985, 497, 19, MUTED, center=True)
        self.text('An empty grab costs 50 coins and uses one of your three misses.', 720, 603, 22, bold=True, center=True)
        self.text('The entry fee is charged only when you press START below.', 720, 644, 18, MUTED, center=True)
        self.button('briefing_start', 'START LEVEL 3 / 200 COINS', (395, 701, 650, 65))
        self.button('back', 'BACK', (570, 790, 300, 48), PAPER, size=18)

    def bullet(self, x, y, scale=1):
        self.box((x-25*scale, y-10*scale, 50*scale, 20*scale), INK, max(1, int(10*scale)))
        self.line((x-15*scale, y-8*scale), (x-15*scale, y+8*scale), ORANGE, max(2, int(4*scale)))
        self.line((x-7*scale, y-6*scale), (x+12*scale, y-6*scale), STEEL, max(2, int(2*scale)))

    def dialog(self, title, line1, line2, label, action, fill=ORANGE):
        self.top('YOUR PROGRESS')
        self.box((200, 245, 1040, 420), PAPER, 28, shadow=True)
        self.text(title, 720, 285, 37, bold=True, center=True)
        self.text(line1, 720, 367, 22, MUTED, center=True)
        self.text(line2, 720, 412, 20, MUTED, center=True)
        self.button(action, label, (360, 489, 720, 64), fill)
        self.button('back', 'CANCEL', (530, 584, 380, 48), BLUE, size=18)

    def broke(self):
        self.top('INSUFFICIENT COINS')
        self.text('TIME FOR A FRESH START', 720, 270, 42, bold=True, center=True)
        self.text('You need 200 coins to enter. Your current progress cannot continue.', 720, 360, 22, MUTED, center=True)
        self.text('RESET ALL restores 500 coins and clears all levels and records.', 720, 411, 22, MUTED, center=True)
        self.button('reset', 'RESET ALL', (470, 520, 500, 68))
