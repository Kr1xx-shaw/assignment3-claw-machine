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

    def menu(self):
        a = self.app
        self.top('MOVE. GRAB. DROP. MAKE YOUR COLORS COUNT.')
        self.box((48, 136, 690, 456), BLUE, 28, shadow=True)
        self.text('A LITTLE SKILL. A LITTLE TIMING.', 393, 157, 14, MUTED, True, True)
        self.line((120, 204), (660, 204), STEEL, 13)
        self.line((391, 209), (391, 289), INK, 5)
        self.box((364, 277, 54, 34), ORANGE, 9)
        self.ball(391, 354, 48, PALETTE[0][1])
        for side in (-1, 1):
            points = [(391+side*16, 301), (391+side*68, 332), (391+side*49, 393), (391+side*23, 399)]
            pygame.draw.lines(self.canvas, INK, False, points, 13)
            pygame.draw.lines(self.canvas, STEEL, False, points, 7)
        self.box((154, 506, 480, 20), PAPER, 8)
        for x, y, c in ((237, 468, 1), (543, 468, 2), (478, 474, 3)):
            self.ball(x, y, 31, PALETTE[c][1])
        self.text('COLLECT THREE. KEEP THE COINS.', 393, 547, 18, bold=True, center=True)

        self.text('YOUR NEXT CATCH', 790, 146, 16, MUTED, True)
        self.text(LEVEL_NAMES[a.selected-1], 790, 181, 35, bold=True)
        self.text('3 deliveries to clear / 3 misses end the round', 790, 237, 19, MUTED)
        self.text('Same color again? Earn more each time.', 790, 274, 20, bold=True)
        self.text('100  >  150  >  200  >  +50 per extra ball', 790, 311, 20, GREEN, True)
        self.text('Empty grab: -50 coins. Entry: 200 coins.', 790, 349, 18, MUTED)
        enough = a.progress.coins >= ENTRY_COST and not a.load_blocked
        self.button('start', f'PLAY LEVEL {a.selected} / 200 COINS', (790, 400, 600, 69), enabled=enough)
        self.button('help', 'HOW TO PLAY', (790, 486, 287, 56), PAPER, size=18)
        self.button('reset', 'RESET ALL', (1093, 486, 297, 56), PAPER, size=18)
        if not enough:
            self.text('RESET ALL to restore 500 coins and start over.', 790, 559, 17, RED, True)
        for i, name in enumerate(LEVEL_NAMES):
            x = 48 + i*454
            unlocked = i+1 <= a.progress.unlocked and not a.load_blocked
            selected = i+1 == a.selected
            self.box((x, 625, 435, 180), PAPER if unlocked else (231, 236, 231), 22,
                     ORANGE if selected else MID_BLUE, 3 if selected else 2)
            self.text(f'0{i+1}', x+22, 641, 35, GREEN if a.progress.cleared[i] else MUTED, True)
            self.text(name, x+89, 652, 23, bold=True)
            self.text(('CLEARED' if a.progress.cleared[i] else 'READY') if unlocked else 'LOCKED', x+24, 700, 13, MUTED, True)
            self.text(f'Best earned: {a.progress.best[i]:,} coins', x+24, 730, 16, MUTED)
            self.button(f'level_{i+1}', 'SELECTED' if selected else ('SELECT' if unlocked else 'LOCKED'),
                        (x+267, 741, 146, 43), BLUE, enabled=unlocked, size=15)
        self.text('Progress saves automatically. Closing a paid round ends it without a refund.', 48, 827, 15, MUTED)

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
