# Iteration four: training, original audio and ending sequences

## Changes

The sword pose, sweep collision, four-hit damage multipliers, enemy tuning,
wave composition and controls remain intact. New code is concentrated in
`tutorial.py`, `audio.py`, World lifecycle/event hooks and presentation.

`Tutorial` has movement, attack, combo, dodge and complete stages. Movement
requires 80px of actual WASD displacement. Attack requires contact. Combo
requires connected strikes 1, 2, 3 and 4 in order, followed by an 0.85s visual
confirmation. The dummy has a health floor and cannot die prematurely.

Dash training uses an 0.9s announced emitter, harmless 75px/s projectiles and
two completion routes: a projectile contact evaded during invulnerability, or
two accepted dashes with at least 2.5s of practice. No precise timing gate is
required. Completion stays visible for 1.4s, then enters the arena. ENTER or
the existing skip button bypasses training at any point. The main menu's
training button starts it again.

## Local audio

The game ships six original music tracks and nineteen original effects, all
real PCM WAVs. See [ASSETS.md](ASSETS.md) for source/license boundaries and the
per-file inventory; no external downloads were successfully incorporated.

`AudioManager` loads effects with `pygame.mixer.Sound` and streams background
tracks through `pygame.mixer.music`. It selects menu, tutorial, arena, boss,
victory or defeat music, caches the current selection and does not restart it
on each frame. Defeat music starts during player collapse and continues into
the defeat screen. Menu/tutorial/arena/boss loop; ending fragments play once.

Music fades down before a change and ramps up afterward, using nonblocking
updates. Pause reduces the music level. Defaults are 30% music and 65% effects.
Menu and pause offer separate volume buttons and mute. M toggles mute; F5/F6
adjust music and F7/F8 adjust effects. These additions do not replace existing
controls. Volume preferences last for the application session, not across runs.

World queues event names on accepted swings/dodges, real contacts, actual shots,
deaths, boss warning/spawn/destruction and lifecycle transitions. The app drains
them once per frame. Short same-sample cooldowns combine dense multi-target
hits without frame-by-frame repetition. Finisher swing and contact have separate
sounds: a miss never plays the contact effect. Muted/disabled audio drains events
too, preventing a backlog when sound is restored.

Missing/unreadable files are reported in `AudioManager.diagnostics` and skipped.
Mixer initialization failure leaves the game playable and shows audio as
unavailable in the controls panel. No runtime network access or asset generation
is required.

## Nonblocking endings

Configurable times in `neon/balance.py`:

- `BOSS_DESTRUCTION_TIME = 3.10` seconds.
- `BOSS_EXPLOSION_AT = 1.40` seconds.
- `PLAYER_DEFEAT_TIME = 1.75` seconds.
- `ENDING_FADE_TIME = 0.50` seconds.

On the boss's killing blow, World preserves the final blade impact, stops enemy
AI/spawning/projectiles and enters `boss_dying`. The last swing can recover but
player translation and combat inputs are blocked. The boss flickers, its core
loses energy, sparks appear, and at 1.4s an explosion emits pixel fragments.
Ruins and particles remain before the final fade. Only after 3.1s does World
enter victory and emit its cue once. No sleep or blocking wait is used.

Player zero HP enters `player_dying`, clears harmful projectiles and blocks
combat. A short collapse/discharge precedes defeat after 1.75s. Ending screens
fade their backdrop and offer replay, main menu and exit. Both endings keep
the loop and audio active. Terminal feedback continues dissipating normally.

Scene entrance dimming, objective confirmation, existing wave breaks and boss
warnings connect the flow without introducing a new gameplay system.

## Technical verification

Commands from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q main.py neon tests tools
.\.venv\Scripts\python.exe main.py --smoke-test
.\.venv\Scripts\python.exe -m tools.capture_preview
```

The test suite loads every actual WAV, plays every effect through SDL dummy
audio and starts each music track, checking mixer activity and load counts.
That proves decoding, playback calls and routing; **it is not a listening test**.
The unavailable-device case is simulated at mixer initialization. A temporary
empty asset directory verifies missing-file behavior. Combat event tests prove
once-only swing/contact/destruction/victory cues and real killing-blow feedback.

New tutorial tests complete all objectives, including the real projectile-evade
route and the forgiving two-dash route. Existing sword tests use an explicit
combat-training fixture rather than the new movement objective. Arena full-run
victory is tested separately from the full tutorial. Progression tests now wait
through boss destruction rather than assuming immediate victory.

## Manual acceptance checks

Launch `.\.venv\Scripts\python.exe main.py` with a working output device:

1. Hear the menu ambience. Change both volume controls and mute/unmute; make
   sure effects remain distinct from music. Repeat in pause.
2. Complete movement, one contact, a full connected combo and dash practice.
   Check the confirmation and completion messages. Repeat using the other
   dash route. Try ENTER at each stage and repeat training from the menu.
3. Listen for tutorial, wave and boss music changes. Pause/resume and stay in
   each scene; tracks must not restart every frame or after player collapse.
4. Compare swings in empty space with contacts, especially the fourth hit.
   Verify projectile, damage, enemy-death and boss cues match visible events.
5. Complete all waves, dodge Sentinel-X's signals and kill it. Observe the
   final impact, unstable core, explosion, debris and fade for about 3.1s before
   VICTORIA / Sentinel-X derrotado appears. Controls must not skip the ending.
6. Lose all HP. Observe collapse before defeat, then test replay, menu and exit.
7. Repeat offline. If practical, test without an output device; the game should
   remain playable. Assess sustained 60 FPS and Linux separately.

No new human play/listening session, native device test or Linux run is claimed.
Static images show selected keyframes, not a recording of the animation.
Procedural music is intentionally modest; human evaluation of repetition,
loudness, timbre and combat feel remains pending.
