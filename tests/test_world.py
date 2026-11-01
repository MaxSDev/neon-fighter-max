import unittest

from pygame import Vector2

from neon.world import World


class WorldTests(unittest.TestCase):
    def test_connected_combo_confirms_before_dodge_training(self):
        world = World()
        world.start()
        world.tutorial.step = 'combo'
        self.assertEqual(world.stage, 'tutorial')
        dummy = world.enemies[0]
        for index in range(4):
            dummy.pos = world.player.pos + Vector2(26, 0)
            dummy.velocity.update(0, 0)
            world.attack(Vector2(1, 0))
            for _ in range(24):
                world.update(1 / 120, Vector2())
                if world.tutorial_hits == index + 1:
                    break
            self.assertEqual(world.tutorial_hits, index + 1)
            world.update(0.3, Vector2())
            world.update(0.05, Vector2())
        self.assertEqual(world.stage, 'tutorial')
        self.assertGreater(world.tutorial.confirmation, 0)
        for _ in range(120):
            world.update(1 / 120, Vector2())
        self.assertEqual(world.tutorial.step, 'dodge')

    def test_each_enemy_is_hit_once_per_swing(self):
        world = World()
        world.start()
        world.tutorial.step = 'combo'
        dummy = world.enemies[0]
        dummy.pos = world.player.pos + Vector2(26, 0)
        world.attack(Vector2(1, 0))
        world.update(0.2, Vector2())
        hp = dummy.hp
        self.assertEqual(hp, 977)
        world.update(0.06, Vector2())
        world.update(0.06, Vector2())
        self.assertEqual(dummy.hp, hp)

    def test_skip_staggered_wave_and_restart_clears_progress(self):
        world = World()
        world.start()
        world.tutorial.step = 'combo'
        world.skip_tutorial()
        for _ in range(200):
            world.update(1 / 60, Vector2())
        self.assertEqual(world.wave, 1)
        self.assertTrue(world.enemies)
        self.assertTrue(world.spawn_queue)
        world.start()
        world.tutorial.step = 'combo'
        self.assertEqual(world.stage, 'tutorial')
        self.assertEqual(world.player.hp, 100)
        self.assertEqual(world.wave, 0)
        self.assertFalse(world.spawn_queue)
        self.assertIsNone(world.pending_spawn)
        self.assertFalse(world.projectiles)
        self.assertFalse(world.boss_spawned)

    def test_pause_freezes_simulation_and_defeat_is_terminal(self):
        world = World()
        world.start()
        world.tutorial.step = 'combo'
        world.toggle_pause()
        before = world.player.pos.copy()
        world.update(0.5, Vector2(1, 0))
        self.assertEqual(world.player.pos, before)
        world.toggle_pause()
        world.player.hp = 0
        world.update(0.01, Vector2())
        self.assertEqual(world.stage, 'player_dying')
        for _ in range(240):
            world.update(1 / 120, Vector2(1, 0))
        self.assertEqual(world.stage, 'defeat')
        world.update(0.5, Vector2(1, 0))
        self.assertEqual(world.player.pos, before)

    def test_combat_remains_consistent_at_different_frame_rates(self):
        results = []
        for fps in (30, 60, 120):
            world = World(seed=7)
            world.start()
            world.tutorial.step = 'combo'
            world.enemies[0].pos = world.player.pos + Vector2(28, 0)
            world.attack(Vector2(1, 0))
            for _ in range(fps // 2):
                world.update(1 / fps, Vector2())
            results.append((world.tutorial_hits, world.enemies[0].hp))
        self.assertEqual(results, [(1, 977)] * 3)

    def test_full_run_wins_using_real_damage_and_normal_player_stats(self):
        world = World(seed=11)
        world.start()
        world.tutorial.step = 'combo'
        world.skip_tutorial()
        for _ in range(18000):
            movement = Vector2()
            aim = world.player.facing
            if world.enemies:
                target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(world.player.pos))
                aim = target.pos - world.player.pos
                distance = aim.length()
                direction = aim.normalize() if distance else Vector2(1, 0)
                if distance > 32:
                    movement = direction
                elif distance < 25:
                    movement = -direction
                if distance < 47 and world.player.attack_left == 0:
                    world.attack(aim)
                if any(e.windup > 0 and e.pos.distance_to(world.player.pos) < 36 for e in world.enemies):
                    world.dodge(-direction)
            world.update(1 / 60, movement, aim)
            if world.stage in ('victory', 'defeat'):
                break
        self.assertEqual(world.stage, 'victory')
        self.assertEqual(world.kills, 23)
        self.assertTrue(world.boss_defeated)
        self.assertEqual(world.tutorial_hits, 0)

    def test_enemy_attacks_can_cause_defeat_without_injected_damage(self):
        world = World(seed=11)
        world.start()
        world.tutorial.step = 'combo'
        world.skip_tutorial()
        for _ in range(3600):
            world.update(1 / 60, Vector2())
            if world.stage == 'defeat':
                break
        self.assertEqual(world.stage, 'defeat')
        self.assertEqual(world.player.hp, 0)

    def test_early_input_buffers_one_followup_attack(self):
        world = World()
        world.start()
        world.tutorial.step = 'combo'
        world.attack(Vector2(1, 0))
        world.update(0.15, Vector2())
        world.attack(Vector2(1, 0))
        world.update(0.15, Vector2())
        self.assertEqual(world.player.combo, 2)
        self.assertGreater(world.player.attack_left, 0)

    def test_finisher_has_extended_reach_and_stronger_damage(self):
        world = World()
        world.start()
        world.tutorial.step = 'combo'
        enemy = world.enemies[0]
        enemy.pos = world.player.pos + Vector2(60, 0)
        world.attack(Vector2(1, 0))
        world.update(0.25, Vector2())
        world.update(0.1, Vector2())
        self.assertEqual(enemy.hp, 999)
        world.player.combo = 3
        world.player.combo_window = 1
        world.attack(Vector2(1, 0))
        for _ in range(30):
            world.update(1 / 120, Vector2())
            if world.impact > 0:
                break
        self.assertEqual(enemy.hp, 953)
        self.assertGreater(world.impact, 0)


if __name__ == '__main__':
    unittest.main()
