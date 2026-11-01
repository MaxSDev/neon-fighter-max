# Asset provenance

## Audio included in this project

All 25 shipped audio files are **original procedural resources created for
Neon Fighter Max in this iteration**. Their composition, synthesis, envelopes
and deterministic noise are implemented in [tools/generate_audio.py](../tools/generate_audio.py).
No third-party samples, commercial music, downloaded scripts or soundfonts are
used. Author/producer: Neon Fighter Max project, procedural implementation in
this repository. Source URL for every included file: the local generator link
above; there is no external source URL.

License/provenance status: original project-generated content, with no inherited
third-party audio license. This document does not claim these originals were
downloaded under CC0 or invent a Creative Commons grant for them. Their editable
source and WAV outputs are included with the project for reuse and redistribution
as part of the game.

Files live under `assets/audio/`. Format: mono PCM WAV, 16-bit, 22050 Hz.
`assets/audio/manifest.json` records each actual file's size, duration, sample
rate, SHA-256 and generator source. Total WAV payload: 3,411,106 bytes.

| Resource | Author | Source / URL | License provenance | Game use |
| --- | --- | --- | --- | --- |
| `music/menu.wav` | Project | Local generator above | Original procedural | Mysterious electronic menu loop |
| `music/tutorial.wav` | Project | Local generator above | Original procedural | Gentle training loop |
| `music/arena.wav` | Project | Local generator above | Original procedural | Rhythmic wave combat loop |
| `music/boss.wav` | Project | Local generator above | Original procedural | More intense miniboss loop |
| `music/victory.wav` | Project | Local generator above | Original procedural | Major-key ending fragment |
| `music/defeat.wav` | Project | Local generator above | Original procedural | Slow, dark ending fragment |
| `sfx/swing.wav` | Project | Local generator above | Original procedural | Accepted normal sword swing |
| `sfx/swing_heavy.wav` | Project | Local generator above | Original procedural | Accepted fourth swing, including misses |
| `sfx/hit.wav` | Project | Local generator above | Original procedural | Actual normal blade contact |
| `sfx/hit_heavy.wav` | Project | Local generator above | Original procedural | Fourth blade contact / boss final explosion |
| `sfx/spark.wav` | Project | Local generator above | Original procedural | Special contact sparks |
| `sfx/dash.wav` | Project | Local generator above | Original procedural | Accepted dodge |
| `sfx/enemy_shot.wav` | Project | Local generator above | Original procedural | Actual shot/volley emission |
| `sfx/projectile_hit.wav` | Project | Local generator above | Original procedural | Projectile/body contact, including invulnerable contact |
| `sfx/enemy_hurt.wav` | Project | Local generator above | Original procedural | Enemy receives sword damage |
| `sfx/enemy_destroy.wav` | Project | Local generator above | Original procedural | Normal enemy removed after death |
| `sfx/boss_attack.wav` | Project | Local generator above | Original procedural | Boss begins attack preparation |
| `sfx/boss_spawn.wav` | Project | Local generator above | Original procedural | Boss materializes |
| `sfx/boss_destroy.wav` | Project | Local generator above | Original procedural | Boss destruction begins, once |
| `sfx/button.wav` | Project | Local generator above | Original procedural | Menu/button actions |
| `sfx/victory.wav` | Project | Local generator above | Original procedural | Victory begins after destruction |
| `sfx/defeat.wav` | Project | Local generator above | Original procedural | Player defeat animation begins |
| `sfx/tutorial_step.wav` | Project | Local generator above | Original procedural | Training objective advances |
| `sfx/wave_start.wav` | Project | Local generator above | Original procedural | New wave enters its spawn queue |
| `sfx/player_hurt.wav` | Project | Local generator above | Original procedural | Player takes melee damage |

## External sources inspected, not incorporated

Checked on 2026-10-31:

| Source | Author | Official URL | Verified page license | Outcome |
| --- | --- | --- | --- | --- |
| Sci-fi Sounds | Kenney | https://kenney.nl/assets/sci-fi-sounds | Official page labels Creative Commons CC0 | ZIP request returned non-ZIP content; no files incorporated |
| Impact Sounds | Kenney | https://kenney.nl/assets/impact-sounds | Official page labels Creative Commons CC0 | ZIP request returned HTML; no files incorporated |
| Interface Sounds | Kenney | https://kenney.nl/assets/interface-sounds | Official page labels Creative Commons CC0 | ZIP request returned HTML; no files incorporated |
| Dark Sci-Fi Audio Pack | Not verified | https://opengameart.org/content/dark-sci-fi-audio-pack | Not verified because access failed | Page returned HTTP 403 through the web reader; not used |

Official Kenney pages were readable, but reading a CC0 listing is not proof of
a successful asset download. The initial terminal request was blocked by the
sandbox, then retried with approval. Bounded approved ZIP requests still did
not produce valid archives. Two alternative official packages were tried.
The authorized procedural fallback therefore supplies **both music and effects**.

## Reproduction and existing art

Run `.\.venv\Scripts\python.exe -m tools.generate_audio` to regenerate the
original WAVs and manifest. The generator only uses Python's standard library
and writes under `assets/audio/`; it does not access the network. The generator
is not called at game startup: shipped assets are loaded directly from disk.

Existing sprites, sword geometry, tiles and lighting remain project-authored
procedural pixel art. Text uses pygame's bundled default font. Screenshots are
rendered fixtures generated from this project's code.
