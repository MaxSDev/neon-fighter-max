# Current validation: iteration five

Validated 2026-10-31 in the existing Windows / Python 3.12.6 / pygame-ce 2.5.8
environment. No dependencies or new audio assets were added.

| Check | Result | Boundary |
| --- | --- | --- |
| unittest suite | PASS: 71 tests | Existing regressions plus settings/training flow and overload logic |
| Syntax compilation | PASS | `main.py`, `neon`, `tests`, `tools` |
| Entry-point smoke test | PASS: 120 frames | SDL dummy video/audio; no hardware performance/listening claim |
| Preview generation | PASS: 33 PNG fixtures | Includes settings, practice choice and overload patterns |

Tests prove audio-only INI round-trip, fallback/clamping, settings navigation,
no main-menu volume buttons, direct-arena restart, voluntary practice waiting
for a choice and ENTER skipping. The temporary directory contains only audio.ini;
there is no training/progress persistence. Capture and app tests opt out of the
real preference path. An early test wrote its audio settings to that path; the
test was isolated and its known generated preference file was removed.

Overload tests cover exact <=50% latching once, no activation on a lethal hit,
warning times and outputs for all four patterns, one-time area damage, dash
escape, actual fan/radial projectile gaps, cancellation of old hazards, one
activation event, no pattern start during stagger/live hazards or zero shot
budget, staggered ranged shots and boss death through the preserved ending.
The normal-stat arena controller still reaches victory with 23 kills.

The first new tests failed because the settings/phase APIs were absent. The old
restart assertion was updated from tutorial to arena, as explicitly requested.
Existing sword, audio, projectile and lifecycle checks remain passing without
skips. Real original audio files are unchanged; alias cues are loaded and played
through the same SDL dummy verification as the original effects.

Static images inspected: clean main menu, settings, voluntary training choice,
overload notice/core, fan, radial escape wedge and area warnings; pressure and
area discharge previews also retained. These are staged states, not a manually
played session. The user's iteration-four manual acceptance does not validate
this build's new phase-two balance.

Manual play/listening, restart across a real app launch, sustained 60 FPS and
Linux execution remain pending. Instructions and before/after tuning are in
[ITERATION_5.md](ITERATION_5.md). Commands are unchanged in the historical records.

# Historical validation: iteration four

Validated 2026-10-31 in the existing Windows / Python 3.12.6 / pygame-ce 2.5.8
environment. No dependencies installed or upgraded.

| Check | Result | Boundary |
| --- | --- | --- |
| unittest suite | PASS: 57 tests | Gameplay, interactive tutorial, endings, real WAV loading/playback and error paths |
| Syntax compilation | PASS | `main.py`, `neon`, `tests`, `tools` |
| Entry-point smoke test | PASS: 120 frames | SDL dummy video/audio; no native device or listening claim |
| Audio inventory | PASS: 25 actual WAV files, 3,411,106 bytes | Six music tracks, nineteen effects, reproducible source and SHA-256 manifest |
| Preview generation | PASS: 25 PNG fixtures | Includes tutorial stages and ending keyframes |

Full tutorial completion, ENTER/button skipping, menu training replay, both dash
completion paths, normal-stat arena victory, queued waves, projectiles, sword
phases and combos remain checked. Boss victory is delayed until the full 3.1s
ending; player defeat is delayed 1.75s. A real killing swing preserves contact
feedback and starts one destruction event. Ending inputs cannot move the player
or run enemy AI/spawning.

All actual WAVs decode as nonempty 16-bit PCM. SDL dummy audio accepts every
effect and each music scene; current-track load counters prove no per-frame
restart or restart between player collapse and defeat. Muting drains pending
events. Missing assets and unavailable mixer initialization are nonfatal.
These checks do not prove audible quality, physical speaker output or balance.

The new test targets initially failed because the new lifecycle/tutorial API
was absent. Earlier tests were adapted where behavior intentionally changed:
combat fixtures bypass movement teaching, immediate-death assertions now wait,
and the full arena controller waits through `boss_dying` rather than stopping
when combat input is disabled. A temporary test-file indentation error was
corrected; the final complete suite passes without skipped tests.

Static inspection covered the menu/audio panel, combo and dodge instructions,
boss unstable core/explosion/aftermath and player collapse. Final keyframe checks
also include movement, completion, fade, victory and defeat. These are staged
frames, not a manually played recording.

The user's third-iteration manual acceptance is context, not validation of this
new build. Listening, physical audio device behavior, native manual gameplay,
Linux and sustained 60 FPS remain pending. See [ITERATION_4.md](ITERATION_4.md)
for commands/manual checks and [ASSETS.md](ASSETS.md) for actual provenance.

# Historical validation: iteration three

Validated on 2026-10-31 with the existing Python 3.12.6 / pygame-ce 2.5.8
environment on Windows. No packages were installed or upgraded.

| Check | Result | Boundary |
| --- | --- | --- |
| unittest suite | PASS: 44 tests | Existing sword/control regressions plus progression, new AI and projectile checks |
| Syntax compilation | PASS | `main.py`, `neon`, `tests`, `tools` |
| Entry-point smoke test | PASS: 120 frames | SDL dummy driver; no native manual play or sustained FPS claim |
| Preview generation | PASS: 15 PNG fixtures | Includes ranged warning/shot, boss attacks/destruction and spawn warning |

Tests establish the requested 5 / 7 / 10 enemy compositions, a maximum of five
active enemies, staggered warnings, valid spawn bounds and prop exclusion,
revalidation if the player enters a warning, pause of warnings/projectiles,
queue-aware progression and victory only after boss destruction. The full-run
controller completes the tutorial, defeats all 22 regular enemies and Sentinel-X
using real sword damage, movement and legal dodges with normal player stats.
The scripted progression test separately injects zero HP to isolate lifecycle
transitions; it does not prove combat balance.

New AI checks cover faster melee cadence, ranged retreat and locked shot aim,
swept projectile contact, one-time consumption even during dash invulnerability,
expiry and valid bounds, announced boss melee/energy, recovery, dodge avoidance
and rendering of the boss health bar. Sword phase/contact, combo, hitstop,
native UI, victory/defeat and restart regressions remain passing.

An explicit red test reproduced a shot incorrectly considering player movement
after its lifetime expired (player HP 90 instead of 100). Collision now clips
relative player motion to the projectile's remaining lifetime; the regression
passes. Two earlier MVP tests were adapted because their assumptions changed:
18 kills became 23, and killing a visible batch no longer empties a wave queue.

Static images inspected for this iteration: mixed arena, ranged preparation,
visible energy projectile, Sentinel-X energy/melee warnings and destruction,
plus spawn warning, finisher, victory and defeat. These are staged fixtures,
not a human play session. Prior sword sequence checks also remain automated.

Native Windows input/game feel, difficulty assessment, sustained 60 FPS and
Linux execution remain pending. Reproduction commands are unchanged below;
manual steps and current tuning are in [ITERATION_3.md](ITERATION_3.md).

# Historical validation: combat polish

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
