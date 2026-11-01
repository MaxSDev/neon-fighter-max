"""Iteration three: staggered progression and safe spawn contracts."""

import unittest
from collections import Counter

from pygame import Vector2

from neon.balance import WAVES, MAX_ACTIVE_ENEMIES
from neon.world import World


class ProgressionTests(unittest.TestCase):
    def test_wave_compositions_match_design(self):
        self.assertEqual([Counter(wave) for wave in WAVES], [
            Counter(drone=5), Counter(drone=5, ranged=2), Counter(drone=5, fast=3, ranged=2)])

    def test_spawn_is_announced_staggered_safe_and_capped(self):
        world = World(seed=11)
        world.start()
        world.skip_tutorial()
        world.spawn_wave()
        self.assertFalse(world.enemies)
        for _ in range(1200):
            world.update(1 / 120, Vector2())
            self.assertLessEqual(len(world.enemies), MAX_ACTIVE_ENEMIES)
            if len(world.enemies) == MAX_ACTIVE_ENEMIES:
                break
        self.assertTrue(world.enemies)
        self.assertTrue(world.spawn_history)
        for _, kind, pos in world.spawn_history:
            self.assertTrue(world.spawn_bounds_valid(pos, kind))
            self.assertGreaterEqual(pos.distance_to(world.player.pos), 95)
        times = [time for time, _, _ in world.spawn_history]
        self.assertTrue(all(b - a >= 0.6 for a, b in zip(times, times[1:])))

    def test_wave_waits_for_queue_and_victory_waits_for_boss_destruction(self):
        world = World(seed=11)
        world.start()
        world.skip_tutorial()
        for _ in range(24000):
            for enemy in world.enemies:
                enemy.hp = 0
            world.update(1 / 120, Vector2())
            if world.boss_defeated:
                break
        self.assertTrue(world.boss_defeated)
        self.assertEqual(world.stage, 'boss_dying')
        self.assertGreater(world.boss_destruction, 0)
        self.assertEqual(Counter(kind for _, kind, _ in world.spawn_history), Counter(drone=15, fast=3, ranged=4, sentinel=1))
        for _ in range(420):
            world.update(1 / 120, Vector2())
        self.assertEqual(world.stage, 'victory')

    def test_player_entering_warning_prevents_unsafe_spawn(self):
        world = World(seed=11)
        world.start()
        world.skip_tutorial()
        world.spawn_wave()
        world.update(1 / 120, Vector2())
        self.assertIsNotNone(world.pending_spawn)
        position = world.pending_spawn.pos.copy()
        world.player.pos = position.copy()
        for _ in range(88):
            world.update(1 / 120, Vector2())
        self.assertFalse(world.enemies)
        self.assertEqual(len(world.spawn_queue), 5)
        self.assertFalse(world.spawn_history)

    def test_pause_freezes_spawn_warning_and_projectiles(self):
        from neon.projectiles import Projectile

        world = World(seed=11)
        world.start()
        world.skip_tutorial()
        world.spawn_wave()
        world.update(1 / 120, Vector2())
        shot = Projectile(Vector2(100, 100), Vector2(100, 0), 10, 3, 2)
        world.projectiles.append(shot)
        warning = world.pending_spawn.left
        world.toggle_pause()
        world.update(0.25, Vector2())
        self.assertEqual(world.pending_spawn.left, warning)
        self.assertEqual(shot.life, 2)
        self.assertEqual(shot.pos, Vector2(100, 100))


if __name__ == '__main__':
    unittest.main()
