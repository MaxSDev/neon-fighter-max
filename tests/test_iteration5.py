"""Settings persistence, training navigation and overload acceptance tests."""

import os
from pathlib import Path
import tempfile
import unittest

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
from pygame import Vector2

from neon.app import Game
from neon.audio import AudioManager
from neon.enemies import create_enemy
from neon.world import World


class NavigationTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_audio_settings_round_trip_without_progress_files(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / 'audio.ini'
            audio = AudioManager(preferences_path=path)
            audio.adjust('music', -0.1)
            audio.adjust('effects', 0.1)
            audio.toggle_mute()
            restored = AudioManager(preferences_path=path)
            self.assertAlmostEqual(restored.music_volume, 0.2)
            self.assertAlmostEqual(restored.effects_volume, 0.75)
            self.assertTrue(restored.muted)
            self.assertEqual([p.name for p in Path(directory).iterdir()], ['audio.ini'])

    def test_restart_bypasses_training_and_practice_waits_for_choice(self):
        game = Game(preferences_path=None)
        game.action('play')
        self.assertEqual(game.world.stage, 'tutorial')
        game.action('restart')
        self.assertEqual(game.world.stage, 'arena')
        self.assertEqual(game.world.wave, 0)
        game.action('training')
        game.world.tutorial.advance('complete')
        for _ in range(240):
            game.world.update(1 / 120, Vector2())
        self.assertEqual(game.world.stage, 'tutorial')
        game.action('menu')
        self.assertEqual(game.world.stage, 'menu')

    def test_main_menu_has_settings_and_no_audio_buttons(self):
        game = Game(preferences_path=None)
        game.frame(0, [], Vector2(), (240, 150))
        self.assertIn('settings', game.renderer.buttons)
        self.assertNotIn('music_up', game.renderer.buttons)
        game.action('settings')
        game.frame(0, [], Vector2(), (240, 150))
        self.assertIn('music_up', game.renderer.buttons)
        self.assertIn('back', game.renderer.buttons)
        game.action('back')
        self.assertEqual(game.menu_page, 'main')

    def test_invalid_audio_preferences_fall_back_or_clamp(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / 'audio.ini'
            path.write_text('[audio]\nmusic_volume = nan\neffects_volume = 9\nmuted = yes\n', encoding='utf-8')
            audio = AudioManager(preferences_path=path)
            self.assertEqual(audio.music_volume, 0.3)
            self.assertEqual(audio.effects_volume, 1)
            self.assertTrue(audio.muted)
            path.write_text('unreadable ini contents', encoding='utf-8')
            audio = AudioManager(preferences_path=path)
            self.assertEqual(audio.music_volume, 0.3)
            self.assertEqual(audio.effects_volume, 0.65)

    def test_practice_completion_buttons_continue_or_leave_and_enter_still_skips(self):
        game = Game(preferences_path=None)
        game.action('training')
        game.world.tutorial.advance('complete')
        game.world.tutorial.age = 2
        game.frame(0, [], Vector2(), (240, 150))
        self.assertTrue({'continue', 'menu'}.issubset(game.renderer.buttons))
        game.action('continue')
        self.assertEqual(game.world.stage, 'arena')
        game.action('training')
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN), (240, 150))
        self.assertEqual(game.world.stage, 'arena')


class OverloadTests(unittest.TestCase):
    def test_cycles_vary_without_losing_area_or_pressure_windows(self):
        from neon.balance import overload_pattern

        self.assertEqual([overload_pattern(i) for i in range(4)], ['fan', 'area', 'radial', 'pressure'])
        self.assertEqual([overload_pattern(i) for i in range(4, 8)], ['radial', 'area', 'fan', 'pressure'])
        self.assertEqual([overload_pattern(i) for i in range(8, 12)], ['fan', 'area', 'radial', 'pressure'])

    def test_threshold_is_latched_once_and_death_does_not_trigger_it(self):
        boss = create_enemy(Vector2(300, 150), 'sentinel')
        boss.hp = boss.max_hp // 2 + 1
        boss.update(0.01, World().player)
        self.assertEqual(boss.phase, 1)
        boss.hit(1, Vector2(1, 0))
        self.assertEqual(boss.phase, 2)
        boss.phase_transition_left = 0.4
        boss.hit(1, Vector2(1, 0))
        self.assertEqual(boss.phase_transition_left, 0.4)
        dead = create_enemy(Vector2(300, 150), 'sentinel')
        dead.hit(dead.hp, Vector2(1, 0))
        self.assertEqual(dead.phase, 1)

    def test_every_pattern_is_announced_and_has_bounded_outputs(self):
        from neon.balance import OVERLOAD_ORDER

        for index, pattern in enumerate(OVERLOAD_ORDER):
            with self.subTest(pattern=pattern):
                world = World()
                boss = create_enemy(world.player.pos + Vector2(25 if pattern == 'pressure' else 100, 0), 'sentinel')
                boss.phase = 2
                boss.pattern_index = index
                boss.cooldown = 0
                boss.update(1 / 120, world.player)
                self.assertEqual(boss.attack_kind, pattern)
                self.assertGreater(boss.windup, 0.5)
                self.assertFalse(boss.shots)
                self.assertEqual(world.player.hp, 100)
                if pattern == 'area':
                    self.assertGreaterEqual(len(boss.zones), 1)
                    self.assertLessEqual(len(boss.zones), 2)
                for _ in range(150):
                    boss.update(1 / 120, world.player)
                    if boss.recovery > 0:
                        break
                self.assertGreater(boss.recovery, 0)
                self.assertEqual(len(boss.shots), {'fan': 5, 'radial': 9, 'area': 0, 'pressure': 0}[pattern])

    def test_area_warns_hits_once_and_can_be_escaped(self):
        from neon.boss_patterns import EnergyZone

        player = World().player
        area = EnergyZone(player.pos.copy(), 1.1)
        for _ in range(100):
            area.update(1 / 120, player)
        self.assertEqual(player.hp, 100)
        for _ in range(80):
            area.update(1 / 120, player)
            player.invulnerable = 0
        self.assertEqual(player.hp, 82)
        self.assertFalse(area.alive)
        player = World().player
        area = EnergyZone(player.pos.copy(), 1.1)
        player.dodge(Vector2(1, 0))
        for _ in range(160):
            player.update(1 / 120, Vector2())
            area.update(1 / 120, player)
        self.assertEqual(player.hp, 100)

    def test_fan_and_radial_patterns_leave_real_projectile_gaps(self):
        for pattern, gap_angle in (('fan', 9), ('radial', 0)):
            world = World()
            boss = create_enemy(Vector2(240, 155), 'sentinel')
            boss.phase = 2
            boss.attack_kind = pattern
            boss.locked_aim = Vector2(1, 0)
            boss.windup = 1 / 120
            boss.update(1 / 120, world.player)
            world.player.pos = boss.pos + Vector2(0, -18) + Vector2(100, 0).rotate(gap_angle) + Vector2(0, 10)
            for _ in range(140):
                for shot in boss.shots:
                    shot.update(1 / 120, world.player, world.player.pos)
            self.assertEqual(world.player.hp, 100, pattern)

    def test_world_announces_overload_once_and_clears_old_hazards(self):
        from neon.projectiles import Projectile
        from neon.boss_patterns import EnergyZone

        world = World()
        world.stage = 'arena'
        boss = create_enemy(Vector2(360, 150), 'sentinel')
        boss.hp = boss.max_hp // 2
        world.enemies = [boss]
        world.projectiles = [Projectile(Vector2(100, 100), Vector2(100, 0), 18, 5, 3)]
        world.areas = [EnergyZone(Vector2(100, 100), 1)]
        world.update(1 / 120, Vector2())
        self.assertFalse(world.projectiles)
        self.assertFalse(world.areas)
        boss.hit(1, Vector2(1, 0))
        world.update(1 / 120, Vector2())
        self.assertEqual(world.drain_audio_events().count('overload'), 1)

    def test_live_hazards_and_stun_prevent_new_patterns(self):
        boss = create_enemy(Vector2(350, 150), 'sentinel')
        boss.phase = 2
        boss.cooldown = 0
        boss.update(0.1, World().player, hazards_clear=False)
        self.assertEqual(boss.windup, 0)
        boss.stun = 0.2
        boss.update(0.1, World().player)
        self.assertEqual(boss.windup, 0)
        boss.stun = 0
        boss.update(0.01, World().player, shot_budget=0)
        self.assertEqual(boss.windup, 0)

    def test_killing_overloaded_boss_clears_areas_and_preserves_ending(self):
        from neon.boss_patterns import EnergyZone

        world = World()
        world.stage = 'arena'
        boss = create_enemy(world.player.pos + Vector2(30, 0), 'sentinel')
        boss.phase = 2
        boss.phase_announced = True
        boss.hp = 22
        world.enemies = [boss]
        world.areas = [EnergyZone(Vector2(100, 100), 1)]
        world.attack(Vector2(1, 0))
        for _ in range(40):
            world.update(1 / 120, Vector2())
            if world.stage == 'boss_dying':
                break
        self.assertEqual(world.stage, 'boss_dying')
        self.assertFalse(world.areas)
        self.assertFalse(world.projectiles)
        for _ in range(340):
            world.update(1 / 120, Vector2())
        self.assertEqual(world.stage, 'boss_dying')
        for _ in range(60):
            world.update(1 / 120, Vector2())
        self.assertEqual(world.stage, 'victory')

    def test_ranged_units_cannot_fire_in_same_world_step(self):
        world = World()
        world.stage = 'arena'
        for pos in (Vector2(100, 100), Vector2(380, 210)):
            enemy = create_enemy(pos, 'ranged')
            enemy.windup = 1 / 120
            enemy.locked_aim = Vector2(0, 1)
            world.enemies.append(enemy)
        world.update(1 / 120, Vector2())
        self.assertEqual(len(world.projectiles), 1)
        for _ in range(20):
            world.update(1 / 120, Vector2())
        self.assertEqual(world.enemies[1].windup, 1 / 120)


if __name__ == '__main__':
    unittest.main()
