# Current validation: combat polish

Validation date: 2026-10-31. Same Windows/Python/pygame environment as below.

| Check | Result | Boundary |
| --- | --- | --- |
| unittest suite | PASS: 31 tests | Includes all prior gameplay checks plus sword and UI regressions |
| Syntax compilation | PASS | `main.py`, `neon`, `tests`, `tools` |
| Entry-point smoke test | PASS: 120 frames | SDL dummy window; not native gameplay or an FPS benchmark |
| Preview generation | PASS: 9 PNG fixtures | Seven screens, a finisher miss and a four-swing contact sheet |

New checks cover hand anchoring, continuous return to rest for all four swings,
strike-only swept collision, hits in four aim directions at 30/60/120 updates/s,
actual moving trail positions and expiration, finisher hit/miss feedback,
contact location, controlled shake decay, terminal-state effect decay, clean
tutorial transitions, footer bounds and a HUD unaffected by camera shake.
The old fixed central slash pixel is guarded by a rendering regression test.
The once-per-enemy-per-swing, buffered input, full 18-enemy victory and real
enemy-caused defeat tests still pass.

The first new test run failed because the shared weapon module did not exist.
After implementing swept collision, four old tests failed because they assumed
the old whole-sector damage occurred immediately at 0.06 seconds, or measured
range from the feet instead of the hand. They now wait for actual contact or
completion of the swing; their damage and no-duplicate-hit assertions remain.

Current static fixtures inspected: menu, tutorial, finisher contact, finisher
miss, the four-swing sequence, arena, pause, victory and defeat. They support
layout/pose inspection, not a claim of manual gameplay validation.

Manual game feel, physical input in a native window, sustained 60 FPS and Linux
execution remain pending. The user's screenshots and manual report describe
the previous build. No new human play session is claimed by this update.

Commands are unchanged from the historical section below. Detailed manual
steps: [combat polish guide](COMBAT_POLISH.md). The screenshot tool now uses
both render passes; the current PNG files replace the original preview files.

# Historical MVP validation

Validation date: 2026-10-30.

## Environment

- Windows host, Python 3.12.6.
- Existing project interpreter: `.venv/Scripts/python.exe`.
- pygame-ce 2.5.8, SDL 2.32.10.
- No dependencies installed or upgraded during implementation.

## Automated checks

Run from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q main.py neon tests tools
.\.venv\Scripts\python.exe main.py --smoke-test
.\.venv\Scripts\python.exe -m tools.capture_preview
```

Results:

| Check | Result | Scope |
| --- | --- | --- |
| unittest suite | PASS: 19 tests | Real simulation, real input handlers and SDL dummy rendering |
| Syntax compilation | PASS | Entry point, game modules, tests and preview tool |
| Entry-point smoke test | PASS: 120 frames | 960×540 display surface, 480×270 internal surface, clean exit |
| Preview generation | PASS: 7 PNG files | Menu, tutorial, arena, finisher, pause, victory and defeat |

The tests cover normalized diagonal movement, sword direction/range, four-hit
combo and expiration, invulnerability, dodge cooldown, enemy pursuit and attack
telegraphing, one hit per target per swing, tutorial completion and omission,
wave progression, pause, restart, focus-loss pause, quit handling and all screens.
An identical strike produces one hit and 22 damage at 30, 60 and 120 updates/s.

Two longer simulation tests validate outcomes through the actual combat rules:

- An automated controller completes the tutorial and all three waves, defeating
  all 18 enemies with normal player health, real sword damage and legal dodges.
  It does not inject kills or change actor statistics.
- An idle player loses all health to real enemy attacks and reaches defeat.

A separate progression test marks enemies dead to isolate wave transitions;
that test is not the evidence for complete combat victory.

Tests were introduced before their corresponding combat/progression modules;
initial runs failed because those modules did not yet exist. During integration,
one telegraph test needed to account for the enemy's initial attack cooldown;
one newly inserted test temporarily captured another test's final assertions.
Both test issues were corrected without weakening gameplay rules.

## Visual inspection

The generated menu, tutorial, arena, finisher, pause, victory and defeat images
were inspected as static render fixtures. They show the original armored
sprites, cyan/purple facility palette, readable HUD and distinct finisher.
The tutorial objective was given a dark backing after inspection, and the
background player was removed from the title screen.

Screenshots under `docs/screenshots/` can be regenerated with the preview tool.
They deliberately stage actors and outcomes to exercise drawing; their victory
and defeat images are not proof of a manually completed game.

## Remaining manual checks

- Native Windows window, mouse aiming, physical keyboard response and game feel.
- Human assessment of difficulty, attack readability and tutorial clarity.
- Sustained 60 FPS on target hardware. The loop targets 60 FPS; the headless
  smoke test is not a performance benchmark.
- Linux installation and native runtime. The code uses portable pygame/Python
  APIs and relative project imports, but Linux was not executed here.

No manual gameplay session or Linux validation is claimed. Git and GitHub
operations remain the developer's responsibility; none were performed.
