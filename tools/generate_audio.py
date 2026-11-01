"""Create original offline electronic music and effects using only Python.

All waveforms, arrangements and deterministic noise are authored here. This
script never downloads content and is not needed while playing the game.
"""

from array import array
import math
from pathlib import Path
import random
import sys
import wave
import hashlib
import json

RATE = 22050
ROOT = Path(__file__).resolve().parents[1] / 'assets' / 'audio'
TAU = math.tau


def write_wav(path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = array('h', (round(max(-0.94, min(0.94, sample)) * 32767) for sample in samples))
    if sys.byteorder != 'little':
        pcm.byteswap()
    with wave.open(str(path), 'wb') as output:
        output.setparams((1, 2, RATE, len(pcm), 'NONE', 'not compressed'))
        output.writeframes(pcm.tobytes())


def note(midi):
    return 440 * 2 ** ((midi - 69) / 12)


def music(scene):
    tempo, beats, intensity = {
        'menu': (90, 24, 0), 'tutorial': (96, 24, 0.15),
        'arena': (120, 32, 0.65), 'boss': (135, 32, 1),
        'victory': (110, 8, 0.4), 'defeat': (70, 4, 0),
    }[scene]
    beat_length = 60 / tempo
    duration = beats * beat_length
    rng = random.Random(411 + len(scene))
    result = []
    roots = (40, 36, 45, 47) if scene != 'victory' else (48, 53, 55, 60)
    for index in range(round(duration * RATE)):
        t = index / RATE
        beat = t / beat_length
        bar = int(beat // 4)
        root = roots[bar % 4]
        local = t % (4 * beat_length)
        pad_env = min(1, local / 0.15, (4 * beat_length - local) / 0.25)
        chord = (0, 3, 7) if scene != 'victory' else (0, 4, 7)
        pad = sum(math.sin(TAU * note(root + 12 + offset) * t) for offset in chord) * 0.055 * pad_env
        pulse_time = (beat % 1) * beat_length
        bass = math.sin(TAU * note(root) * t) * math.exp(-pulse_time * 4) * (0.04 + intensity * 0.07)
        step = int(beat * 2)
        pluck_time = (beat * 2 % 1) * beat_length / 2
        melody = note(root + 24 + (0, 7, 12, 3, 7, 15, 12, 7)[step % 8])
        arp = math.sin(TAU * melody * t) * math.exp(-pluck_time * 18) * (0.025 + intensity * 0.06)
        noise = rng.uniform(-1, 1)
        kick = math.sin(TAU * (48 * pulse_time + 7 * (1 - math.exp(-pulse_time * 35)))) * math.exp(-pulse_time * 22)
        snare = noise * math.exp(-pulse_time * 40) * (0.12 if int(beat) % 4 in (1, 3) else 0)
        hat = noise * math.exp(-pluck_time * 100) * 0.035
        percussion = (kick * 0.14 + snare + hat) * intensity
        edge = min(1, t / 0.025, (duration - t) / 0.05)
        ending = min(1, (duration - t) / 0.7) if scene in ('victory', 'defeat') else 1
        result.append((pad + bass + arp + percussion) * edge * ending)
    return result


EFFECTS = {
    'swing': (0.16, 950, 180, 0.45), 'swing_heavy': (0.24, 600, 75, 0.55),
    'hit': (0.16, 320, 70, 0.55), 'hit_heavy': (0.28, 220, 40, 0.7),
    'spark': (0.12, 2600, 600, 0.65), 'dash': (0.23, 180, 1400, 0.45),
    'enemy_shot': (0.20, 1400, 220, 0.12), 'projectile_hit': (0.19, 700, 80, 0.55),
    'enemy_hurt': (0.10, 420, 140, 0.20), 'enemy_destroy': (0.35, 210, 35, 0.8),
    'boss_attack': (0.48, 180, 55, 0.5), 'boss_spawn': (1.20, 90, 380, 0.15),
    'boss_destroy': (1.6, 180, 24, 0.8), 'button': (0.10, 720, 1100, 0),
    'victory': (0.85, 520, 1040, 0), 'defeat': (1.1, 260, 45, 0.15),
    'tutorial_step': (0.35, 650, 1300, 0), 'wave_start': (0.40, 300, 600, 0.08),
    'player_hurt': (0.20, 240, 60, 0.35),
}


def effect(name, spec):
    duration, start, end, noise_mix = spec
    rng = random.Random(name)
    phase = 0
    samples = []
    for index in range(round(duration * RATE)):
        t = index / RATE
        progress = t / duration
        frequency = start * (end / start) ** progress
        phase += TAU * frequency / RATE
        tone = math.sin(phase) * 0.8 + math.sin(phase * 2.01) * 0.2
        envelope = min(1, t / 0.006) * (1 - progress) ** 1.8
        samples.append((tone * (1 - noise_mix) + rng.uniform(-1, 1) * noise_mix) * envelope * 0.75)
    return samples


def main():
    for scene in ('menu', 'tutorial', 'arena', 'boss', 'victory', 'defeat'):
        write_wav(ROOT / 'music' / f'{scene}.wav', music(scene))
    for name, spec in EFFECTS.items():
        write_wav(ROOT / 'sfx' / f'{name}.wav', effect(name, spec))
    manifest = []
    for path in sorted(ROOT.rglob('*.wav')):
        with wave.open(str(path)) as source:
            manifest.append({'file': path.relative_to(ROOT).as_posix(),
                             'seconds': round(source.getnframes() / source.getframerate(), 4),
                             'sample_rate': source.getframerate(), 'bytes': path.stat().st_size,
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                             'source': 'Original procedural synthesis: tools/generate_audio.py'})
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Generated 6 original music tracks and {len(EFFECTS)} original effects in {ROOT}')


if __name__ == '__main__':
    main()
