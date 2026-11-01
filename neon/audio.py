"""Local mixer audio with event consumption, volume fades and silent fallback."""

from collections import Counter
from pathlib import Path

import pygame
from neon.preferences import load_audio_preferences, save_audio_preferences


AUDIO_ROOT = Path(__file__).resolve().parents[1] / 'assets' / 'audio'
EFFECT_NAMES = (
    'swing', 'swing_heavy', 'hit', 'hit_heavy', 'spark', 'dash', 'enemy_shot',
    'projectile_hit', 'enemy_hurt', 'enemy_destroy', 'boss_attack', 'boss_spawn',
    'boss_destroy', 'button', 'victory', 'defeat', 'tutorial_step', 'wave_start', 'player_hurt',
)
MUSIC_NAMES = ('menu', 'tutorial', 'arena', 'boss', 'victory', 'defeat')
EFFECT_ALIASES = {'overload': 'boss_spawn', 'boss_fan': 'enemy_shot',
                  'boss_radial': 'spark', 'area_warning': 'wave_start', 'area_impact': 'hit_heavy'}


class AudioManager:
    def __init__(self, root=AUDIO_ROOT, preferences_path=None):
        self.root = Path(root)
        self.preferences_path = preferences_path
        preferences = load_audio_preferences(preferences_path)
        self.music_volume = preferences['music_volume']
        self.effects_volume = preferences['effects_volume']
        self.muted = preferences['muted']
        self.enabled = False
        self.sounds = {}
        self.diagnostics = []
        self.current_music = None
        self.music_loads = Counter()
        self.played_counts = Counter()
        self.failed_music = set()
        self.last_played = {}
        self.clock = 0
        self.level = 0
        self.output_volume = 0
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(24)
            self.enabled = True
        except pygame.error as error:
            self.diagnostics.append(f'Audio device unavailable: {error}')
            return
        for name in EFFECT_NAMES:
            try:
                self.sounds[name] = pygame.mixer.Sound(str(self.root / 'sfx' / f'{name}.wav'))
            except (pygame.error, OSError) as error:
                self.diagnostics.append(f'Missing/unreadable effect {name}: {error}')
        for name, source in EFFECT_ALIASES.items():
            if source in self.sounds:
                self.sounds[name] = self.sounds[source]

    @staticmethod
    def scene_for(world):
        if world.stage in ('player_dying', 'defeat'):
            return 'defeat'
        if world.stage == 'victory':
            return 'victory'
        if world.stage == 'boss_dying' or (world.stage == 'arena' and world.boss_announced):
            return 'boss'
        return world.stage if world.stage in ('menu', 'tutorial') else 'arena'

    def play(self, name):
        if not self.enabled or self.muted or name not in self.sounds:
            return False
        # Dense multi-target hits may share one short sample, never a frame loop.
        minimum_gap = 0.045 if name in ('hit', 'hit_heavy', 'enemy_hurt', 'spark', 'enemy_shot', 'projectile_hit', 'area_impact') else 0
        if self.clock - self.last_played.get(name, -100) < minimum_gap:
            return False
        sound = self.sounds[name]
        sound.set_volume(self.effects_volume)
        try:
            channel = sound.play()
        except pygame.error:
            return False
        if channel is not None:
            self.played_counts[name] += 1
            self.last_played[name] = self.clock
            return True
        return False

    def adjust(self, category, delta):
        attr = 'music_volume' if category == 'music' else 'effects_volume'
        setattr(self, attr, max(0, min(1, getattr(self, attr) + delta)))
        self.save_preferences()

    def save_preferences(self):
        if not save_audio_preferences(self.preferences_path, self.music_volume, self.effects_volume, self.muted):
            message = 'Audio preferences could not be saved; session values remain active.'
            if message not in self.diagnostics:
                self.diagnostics.append(message)

    def update(self, dt, world):
        dt = min(max(dt, 0), 0.25)
        self.clock += dt
        events = world.drain_audio_events()
        if not self.enabled:
            return
        for event in events:
            self.play(event)
        desired = self.scene_for(world)
        if desired != self.current_music:
            self.level = max(0, self.level - dt / 0.35)
            if self.level == 0:
                pygame.mixer.music.stop()
                if desired not in self.failed_music:
                    try:
                        pygame.mixer.music.load(str(self.root / 'music' / f'{desired}.wav'))
                        pygame.mixer.music.set_volume(0)
                        pygame.mixer.music.play(0 if desired in ('victory', 'defeat') else -1)
                        self.music_loads[desired] += 1
                    except (pygame.error, OSError) as error:
                        self.failed_music.add(desired)
                        self.diagnostics.append(f'Missing/unreadable music {desired}: {error}')
                self.current_music = desired
        else:
            self.level = min(1, self.level + dt / 0.45)
        target = self.level * self.music_volume * (0.35 if world.paused else 1)
        if world.stage == 'boss_dying':
            target *= 0.65
        if self.muted:
            target = 0
        self.output_volume += (target - self.output_volume) * min(1, dt * 12)
        pygame.mixer.music.set_volume(self.output_volume)

    def toggle_mute(self):
        self.muted = not self.muted
        self.save_preferences()
        if self.enabled and self.muted:
            pygame.mixer.stop()
            pygame.mixer.music.set_volume(0)
            self.output_volume = 0
