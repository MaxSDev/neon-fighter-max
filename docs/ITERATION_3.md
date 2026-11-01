# Iteration three: waves, energy enemies and Sentinel-X

## Architecture and progression

The existing World owns the wave counter, intermissions and outcomes. Its wave
spawn now fills a queue rather than constructing every actor immediately.
`SpawnTicket` reserves a visible warning position for 0.70s. After each actual
spawn, there is a 0.85s delay before the next warning. At most five enemies are
active. The queue entry is consumed only after a valid materialization. A wave
cannot end while queued enemies or a warning remain.

Spawn candidates are bounded to the arena, exclude the complete sprite bounds
from the shared prop rectangles and maintain 95px from the player (120px for
the boss), plus spacing from existing enemies. They are checked again after
the warning. If the player enters it, the warning is discarded and the same
queue entry is retried at another safe position; an unsafe spawn is never forced.

| Wave | Drones | Fast | Ranged | Total |
| --- | --- | --- | --- | --- |
| 1 | 5 | 0 | 0 | 5 |
| 2 | 5 | 0 | 2 | 7 |
| 3 | 5 | 3 | 2 | 10 |

Two-second intermissions and up to 15 health recovery remain. After wave 3,
an alert and a separate spawn warning introduce Sentinel-X. Its defeat clears
remaining projectiles and plays an 0.85s destruction sequence before victory.
Restart reconstructs all state, including queues, projectiles and boss flags.

## New classes and responsibilities

- `EnemyStats` and `ProjectileStats` in `neon/balance.py` hold shared tuning.
- `create_enemy()` builds the appropriate enemy class with configured stats.
- Basic `Enemy` remains the melee implementation. Fast enemies reuse it with
  different timing; shared hit reaction remains in `advance_reaction()`.
- `RangedEnemy` retreats below its preferred range, approaches when too far,
  pauses to telegraph and fires in the direction locked at warning start.
- `Sentinel` adds an announced radial melee attack, a locked three-projectile
  spread, visible recovery and reduced knockback/stagger. Sword hits do not
  cancel its warning, so the player must still respect announced attacks.
- `Projectile` has fixed velocity, lifetime and radius. Collision sweeps relative
  motion against the player's body, clipped to remaining projectile lifetime.
  A contact consumes the projectile even if invulnerability prevents damage.
- `World._collect_dead()` counts and removes deaths once; `_advance_progression()`
  waits for the queue and handles boss arrival/destruction. Presentation remains
  in `art.py` and `renderer.py`, retaining native UI and the existing sword.

## Tuning

All values below are configurable in `neon/balance.py`; distances and speeds use
the 480×270 internal world. Cooldown begins after attack resolution; total cadence
also includes preparation and any recovery/stagger.

| Enemy | HP | Damage | Speed | Preparation | Cooldown |
| --- | --- | --- | --- | --- | --- |
| Drone | 58 | 12 | 39 | 0.42s | 1.05s |
| Fast | 44 | 8 | 49 | 0.23s | 0.64s |
| Ranged | 48 | 10 | 35 | 0.60s | 1.60s |
| Sentinel-X melee | 520 | 24 | 28 | 0.65s | 1.25s |
| Sentinel-X energy | same boss | 18 per shot | same boss | 0.90s | 1.80s |

Fast movement matches the previous last-wave drone speed; attack timing is
shorter and damage is reduced. Optional fast-unit dodges were omitted to keep
the first behavior predictable. Ranged units prefer 104–136px distance.

Normal energy shots travel at 100px/s for at most 3.2s with radius 3px. Boss
shots travel at 125px/s for at most 3s with radius 5px, at -16°, 0° and +16°.
Shots are not homing. At most 32 projectiles may exist. They cannot be parried;
move or dash to avoid them. Prop decorations do not block projectiles.

Sentinel-X recovers for 0.55s after each attack. At close range it can slam;
after a slam it selects energy, and at long range it selects energy rather
than swinging at empty space. It still moves closer during downtime. Its dark
armor, red visor, orange core and larger silhouette distinguish it from normal
units. The upper health bar displays remaining boss HP.

## Manual checks

Run `.\.venv\Scripts\python.exe main.py` from the project directory.

1. Skip or complete training. Verify purple warnings precede enemies, counts
   are 5 / 7 / 10 across waves and never more than five enemies coexist. Stand
   on a warning and check that it relocates instead of spawning on the player.
2. Compare normal pink drones with green fast units in wave 3. Fast preparation
   should remain readable but resolve sooner. Move out of the orange circle or
   time Shift to avoid damage; compare attack frequency.
3. In waves 2–3, approach a magenta gunner: it should retreat, announce its aim
   with a dashed line, then fire a visible orange shot. Change direction after
   the warning; the shot must keep its original course. Repeat with dash.
4. Clear all queued enemies. Sentinel-X should arrive after the third wave with
   a boss alert, safe spawn warning and upper health bar. No victory yet.
5. Stay close to inspect its orange melee circle; stand farther away to inspect
   the three dashed energy paths. Dodge the resolution and use recovery to
   attack. Verify sword damage lowers its health bar and hits produce particles.
6. Kill the boss: observe the brief destruction, then victory. Press R and
   confirm a clean tutorial/restart. Also pause while shots and warnings exist;
   neither should advance during pause.
7. Recheck all four sword attacks, finisher misses/contacts, HUD legibility and
   camera settling. These systems retain the prior iteration's behavior.

## Validation limits

Automated full-run victory proves a legal route with one deterministic controller
and seed, not human difficulty or universal balance. Static render fixtures are
generated by `python -m tools.capture_preview`; they deliberately stage combat
states. No new manual gameplay or Linux native runtime is claimed.

The arena retains decorative props, not a new collision/pathfinding system;
spawn exclusion uses their visual rectangles. Actors may walk through those
decorations as before. Hitboxes remain circles. No fast-unit evasive AI, audio,
music, Ultimate ability, external assets, dependencies or Git operations were
added. The loop targets 60 FPS; sustained hardware performance remains unmeasured.
