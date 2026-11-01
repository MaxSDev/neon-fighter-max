"""Load and play real WAV assets through SDL's dummy audio device."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame

from neon.audio import AUDIO_ROOT, AudioManager, EFFECT_NAMES, MUSIC_NAMES, EFFECT_ALIASES
from neon.world import World


class AudioTests(unittest.TestCase):
    def tearDown(self):
        pygame.mixer.quit()

    def test_all_real_assets_are_nonempty_pcm_and_effects_play(self):
        manager = AudioManager()
        self.assertTrue(manager.enabled)
        self.assertFalse(manager.diagnostics)
        for folder, names in (('sfx', EFFECT_NAMES), ('music', MUSIC_NAMES)):
            for name in names:
                path = AUDIO_ROOT / folder / f'{name}.wav'
                with wave.open(str(path)) as source:
                    self.assertEqual(source.getsampwidth(), 2)
                    self.assertGreater(source.getnframes(), 1000)
                    self.assertTrue(any(source.readframes(source.getnframes())))
        for name in (*EFFECT_NAMES, *EFFECT_ALIASES):
            pygame.mixer.stop()
            self.assertTrue(manager.play(name), name)

    def test_scene_music_loads_once_and_each_track_plays(self):
        manager = AudioManager()
        world = World()
        for stage, boss, expected in (
            ('menu', False, 'menu'), ('tutorial', False, 'tutorial'),
            ('arena', False, 'arena'), ('arena', True, 'boss'),
            ('victory', True, 'victory'), ('defeat', True, 'defeat')):
            world.stage, world.boss_announced = stage, boss
            for _ in range(60):
                manager.update(1 / 60, world)
            self.assertEqual(manager.current_music, expected)
            self.assertEqual(manager.music_loads[expected], 1)
            self.assertTrue(pygame.mixer.music.get_busy())
        for _ in range(60):
            manager.update(1 / 60, world)
        self.assertEqual(manager.music_loads['defeat'], 1)

    def test_events_are_consumed_once_and_muting_does_not_queue_backlog(self):
        manager = AudioManager()
        world = World()
        world.emit('dash')
        manager.update(0.1, world)
        manager.update(0.1, world)
        self.assertEqual(manager.played_counts['dash'], 1)
        manager.toggle_mute()
        world.emit('dash')
        manager.update(0.1, world)
        manager.toggle_mute()
        manager.update(0.1, world)
        self.assertEqual(manager.played_counts['dash'], 1)

    def test_missing_assets_and_unavailable_device_are_nonfatal(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            manager = AudioManager(directory)
            manager.update(0.1, World())
            self.assertTrue(manager.diagnostics)
        pygame.mixer.quit()
        with patch('pygame.mixer.init', side_effect=pygame.error('Unavailable test device')):
            manager = AudioManager()
            self.assertFalse(manager.enabled)
            manager.update(0.1, World())

    def test_player_dying_to_defeat_does_not_restart_music(self):
        manager = AudioManager()
        world = World()
        world.stage = 'player_dying'
        for _ in range(60):
            manager.update(1 / 60, world)
        world.stage = 'defeat'
        for _ in range(60):
            manager.update(1 / 60, world)
        self.assertEqual(manager.music_loads['defeat'], 1)


if __name__ == '__main__':
    unittest.main()
