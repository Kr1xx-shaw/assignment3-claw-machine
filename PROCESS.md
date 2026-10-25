# Process record

## Starting idea and intended user

The student proposed adapting the Week 7 moving balls into a claw machine:
mouse-following claw, MOVE / GRAB / DROP instructions, an upward air jet, a
collected-ball display, three successful deliveries to win and three empty
grabs to lose. A short round should be understandable to a first-time player.

## Design decisions made in this conversation

1. **Contact-based grabbing.** The student explicitly required that a ball must
   actually be caught rather than awarding a ball every time. The implementation
   checks both inward fingers and the ball's enclosure before a hold is possible.
2. **Protected left delivery bay.** The student moved DROP to the left and asked
   for a surround so free balls could not accidentally enter it.
3. **Flat illustration and English.** The student chose flat vector illustration
   rather than the initial metallic/realistic treatment, and required English UI.
4. **Correction of an inaccessible opening.** The student pointed out that the
   full-height partition in the AI concept blocked the claw. The design was
   corrected to a short lower-left collector with clear airspace above it and
   sliding top panels. The implemented collider ends at the visible short bay.
5. **Clear scoring moment.** Holding a ball is intermediate feedback; a point is
   awarded only after verified delivery. Collection slots show the actual colours.
6. **Predictable mistakes.** Busy clicks are ignored, a misaligned DROP click
   keeps the ball held, and switching windows pauses the simulation.

## AI assistance — honest disclosure

OpenAI Codex assisted with planning, Python code, documentation and automated
tests. The built-in OpenAI image-generation tool produced and revised concept
mockups. The exact image model identifier was not provided in the tool result.

A suggestion retained was separating the game into aim/grab/carry/delivery states
with explicit feedback and protected collection. A generated visual suggestion
changed/rejected was the full-height left partition: it made delivery impossible.
The student identified that problem, and the final design shortened the wall.
The student also changed the visual direction and requested English labels.

The concept PNG is a design reference only. Every game element is drawn from
geometric primitives at its live simulation position. AI-created documentation
fixtures are not represented as observations from a human user.

## Automated validation

The source contains tests for successful and unsuccessful contact geometry,
ordinary repeated clicks, pause/reset, protected collection, delivery before
scoring, three-win/three-miss endings, jet contact and consistent fixed-step
updates. A headless event-loop test exercises mouse-click delivery and keyboard
and button restart. The report in `VALIDATION.md` records completed checks.

These checks establish program behaviour under those test conditions; they are
not evidence of a classmate's usability experience.

## Real user trial — TO BE COMPLETED BY THE STUDENT

No human participant trial has been performed or invented for this record.
The following is a practical plan, not a completed study:

1. Give one person the running game without first explaining the controls.
2. Ask them to try to collect a ball and then play a round.
3. Observe whether they understand aiming, when the grab begins, the left DROP
   alignment, and the difference between holding and scoring.
4. Note at least one hesitation or mistake. Make an improvement based on it,
   or explain with a reason why the design is kept.

Fill in after that real session (no participant name needed):

- Date and device: **pending**
- What they tried before explanation: **pending**
- What they understood or hesitated over: **pending**
- One specific observation: **pending**
- Change made, or reason for keeping the design: **pending**
- What happened after retesting: **pending**

## Development history

### Startup font bug reported by the student

The student supplied a traceback from an actual launch: Pygame's Windows
system-font discovery passed a non-string registry value to `splitext`, causing
a `TypeError` before the first frame. The renderer was changed to open known
font files directly and fall back to Pygame's bundled default if loading fails.
An automated regression reproduced the exception before the change. Checks were
added for the broken discovery path, missing files and a corrupted font file.
This is a runtime bug report; the separate participant usability trial is still
pending.

Local commits should record the actual implementation and subsequent changes.
Do not fabricate earlier commits or trial findings. Add a real commit after the
participant-driven change, and describe what changed and why here.

