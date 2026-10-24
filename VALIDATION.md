# Validation record — 24 October 2026

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
