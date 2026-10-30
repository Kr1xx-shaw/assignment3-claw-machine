# Process record

## Starting idea and intended user

I proposed adapting the Week 7 moving balls into a claw machine:
mouse-following claw, MOVE / GRAB / DROP instructions, an upward air jet, a
collected-ball display, three successful deliveries to win and three empty
grabs to lose. A short round should be understandable to a first-time player.

## My design decisions

1. **Contact-based grabbing.** I explicitly required that a ball must
   actually be caught rather than awarding a ball every time. The implementation
   checks both inward fingers and the ball's enclosure before a hold is possible.
2. **Protected left delivery bay.** I moved DROP to the left and asked
   for a surround so free balls could not accidentally enter it.
3. **Flat illustration and English.** I chose flat vector illustration
   rather than the initial metallic/realistic treatment, and required English UI.
4. **Correction of an inaccessible opening.** I pointed out that the
   full-height partition in the AI concept blocked the claw. I changed it
   to a short lower-left collector with clear airspace above it and
   sliding top panels. The implemented collider ends at the visible short bay.
5. **Clear scoring moment.** Holding a ball is intermediate feedback; a point is
   awarded only after verified delivery. Collection slots show the actual colours.
6. **Predictable mistakes.** Busy clicks are ignored, a misaligned DROP click
   keeps the ball held, and switching windows pauses the simulation.

## AI assistance — honest disclosure

I used OpenAI Codex to help with planning, Python code, documentation and
automated tests. The built-in OpenAI image-generation tool produced and revised concept
mockups. The exact image model identifier was not provided in the tool result.

I kept the suggestion to separate the game into aim/grab/carry/delivery states,
with explicit feedback and a protected collection area. I rejected the generated
full-height left partition because it made delivery impossible. After noticing
that problem, I changed the design to a shorter wall. I also changed the visual
direction to flat illustration and requested English labels.

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

## Classmate playtesting and changes

I let my classmates try the game before I explained the controls. I observed
that the moving balls were too fast for them to catch reliably, which led to
frequent empty grabs. They also told me that Levels 2 and 3 felt too difficult
and that the entry fee was too high.

Repeated misses and the cost of entering later levels could leave players
without enough coins to continue even before they reached three misses in that
round. This made it very difficult to clear Levels 2 and 3. I treated the
playtest feedback as both a timing problem and a balance problem between
difficulty and coin costs.

- **Level 2:** I reduced launch speed from 360–430 to 320–380 pixels/second,
  about 11% slower, to give players more time to aim.
- **Level 3:** I also felt that this level needed a more distinctive interaction,
  so I added hold-to-use bullet time, then strengthened it to 66.4%
  of normal ball/bullet speed. It gives players three opportunities per round,
  lasting up to three seconds each, to make the faster stream more manageable.
- **Entry fee:** I reduced entry and retry fees from 200 to 100 coins so that
  another attempt would cost less.

I made these changes to give players more time to aim, make Level 3 feel more
distinctive, and reduce the cost of continuing after mistakes.
The automated checks elsewhere in this document verify program behavior; this
section records the feedback from actual people playing the game.

## Development history

### Lower entry fee — 29 October 2026

I reduced every level-entry fee from 200 to 100 coins. Initial PLAY,
NEXT LEVEL, PLAY AGAIN and confirmed RETRY all charge 100 once. Starting a new
round requires 150 available coins, covering entry and the first 50-coin grab.
The controller, buttons, entry notice, result arithmetic and instructions now
use the shared entry-cost constant. Existing saved balances are retained without
retroactively changing earlier transactions.

### Stronger bullet-time slowdown — 29 October 2026

I requested a further 20% speed reduction during bullet time. Applied
relative to the existing 83% speed, the new multiplier is 0.83 x 0.80 = 0.664,
or 66.4% of normal speed (33.6% total reduction). The interface derives its speed
label from the same parameter. The three-second limit, three uses, filter and
Esc pause controls continue to apply.

### Hold-to-use bullet time and unified pause key — 29 October 2026

I requested a Level 3 Space-held bullet-time mode that reduces speed
by 17%, with three opportunities. I then decided that pause should use Esc
only in all levels. Space now has no action in Levels 1 and 2.

Each new Space press in Level 3 consumes one use and slows free balls, bullets
and the launch stream to 83% while held. The claw and delivered balls remain at
normal speed. Release restores normal timing without changing stored velocities,
so repeated presses do not compound the slowdown. I then requested a
dark environmental filter and a 3.0-second countdown. Each activation now lasts
up to three ordinary seconds, even during slow frames. Holding beyond expiry
cannot spend another use; the player must release and press again.

The cabinet is darkened by a translucent layer with transparent masks over the
balls, including held and collected balls, preserving their existing art and
occlusion. The wallet and controls remain outside the filter. The right panel
shows seconds left and remaining uses; the pre-level briefing explains the limit.
This uses existing procedural illustration rather than adding external art.

Pause, focus loss, retry/reset screens and results end the effect. A spent use
is not refunded; a fresh paid Level 3 round gets three uses. Automated tests
check the exact displacement ratio, full-speed claw, release, exhaustion, paused
input, repeated key events, focus loss and stable gripping. My classmates'
feedback and my resulting adjustments are recorded above.

### Small difficulty adjustment, stable lifting and same-color reward — 29 October 2026

I reported that Level 2 had become slightly too difficult and that
some balls appeared to reach the top with the claw before falling. Level 2
launches were reduced from 360–430 to 320–380 pixels/second (about 11%).

Inspection found that only the closing phase could confirm a grip. Simulated
trials also found balls touching both lower fingers during lifting with their
centers about 37 pixels below the claw, just outside the former 40-pixel cutoff.
The valid pocket was widened slightly (36–75 vertical pixels and 0.75 ball radii
laterally). Real opposing contacts can now confirm a hold during lifting, and
top-arrival success/miss is resolved after the final contact check. A regression
test follows the last-step capture through repeated movement and a five-second
wait at the rail. One-finger contacts and bullets remain uncatchable.

I also requested 200 coins for the same color. Each color's first
delivery pays 100, and all subsequent deliveries of that color pay 200 each.
This replaces the earlier increasing 100/150/200/... schedule. Existing saved
color counts remain valid and inform the next reward; balances are not recalculated.

### Faster streams and paid lowering

I reported that Levels 2 and 3 felt slower and easier than Level 1.
Launch speed was raised from 150–185 to 360–430 pixels/second in Level 2 and from
215–255 to 540–640 in Level 3. Bullet launches are faster still. The contact-based
grip remains unchanged; simulated aim/timing trials confirm catches remain possible.
My classmates later reported that the faster levels were too difficult, leading
to the adjustments recorded in the playtesting section above.

I also requested a 50-coin deduction on every lowering. This is additional
to the 200 entry fee and the existing 50 empty-grab penalty. Only a valid new descent
charges; delivery, busy clicks and paused input do not. The charge is saved immediately.
New entries require 250 available coins so the player can afford entry and at least
one grab. A paid grab can finish at zero; a further grab needs 50 coins or a full reset.

### Three-level coin campaign — 28 October 2026

After viewing the implemented menu, I preferred the earlier concept's
centered composition. The start screen was revised to use a large curved title,
a central claw and open tray, a prominent PLAY button, HOW TO PLAY below it and
three illustrated level cards along the bottom. The earlier BEST SCORE badge
became a coin wallet; stars became best-earnings records. The paid-entry rules,
new levels, unlocks and persistent progress remain part of this layout.

I requested a start menu, money instead of stars, increasing same-color
rewards, a deduction for empty grabs and two extra levels. Level 2 starts empty
with three left-side launchers and a right recycler. Level 3 is faster, changes
the launcher layout and introduces uncatchable bullets with a pre-level explanation.
I specified a 200-coin fee for every entry, plus full progress reset
when funds are insufficient. Initial 500 coins and 50-coin miss penalties follow
the planning proposal. A confirmed reset clears all accumulated records.

Codex implemented the campaign controller, procedural start/menu illustrations,
coin persistence and stream physics. Initial automated stream trials found no
catches with the old slow claw closure. Closure was accelerated for Levels 2/3;
the same two-finger geometry checks remain mandatory, and deterministic trials
now demonstrate both real catches and misses in each stream level. This is
automated tuning evidence, not a human playtest or proof of final difficulty.

Retry is paid even through the R shortcut. Reading instructions does not charge.
Only delivered balls earn coins; recycled free balls do not cost a miss. Closing
the window keeps recorded coins/unlocks but forfeits the current paid round.
Save errors are shown in the interface instead of silently discarding progress.

Further playtesting could check how clearly players understand entry fees,
same-color bonuses, the recycler, the bullet briefing and RESET ALL.

### Startup font bug reported by me

I supplied a traceback from an actual launch: Pygame's Windows
system-font discovery passed a non-string registry value to `splitext`, causing
a `TypeError` before the first frame. The renderer was changed to open known
font files directly and fall back to Pygame's bundled default if loading fails.
An automated regression reproduced the exception before the change. Checks were
added for the broken discovery path, missing files and a corrupted font file.
This runtime bug report is separate from the classmate playtest feedback
recorded above.

I use Git commits to record the implementation and subsequent changes. This
process record describes the feedback I received, the decisions I made and the
changes implemented with Codex assistance.

