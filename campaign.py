"""Campaign rules, coin accounting and atomic local progress storage.

The physics model emits delivery/miss events. Only this controller charges fees
or pays rewards; opening menus and rendering never change the wallet.
"""
from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path

from model import Game, State

ENTRY_COST = 200
INITIAL_COINS = 500
MISS_COST = 50
LEVEL_NAMES = ('AIR JET', 'CROSS CURRENT', 'FAST & FURIOUS')


@dataclass
class Progress:
    coins: int = INITIAL_COINS
    unlocked: int = 1
    colors: list = field(default_factory=lambda: [0] * 6)
    best: list = field(default_factory=lambda: [0] * 3)
    cleared: list = field(default_factory=lambda: [False] * 3)

    @classmethod
    def parse(cls, raw):
        def integer(value, low, high):
            return type(value) is int and low <= value <= high
        if not isinstance(raw, dict) or raw.get('version') != 1:
            raise ValueError('Unknown save format')
        p = cls(**raw['progress'])
        if not integer(p.coins, 0, 10**12) or not integer(p.unlocked, 1, 3):
            raise ValueError('Invalid wallet or level')
        for values, length in ((p.colors, 6), (p.best, 3)):
            if not isinstance(values, list) or len(values) != length or not all(integer(v, 0, 10**12) for v in values):
                raise ValueError('Invalid collection')
        if not isinstance(p.cleared, list) or len(p.cleared) != 3 or not all(type(v) is bool for v in p.cleared):
            raise ValueError('Invalid level records')
        if any(not p.cleared[i] for i in range(p.unlocked - 1)):
            raise ValueError('Invalid unlock order')
        return p


def default_save_path():
    base = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share'))
    return base / 'ClawMachine' / 'progress.json'


class Campaign:
    def __init__(self, save_path=None, seed=None):
        self.path = Path(save_path) if save_path is not None else None
        self.seed = seed
        self.progress = Progress()
        self.game = None
        self.screen = 'menu'
        self.selected = 1
        self.pending_level = 1
        self.return_screen = 'menu'
        self.save_error = ''
        self.load_blocked = False
        self.notice = ''
        self.notice_time = 0
        self.round_earnings = self.round_penalties = 0
        self.round_rewards = []
        self.settled = False
        if self.path:
            try:
                self.progress = Progress.parse(json.loads(self.path.read_text(encoding='utf-8')))
            except FileNotFoundError:
                pass
            except (OSError, ValueError, TypeError, KeyError):
                self.load_blocked = True
                self.save_error = 'Progress could not be loaded. RESET ALL to start a new save.'
            self.selected = self.progress.unlocked

    def save(self):
        if self.path is None:
            return True
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix('.tmp')
            temp.write_text(json.dumps({'version': 1, 'progress': asdict(self.progress)}, indent=2), encoding='utf-8')
            os.replace(temp, self.path)
            self.save_error = ''
            return True
        except OSError:
            self.save_error = 'Save unavailable. Keep this window open; progress is currently in memory.'
            return False

    def request_start(self, level=None):
        if self.screen not in ('menu', 'result', 'retry') or self.load_blocked:
            return False
        level = self.selected if level is None else level
        if level not in (1, 2, 3) or level > self.progress.unlocked:
            return False
        if self.progress.coins < ENTRY_COST:
            self.screen = 'broke'
            return False
        self.pending_level = level
        if level == 3:
            self.screen = 'briefing'
            return True
        return self._start(level)

    def accept_briefing(self):
        if self.screen == 'briefing':
            return self._start(3)
        return False

    def _start(self, level):
        if self.progress.coins < ENTRY_COST:
            self.screen = 'broke'
            return False
        self.progress.coins -= ENTRY_COST
        self.selected = level
        self.game = Game(self.seed, level=level)
        self.round_earnings = self.round_penalties = 0
        self.round_rewards = []
        self.settled = False
        self.screen = 'play'
        self.notice = '-200 COINS / ENTRY'
        self.notice_time = 2.5
        self.save()
        return True

    def request_retry(self):
        if self.screen == 'play':
            self.screen = 'retry'

    def return_to_menu(self):
        # Only result/briefing screens may leave a paid round. A running round
        # can be paused or explicitly forfeited via the retry confirmation.
        self.screen = 'menu'

    def ask_reset(self):
        self.return_screen = self.screen
        self.screen = 'reset'

    def cancel(self):
        if self.screen == 'reset':
            self.screen = self.return_screen
        elif self.screen == 'retry':
            self.screen = 'play'
        elif self.screen in ('help', 'briefing'):
            self.screen = 'menu'

    def confirm_reset(self):
        if self.screen != 'reset':
            return
        self.progress = Progress()
        self.game = None
        self.selected = 1
        self.load_blocked = False
        self.round_rewards = []
        self.round_earnings = self.round_penalties = 0
        self.screen = 'menu'
        self.save()

    def update(self, elapsed):
        if self.screen != 'play':
            return
        g = self.game
        if not g.paused:
            self.notice_time = max(0, self.notice_time - elapsed)
        g.update(elapsed)
        changed = False
        for kind, color in g.events:
            if kind == 'delivery':
                reward = 100 + 50 * self.progress.colors[color]
                self.progress.colors[color] += 1
                self.progress.coins += reward
                self.round_earnings += reward
                self.round_rewards.append(reward)
                self.notice = f'+{reward} COINS / SAME COLOR x{self.progress.colors[color]}'
            elif kind == 'miss':
                penalty = min(MISS_COST, self.progress.coins)
                self.progress.coins -= penalty
                self.round_penalties += penalty
                self.notice = f'-{penalty} COINS / EMPTY GRAB'
            changed = True
            self.notice_time = 3
        g.events.clear()
        if g.terminal and not self.settled:
            self.settled = True
            index = g.level - 1
            self.progress.best[index] = max(self.progress.best[index], self.round_earnings)
            if g.state == State.WON:
                self.progress.cleared[index] = True
                self.progress.unlocked = max(self.progress.unlocked, min(3, g.level + 1))
            self.screen = 'result'
            changed = True
        if changed:
            self.save()
