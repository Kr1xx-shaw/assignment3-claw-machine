# Validation record

## Classmate playtesting update — 30 October 2026

My classmates played the game and reported that Levels 2 and 3 were too difficult
and that entry cost too many coins. I responded by lowering Level 2 speed,
adding and strengthening Level 3 bullet time, and reducing entry/retry fees to
100 coins. `PROCESS.md` records this feedback and the resulting decisions.

The sections below preserve the automated checks from development. They verify
program behavior and are separate from this real-player feedback.

## Entry fee reduced to 100 — 29 October 2026

All **53 tests passed** with updated wallet expectations for initial entry,
next-level entry, repeated paid retry, save/reopen and the 150-coin affordability
boundary. Lowering and miss fees retain their existing checks. Menu, gameplay,
briefing and results were rendered with the new fee and visually inspected.

## Stronger bullet time — 29 October 2026

All 12 targeted bullet-time checks passed after reducing speed to 66.4% of normal
(20% slower than its previous 83% speed). The displacement check verifies 0.664
for both free balls and bullets while the claw retains full speed. Launch timing,
release, the three-second expiry, use limits, filter and keyboard controls passed.

## Bullet-time filter and countdown — 29 October 2026

All **53 automated tests passed**. Four additional checks verify expiry after
three unscaled seconds, expiry across a long frame, early-release cancellation,
and held-key repeat behavior after expiry. The visual check compares rendered
pixels to confirm cabinet dimming while ball colors, collected balls and UI
remain unchanged, then verifies normal background restoration on release.

The active filter/countdown, inactive state, instructions and Level 3 briefing
were rendered and visually inspected. Every level continues to use Esc only
for manual pause/resume. Classmate playtest feedback is recorded above and in `PROCESS.md`.

## Level 3 bullet time and Esc-only pause — 29 October 2026

All **49 automated tests passed**. Eight new checks cover the three-use limit,
17% slower ball/bullet displacement with a full-speed claw, immediate release
restoration, slowed launch timing, pause/results, paid retry reset and stable
gripping. Two of those checks drive the real event loop with Space down/repeat/up,
Esc and focus-loss events and verify Space never pauses Levels 1 or 2.

The Level 3 briefing, instructions, active and inactive bullet-time panels were
rendered and visually inspected. The wallet and saved progression format are
unchanged. Classmate feedback on difficulty is recorded above.

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
The original controller/input and Windows-font checks also passed. Classmate
feedback on subjective difficulty is recorded above.

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
The later classmate feedback on difficulty is recorded above.

## Campaign upgrade — 28 October 2026

The subsequent centered-menu revision passed the event-loop integration and
three font-startup regressions (four targeted checks). The actual rendered menu
was visually inspected, including its title, central illustration, entry fee,
wallet, level cards and reset control. The integration click was updated to the
new PLAY button and still verifies the charge and physical delivery flow.

- **34 automated tests passed** in my cached Pygame runtime.
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
not themselves a human participant trial. The separate classmate feedback and
resulting adjustments are recorded above and in `PROCESS.md`.

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

The classmate feedback and difficulty/cost adjustments are recorded in
`PROCESS.md`; these automated checks do not measure subjective clarity.

## Follow-up: Windows font-startup failure

The traceback I supplied was reproduced by making system-font discovery
raise the same TypeError. The renderer now loads Segoe UI files directly and
falls back to the Pygame bundled font. Three font regressions cover broken font
discovery, absent fonts and a corrupted font file. The event-loop test also
disables system-font discovery with the same exception during its entire run.

After the fix, all **21 tests passed** in the same cached `main-9435ffe77f63ab74`
Python environment named in my traceback. A fresh `main.py
--screenshot` invocation also rendered the startup screen successfully.
