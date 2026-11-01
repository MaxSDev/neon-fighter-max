# Iteration five: settings, training flow and Sentinel-X overload

## Menu and preferences

The main menu keeps the title, subtitle, ambience, protocol start, training and
exit, and adds AJUSTES. Audio controls are moved off the main composition into
a dedicated settings page, with music/effects levels, mute and VOLVER. The page
uses the existing `menu` World state, so menu music is not restarted. ESC also
returns to the main page. Existing M and F5–F8 shortcuts remain; pause retains
its quick audio controls.

`neon/preferences.py` stores only three whitelisted audio values in
`settings/audio.ini`: music volume, effects volume and mute. The file is written
after a user change, using a temporary file and replacement. Missing/malformed
values fall back or clamp to 0–1. An unwritable file adds a diagnostic and leaves
session controls working. Paths are relative to the project module location,
independent of the launch directory. No training record, JSON progress file or
database is created. The local audio preference file is excluded by `.gitignore`.

## Training navigation

- INICIAR PROTOCOLO retains the normal interactive tutorial, with ENTER skipping
  to the arena and automatic arena entry after completion.
- REINICIAR / R after victory or defeat resets the run directly into the arena.
- ENTRENAMIENTO starts voluntary practice. Completion stays in the existing
  tutorial state and offers CONTINUAR A ARENA or VOLVER AL MENÚ. ENTER still
  enters the arena. No practice completion persists across runs or launches.

Only a transient `practice_mode` flag changes this flow; objective mechanics,
safe training shots, combo confirmation and core controls are preserved.

## Difficulty changes

Damage values remain unchanged. Tuning is centralized in `neon/balance.py`.

| Parameter | Iteration 4 | Iteration 5 | Change |
| --- | --- | --- | --- |
| Drone preparation | 0.42s | 0.36s | -14.3% |
| Drone cooldown | 1.05s | 0.90s | -14.3% |
| Fast speed | 49 | 49 | unchanged |
| Fast preparation | 0.23s | 0.20s | -13.0% |
| Fast cooldown | 0.64s | 0.54s | -15.6% |
| Fast attack trigger distance | 23 | 26 | slightly more aggressive approach |
| Fast reach | 28 | 30 | small matching reach increase |
| Ranged preparation | 0.60s | 0.54s | -10% |
| Ranged cooldown | 1.60s | 1.36s | -15% |
| Sentinel-X max HP | 520 | 676 | +30% |
| Sentinel-X phase-one speed | 28 | 31.5 | +12.5% |
| Boss melee preparation | 0.65s | 0.60s | -7.7% |
| Boss melee cooldown | 1.25s | 1.10s | -12% |
| Boss energy preparation | 0.90s | 0.82s | -8.9% |
| Boss energy cooldown | 1.80s | 1.58s | -12.2% |
| Boss phase-one recovery | 0.55s | 0.49s | -10.9% |

Ranged units share a 0.24s minimum gap between actual volleys. A unit that must
wait keeps its aim warning visible rather than silently firing later. Projectile
speed, lifetime, damage, wave counts and the five-enemy cap remain unchanged.

## Phase two: overload

At alive HP <= 50%, Sentinel-X latches phase 2 once. It never switches back,
even if HP is manipulated upward in a test. A lethal hit does not start an
overload transition. Existing shots/areas and the current attack are cancelled;
an 1.15s safe transition, a two-second notice, environmental tint, brighter core,
energy particles and activation cue communicate the change.

Phase two uses an ordered cycle, not unconstrained random combinations:

| Pattern | Warning | Recovery | Cooldown | Escape opportunity |
| --- | --- | --- | --- | --- |
| Fan | 0.85s | 0.55s | 1.35s | Five fixed rays, 18° apart; walkable gaps at distance or dash |
| Area | 1.10s | 0.65s | 1.50s | At most two fixed 26px-radius marks; move outside or dash |
| Radial | 1.05s | 0.65s | 1.55s | Nine rays, with a 120° opening centered on locked aim |
| Pressure | 0.52s each | 0.43s | 0.95s | Two separately announced close attacks; move away or dash |

The first cycle is fan → area → radial → pressure twice. The next swaps fan
and radial, then cycles alternate. This supplies bounded variation without
randomly stacking attacks or removing escape windows. Pressure approaches
without teleporting; phase-two approach speed is 31.5 × 1.12 = 35.28. Phase-two
damage remains 24 for melee and 18 for energy/areas. Each zone resolves once.

The same projectile angles drive warnings and emitted bullets. Green lines
mark the radial opening. Zones track fixed positions chosen at preparation,
not the player's later motion. Their warnings pause with boss stagger. New
patterns do not begin while previous projectiles/areas remain. A 16-projectile
overload budget prevents incomplete/saturated patterns; the global cap remains
32. Cooldowns are lower bounds: hazard clearance may delay the next pattern.

`boss_patterns.py` owns `EnergyZone`, zone placement and projectile-angle
selection. Sentinel's existing timers retain windup/recovery/attack logic.
Overload hooks in World handle one-shot cues, cancellation and hazard updates.
Existing audio files provide distinct cue aliases; no new assets or downloads
are needed. The original 3.1s destruction and delayed victory remain intact;
death clears active zones and shots before that sequence.

## Validation

Reproduction commands:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q main.py neon tests tools
.\.venv\Scripts\python.exe main.py --smoke-test
.\.venv\Scripts\python.exe -m tools.capture_preview
```

The suite verifies settings layout/navigation, audio-only file round-trip,
invalid preferences, direct-arena restart, voluntary practice choice and ENTER
skip; threshold latching, every pattern's warning and output count, no attacks
through stun/live hazards or insufficient shot budget, area one-time damage and
dash escape, actual projectile gaps, one overload cue, staggered ranged shots
and overloaded-boss death cleanup through delayed victory.

The existing scripted normal-stat arena run still defeats all 23 enemies,
including Sentinel-X. This proves a legal deterministic route, not human balance
or survival against every pattern/seed. Tests and screenshot capture disable
real preference persistence or use temporary project-local directories.

## Manual checks

1. Open AJUSTES, change music/effects, toggle M, return and close/reopen the game.
   Values should persist; the main menu should have no volume controls.
2. Start a protocol, try ENTER skipping, then test voluntary ENTRENAMIENTO.
   On completion choose each destination. Win/lose and press R: arena directly.
3. Compare enemy attack pressure and readable warnings; dodge melee and shots.
   Watch two ranged units for staggered shots rather than a simultaneous volley.
4. Damage Sentinel-X to half HP. Check one overload message/cue, brighter core
   and a safe transition. Further hits must not restart the transition.
5. Practice fan gaps at distance, the green radial opening, escaping marked zones
   and both pressure swings. Confirm safe spaces match the visible warnings.
6. Kill the overloaded boss during an attack: hazards must stop, destruction
   must remain visible, then victory. Recheck all four sword hits and audio.

Manual difficulty, physical input, listening, sustained 60 FPS and Linux native
execution remain pending. The ordered cycle and hazard-clearance gate are
deliberate simplifications for readability and predictable escape opportunities.
Circles remain approximate collision shapes; decorative props still have no
pathfinding/collision beyond safe spawn exclusion.
