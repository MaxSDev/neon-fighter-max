# Neon Fighter Max

A playable, offline top-down action prototype: an armored android, a large
energy sword and three short waves inside an abandoned technological facility.
The entire game interface is in Spanish.

## Run

Requires Python 3.12 and `pygame-ce==2.5.8`. No other packages are needed.

Windows PowerShell, from the project directory:

```powershell
# Only if a virtual environment has not already been created:
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The existing project environment already contains the required pygame-ce version.
Installation may require internet access; gameplay never does.

Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

The window is fixed at 960×540. The game renders at 480×270 and uses exact 2×
nearest-neighbor scaling. Text and interface geometry are drawn afterward at
960×540, without upscaling small glyphs. The loop targets 60 FPS; movement uses elapsed time.

## Controls

| Input | Action |
| --- | --- |
| WASD | Move in eight directions |
| Mouse | Aim |
| Left click / J | Swing the sword; repeat to chain up to four strikes |
| Left / right Shift | Dodge in the movement direction, or aim direction while stationary |
| Esc | Pause / resume |
| Enter | Start from the menu |
| R | Restart after victory or defeat |

The tutorial asks for four successful hits on a durable training drone. The
`OMITIR` button skips to the arena. Wave 1 contains five melee drones; wave 2
has five drones and two ranged units; wave 3 has five drones, three fast units
and two ranged units. Sentinel-X arrives after all three waves. Victory requires
destroying this miniboss, not just clearing wave 3.

Enemies arrive one at a time after a purple spawn warning, with at most five
active units. Spawns are checked against player distance, existing enemies,
arena boundaries and decorative prop rectangles, including after the warning.
Fast units have shorter attack timing, ranged units retreat and fire fixed-aim
orange projectiles, and Sentinel-X alternates context-dependent melee slams
and a three-shot energy spread. Orange circles or dashed trajectories announce
attacks; move or dodge before they resolve. Boss recovery is an attack window.

All enemy health, damage, movement and timing, projectile parameters, spawn
limits and wave composition are in `neon/balance.py`. See the
[iteration-three guide](docs/ITERATION_3.md) for values and manual checks.

Sword attacks sweep a hand-anchored blade and can hit each enemy once per swing.
Preparation, strike and recovery share one pose calculation for drawing and
collision. Damage only occurs during the strike phase, along the swept blade.
The fourth strike has extended reach, stronger knockback, a purple trail and a
brief impact frame when it connects. Clicks shortly before recovery ends are
buffered. Holding the attack button does not automatically attack.

Damage is configurable in `neon/settings.py`: base damage 22 multiplied by
`(1.0, 1.15, 1.30, 2.10)`, rounded to `(22, 25, 29, 46)`. The fourth strike
extends the energy blade during the attack and retracts to its normal rest
length. Hit effects originate at actual contact, including the finisher.

The HUD shows health, the four-step combo, dodge recovery and wave number.
Damage grants brief invulnerability. Clearing a wave restores up to 15 health
before a short break. Starting the arena restores full health. Losing window
focus pauses active play automatically.

## Modules

| File | Responsibility |
| --- | --- |
| `main.py` | Entry point and optional headless smoke test |
| `neon/app.py` | Window, controls, menu actions and presentation loop |
| `neon/settings.py` | Resolution, arena boundaries and shared palette |
| `neon/combat.py` | Player/enemy movement, timers, damage and actual sword pose history |
| `neon/weapon.py` | Shared weapon phases, hand anchor, pose and swept collision |
| `neon/world.py` | Tutorial, waves, combat resolution, particles and outcomes |
| `neon/balance.py` | Enemy, projectile, spawn, wave and miniboss tuning |
| `neon/enemies.py` | RangedEnemy, Sentinel and configured enemy factory |
| `neon/projectiles.py` | Energy shots, lifetime, bounds and swept collision |
| `neon/art.py` | Original pixel sprites, floor tiles, consoles and lighting |
| `neon/renderer.py` | Drawing, sword animation, HUD, buttons and overlays |
| `tests/` | Standard-library unittest checks of gameplay and rendering |
| `tools/capture_preview.py` | Reproducible screenshots of staged render fixtures |

Simulation does not depend on the display. It subdivides updates into steps of
at most 1/120 second to avoid missing sword timing windows at lower frame rates.
Delays beyond 0.25 seconds are discarded to avoid large jumps after a stall.
Sprites and the arena background are generated once and cached. Particles are
capped at 220, active enemies at five and projectiles at 32. Sword history and
impact records retain their existing caps.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q main.py neon tests tools
.\.venv\Scripts\python.exe main.py --smoke-test
.\.venv\Scripts\python.exe -m tools.capture_preview
```

On Linux, substitute `.venv/bin/python` for the Windows interpreter path.
The smoke test uses SDL dummy drivers, renders 120 menu frames and exits.
The test suite additionally exercises controls, combat, progression and every
screen. Preview screenshots are staged fixtures, not recordings of manual play.
See [validation results](docs/VALIDACION.md) for the actual checks and limits.
See [combat polish and manual test guide](docs/COMBAT_POLISH.md) for the current
animation, effects, balance settings and seven manual acceptance checks.

## Art and prototype limits

All game graphics are original procedural drawings and hand-authored pixel
patterns in `neon/art.py`; no external art packages or commercial sprites were
used. Text uses pygame's bundled default font. `assets/` remains available for
future project-owned resources. Screenshots are generated from this code.

This first prototype has no audio, save system, controller support, obstacles
with pathfinding or settings screen. The tutorial drone is stationary and safe.
Facing uses horizontal sprite mirroring; sword aim is continuous in all directions.
Environmental props are decorative. Lighting is painted into the background;
there are no dynamic shadows. Camera shake, hitstop and impact frames are simple
effects. Balance, native-window game feel, sustained FPS and Linux runtime
compatibility still require manual validation.
