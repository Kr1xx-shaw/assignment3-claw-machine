# Validation record — 24 October 2026

## Campaign upgrade — 28 October 2026

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
