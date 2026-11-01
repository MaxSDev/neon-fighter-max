# Combat polish: 2026-10-31

## Problems and localized changes

The former renderer moved the sword pivot between idle and attack. It also
animated a sweep independently of a whole-sector collision check. The finisher
rendered a diagonal at fixed screen coordinates. Small text was rasterized at
480×270 and enlarged with the world, exposing malformed-looking small glyphs.

`neon/weapon.py` now owns a small procedural phase machine: idle, windup,
strike and recovery, derived from the existing attack timer. Both collision and
rendering use its `SwordPose`, with a hand attached to the visible forearm.
Aim is locked at attack start; subsequent attacks use the current mouse aim.
The sword alternates swing direction, accelerates through the strike and returns
to a common rest pose. The finisher has a wider sweep and temporary energy-blade
extension, which retracts during recovery. Total durations remain 0.26 s for
normal swings and 0.32 s for the finisher, preserving combo/input timing.

Collision samples the blade swept during each simulation substep, including
player displacement. Only strike-phase samples can damage a target. Enemy
bodies use a 9px circle centered 10px above their feet; blade tolerance is 2px.
The existing per-swing hit set prevents duplicate damage to the same enemy.
These are geometric hitboxes, not per-pixel silhouette masks.

`Player.sword_trail` retains real world-space poses for 55ms, capped at 12
samples. The renderer draws fading strips between those poses. Contact records
anchor bursts, rings and short star flashes at the actual blade/body collision.
Normal contacts use cyan; finisher contacts use purple and a brief low-opacity
impact frame. A finisher miss still animates its purple blade and trail, but
does not create contact particles, flash, hitstop or camera shake.

Hitstop remains 28ms / 55ms for normal / final contacts. Camera amplitude is
capped at 2.8 internal pixels (about 6 window pixels) and decays at 18px/s.
The UI is outside the camera transform. Terminal screens disable camera shake
and allow feedback to dissipate without advancing gameplay. Entering the arena
clears old tutorial contact effects so they cannot appear over the wave intro.

`Renderer.draw()` draws the 480×270 world. `Game.frame()` scales it by exactly
2×, then `Renderer.draw_ui()` renders native 960×540 text and UI geometry.
Font rasters are not enlarged. The smallest font request is now 24 native
pixels; pygame's bundled font is used without external assets or smoothing.
Input and button rectangles retain logical coordinates, so mouse hit testing
remains compatible with the existing controls.

## Configurable balance

Edit `BASE_SWORD_DAMAGE` and `COMBO_DAMAGE_MULTIPLIERS` in `neon/settings.py`:

| Swing | Multiplier | Rounded damage | Knockback speed |
| --- | --- | --- | --- |
| 1 | 1.00 | 22 | 130 |
| 2 | 1.15 | 25 | 130 |
| 3 | 1.30 | 29 | 130 |
| 4 | 2.10 | 46 | 240 |

Knockback values are internal pixels/s with exponential damping. Normal stun
is 0.18s and final stun is 0.30s. Wave counts, enemy types, health, movement,
dodge rules and between-wave healing are unchanged. The stationary tutorial
drone continues to act as a safe target; test physical knockback in the arena.

## Manual acceptance guide

Launch from the project root:

```powershell
.\.venv\Scripts\python.exe main.py
```

1. **Text:** inspect the title subtitle, HUD labels, tutorial objective, bottom
   controls and pause buttons at the normal 960×540 window size. Accents and
   lowercase letters should be distinct, with no clipped text. Prefer 100%
   desktop scaling for the first comparison; OS DPI scaling may rescale the
   entire window independently of the game's exact 2× world scaling.
2. **Rest:** enter the tutorial, leave WASD untouched and move the mouse around
   the robot. The grip should remain on the visible arm and mirror with the
   sprite. The blade should not orbit the torso. Its angle follows aim while
   idle and returns to the same offset after each attack.
3. **Four swings:** stay away from the drone and tap J at roughly 0.28–0.34s
   intervals. Watch the four HUD marks: the swings alternate direction and the
   fourth is wider and purple. The pause between sequences should reset the
   combo. Compare `screenshots/combat-sequence.png` for staged phase poses.
4. **Blade/hitbox:** approach the drone and aim at its body. During an active
   swing, damage should appear as the visible blade crosses it. Targets beyond
   the blade or behind the swing should remain unharmed. Moving into range
   only after the strike should not cause a recovery-phase hit. One swing must
   show only one damage number per enemy, including when hitstop holds contact.
5. **Contact effects:** in the arena, hit an enemy and observe the contact flash,
   short sparks, damage number, recoil and slight freeze. Repeat while moving;
   the trail should remain behind actual past blade positions.
6. **Finisher hit versus miss:** first chain four swings into empty space in
   the tutorial: the fourth must have a purple trail but no contact flash,
   sparks, hitstop or shake. For a connecting finisher, skip the tutorial,
   perform three swings away from enemies, then aim the fourth at a nearby
   enemy. Contact should create a stronger local burst and 46 damage. The
   tutorial clears feedback immediately on its fourth successful hit as it
   transitions, so use the main arena to judge the complete impact effect.
7. **Camera:** compare normal and final contacts. Shake should last briefly,
   settle fully and leave HUD/cursor steady. Pause, resume and finish a run;
   victory/defeat screens must not continue shaking.

All seven checks remain pending a new human play session. Automated checks
and static image inspection do not establish subjective weight, balance or
sustained 60 FPS. No Linux native run was performed.

## Remaining limits

The character still uses two mirrored body facings, a procedural forearm and
the existing walk cycle rather than authored directional attack sprites. Sword
collisions approximate bodies with circles. The glow is a short alpha effect,
not a dynamic lighting system. There is no impact-flash accessibility setting
yet; the full-screen tint is deliberately brief and low-opacity. No packages,
external fonts, enemy types or Git/GitHub operations were added.
