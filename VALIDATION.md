# Validation record — 24 October 2026

## Bullet-time filter and countdown — 29 October 2026

All **53 automated tests passed**. Four additional checks verify expiry after
three unscaled seconds, expiry across a long frame, early-release cancellation,
and held-key repeat behavior after expiry. The visual check compares rendered
pixels to confirm cabinet dimming while ball colors, collected balls and UI
remain unchanged, then verifies normal background restoration on release.

The active filter/countdown, inactive state, instructions and Level 3 briefing
were rendered and visually inspected. Every level continues to use Esc only
for manual pause/resume. Real participant validation remains pending.

## Level 3 bullet time and Esc-only pause — 29 October 2026

All **49 automated tests passed**. Eight new checks cover the three-use limit,
17% slower ball/bullet displacement with a full-speed claw, immediate release
restoration, slowed launch timing, pause/results, paid retry reset and stable
gripping. Two of those checks drive the real event loop with Space down/repeat/up,
Esc and focus-loss events and verify Space never pauses Levels 1 or 2.

The Level 3 briefing, instructions, active and inactive bullet-time panels were
rendered and visually inspected. The wallet and saved progression format are
unchanged. Subjective playtesting remains pending.

## Fine tuning — 29 October 2026

All **41 automated checks passed** after the small Level 2 speed reduction,
lifting-contact fix and repeated-color reward change. New regressions verify
that a ball touching both fingers on the final lift step locks, stays held
during carriage movement and a five-second wait, while one-finger contacts and
bullets never lock. A separate reward check verifies that each new color still
pays 100 while subsequent same-color deliveries pay 200, including across levels.
A natural full-round replay now secures a formerly rejected supported ball.
Five before/after replays that previously returned empty now reach a confirmed
carry, using real physics and identical aim/timing rather than a forced attachment.

Level 2 uses 320–380 pixels/second (about 11% slower than the preceding version).
The original controller/input and Windows-font checks also passed. Real
participant validation of subjective difficulty is still pending.

## Faster streams and lowering fees

The latest revision passes **37 automated checks**. Three new checks cover a
lowering fee saved immediately, invalid/busy/paused inputs staying free, blocked
attempts without sufficient coins, and fast stream travel/removal. Existing
campaign and event-loop expectations include the new lowering fees.

Level 2 now launches at 360–430 pixels/second and Level 3 at 540–640. A clean
uninterrupted launch reaches the recycler in about 1.9–2.2 seconds in Level 2
and 1.3–1.5 seconds in Level 3, compared with roughly 4–5 seconds before.
Simulated timing/aim trials still produce real opposing-contact captures and
misses in each level. The bullet check observes the whole launch sequence,
since a faster bullet may already have left at any single snapshot time.

New rules and accounting were rendered for menu, gameplay, briefing, help and
results. Existing player saves retain their wallet, color totals and unlocks.
Subjective difficulty still needs the pending real participant trial.

## Campaign upgrade — 28 October 2026

The subsequent centered-menu revision passed the event-loop integration and
three font-startup regressions (four targeted checks). The actual rendered menu
was visually inspected, including its title, central illustration, entry fee,
wallet, level cards and reset control. The integration click was updated to the
new PLAY button and still verifies the charge and physical delivery flow.

- **34 automated tests passed** in the student's cached Pygame runtime.
  Coverage includes the original 17 physics checks, 13 campaign/storage/stream
  checks, three font regressions and the updated real-event-loop integration.
- The event-loop test starts from the menu, pays 200, physically captures and
  delivers a ball, pauses, ignores paused clicks and confirms two paid retries
  using keyboard and button paths. The wallet reaches the expected zero balance.
- Campaign tests use actual verified-contact lift/carry/delivery sequences to
  check increasing color rewards, all three unlocks, zero-balance play and reset.
  Temporary files verify that fees/rewards survive reopening, confirmed reset
  persists, malformed saves are preserved until reset, and write failures warn.
- Separate stream trials start from each empty cabinet and use simulated mouse
  aiming/timing to demonstrate real contact catches and empty grabs in Levels 2/3.
  Initial slow closure failed these trials; a faster close fixed this while
  preserving the geometric grip test. Bullets cannot be held even when placed
  at an otherwise valid two-finger contact.
- Thirty seconds of unattended stream simulation in each new level confirms
  recycler removal without misses or rewards and a bounded population.
- Menu, gameplay, Level 3 briefing, instructions, reset confirmation and results
  were rendered from the code and visually inspected. A launcher/collector-label
  overlap was corrected. Screenshot mode does not touch player saves.

These are automated/headless checks and visual inspection of rendered frames,
not a completed human participant trial. The real trial remains pending, including
subjective difficulty and understanding of the new coin rules.

## Completed

- **17 model behaviour tests passed** using the Python standard library.
- **1 Pygame event-loop integration test passed** with the SDL dummy display.
  It drives mouse clicks through a real catch, transport, delivery, pause,
  ignored paused input, keyboard restart and button restart.
- **A complete three-ball victory was reached through actual grip physics** in
  a repeatable replay. Candidate aims were selected by the documentation helper;
  no ball was attached with a forged hold or score during that replay.
- **Source compilation passed** for the initial implementation.
- Start, delivery, victory and loss surfaces were rendered and visually inspected.
  The collector's short wall leaves the overhead carry route open. A clipping
  issue at the floor was corrected before delivery.

Test runtime: CPython 3.12.14, Pygame 2.6.1 / SDL 2.28.4 on Windows.
The model-only suite was also run with the system Python interpreter.

## Limits of this validation

The current session did not expose the Computer Use runtime, so no claim is made
that a person or a desktop-control agent played through the visible window.
The event-loop integration test is automated and headless. The window can be
opened normally with the documented command or PLAY.cmd.

`gameplay-start.png` and `gameplay-drop.png` are actual code-rendered simulation
screenshots. The drop scene follows real successful grabs. The win/loss images
use explicit documentation state fixtures to inspect overlay layout.

The classmate/user trial remains **pending**, as recorded in PROCESS.md.
Difficulty tuning and subjective clarity must be checked during that real trial.

## Follow-up: Windows font-startup failure

The student's supplied traceback was reproduced by making system-font discovery
raise the same TypeError. The renderer now loads Segoe UI files directly and
falls back to the Pygame bundled font. Three font regressions cover broken font
discovery, absent fonts and a corrupted font file. The event-loop test also
disables system-font discovery with the same exception during its entire run.

After the fix, all **21 tests passed** in the same cached `main-9435ffe77f63ab74`
Python environment named in the student's traceback. A fresh `main.py
--screenshot` invocation also rendered the startup screen successfully.
