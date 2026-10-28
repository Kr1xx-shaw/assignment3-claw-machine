# Credits and provenance

- **Concept and direction:** the student's claw-machine brief, protected left
  collector, upward air jet, win/loss rules, flat illustration and English UI.
- **Course foundation:** SD5913 PFAD, 2026 Week 7 `Ball` class demonstration:
  https://github.com/sd5913/pfad/tree/2026/week07 . Its separation of per-object
  state and shared update behaviour informed this project. The claw, gate,
  collection, input system and game rules are new implementation for this brief.
- **Implementation assistance:** OpenAI Codex, disclosed in `PROCESS.md`.
- **Concept illustration:** built-in OpenAI `image_gen`, revised through the
  conversation. `assets/concept-corrected.png` is a design reference, not a
  runtime background. The final edit prompt is in `assets/concept-prompt.txt`.
- **Rendered game art:** procedural circles, lines, polygons and text in
  `view.py` and `app_view.py`; no third-party sprites, photographs, audio or logo assets.
  The start menu, coin campaign, stream levels and bullet rules follow the
  student's additional brief. Rendered menu screenshots come from game code.
- **Library:** Pygame 2.6.1, https://www.pygame.org/ , distributed under LGPL.
  Python is the runtime. Pygame is installed as a dependency and not vendored.
- **Typography:** Windows Segoe UI font files are loaded directly where available,
  bypassing system-font discovery. Pygame's bundled default font is used if those
  files are missing or unusable. No Windows font file is copied or redistributed.

