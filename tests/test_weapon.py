"""Regression coverage for visible sword geometry and contact-only feedback."""

import math
import unittest

from pygame import Vector2

from neon.combat import Player
from neon.world import World
from neon.weapon import sword_pose, sword_contact


class WeaponTests(unittest.TestCase):
    def test_hand_anchor_is_shared_by_idle_and_all_attack_phases(self):
        player = Player()
        idle = sword_pose(player)
        player.attack(Vector2(1, 0))
        for elapsed in (0, 0.03, 0.1, 0.2, 0.259):
            pose = sword_pose(player, elapsed)
            self.assertEqual(pose.hand, idle.hand)
            self.assertLessEqual(abs(pose.angle), math.pi)

    def test_attack_returns_continuously_to_rest(self):
        for combo in range(1, 5):
            player = Player()
            idle = sword_pose(player)
            player.combo = combo - 1
            player.combo_window = 1
            player.attack(Vector2(1, 0))
            end = sword_pose(player, player.attack_duration)
            self.assertAlmostEqual(end.angle, idle.angle)
            self.assertEqual(end.hand, idle.hand)
            self.assertLess(end.tip.distance_to(idle.tip), 0.0001)

    def test_windup_cannot_damage_even_when_blade_overlaps_target(self):
        player = Player()
        player.attack(Vector2(1, 0))
        player.update(0.02, Vector2())
        pose = sword_pose(player)
        self.assertEqual(pose.phase, 'windup')
        self.assertIsNone(sword_contact(player, pose.tip, 5))

    def test_collision_follows_swept_blade_not_whole_attack_sector(self):
        player = Player()
        player.attack(Vector2(1, 0))
        player.update(0.09, Vector2())
        pose = sword_pose(player)
        self.assertEqual(pose.phase, 'strike')
        center = pose.hand + (pose.tip - pose.hand) * 0.75
        self.assertIsNotNone(sword_contact(player, center, 4))
        self.assertIsNone(sword_contact(player, pose.hand + Vector2(0, 35), 4))

    def test_finisher_miss_has_no_impact_sparks_hitstop_or_shake(self):
        world = World(seed=9)
        world.start()
        world.tutorial.step = 'combo'
        world.enemies[0].pos = Vector2(420, 220)
        world.player.combo = 3
        world.player.combo_window = 1
        world.attack(Vector2(1, 0))
        world.update(0.2, Vector2())
        self.assertEqual(world.impact, 0)
        self.assertEqual(world.hitstop, 0)
        self.assertEqual(world.shake, 0)
        self.assertFalse(world.impacts)
        self.assertFalse(world.particles)

    def test_finisher_contact_stores_world_contact_and_expires(self):
        world = World(seed=9)
        world.start()
        world.tutorial.step = 'combo'
        enemy = world.enemies[0]
        enemy.pos = world.player.pos + Vector2(30, 0)
        world.player.combo = 3
        world.player.combo_window = 1
        world.attack(Vector2(1, 0))
        for _ in range(30):
            world.update(1 / 120, Vector2())
            if world.impacts:
                break
        self.assertTrue(world.impacts)
        contact = world.impacts[0]
        self.assertTrue(contact.finisher)
        self.assertLess(contact.pos.distance_to(enemy.pos + Vector2(0, -10)), 12)
        self.assertGreater(world.impact, 0)
        self.assertGreater(world.hitstop, 0)
        self.assertLessEqual(world.shake, 2.8)
        for _ in range(60):
            world.update(1 / 120, Vector2())
        self.assertFalse(world.impacts)
        self.assertEqual(world.impact, 0)
        self.assertEqual(world.shake, 0)

    def test_attacks_hit_in_all_mouse_directions_at_multiple_frame_rates(self):
        for fps in (30, 60, 120):
            for direction in (Vector2(1, 0), Vector2(-1, 0), Vector2(0, -1), Vector2(0, 1)):
                with self.subTest(fps=fps, direction=direction):
                    world = World(seed=9)
                    world.start()
                    world.tutorial.step = 'combo'
                    target = world.enemies[0]
                    target.pos = world.player.pos + direction * 30
                    world.attack(direction)
                    for _ in range(fps // 2):
                        world.update(1 / fps, Vector2())
                    self.assertEqual(target.hp, 977)
                    self.assertEqual(world.tutorial_hits, 1)

    def test_moving_sword_trail_retains_real_previous_hand_positions(self):
        player = Player()
        player.attack(Vector2(1, 0))
        for _ in range(16):
            player.update(1 / 120, Vector2(1, 0))
        self.assertGreater(len(player.sword_trail), 1)
        first_hand = player.sword_trail[0][1].hand
        self.assertLess(first_hand.x, sword_pose(player).hand.x)
        for _ in range(30):
            player.update(1 / 120, Vector2())
        self.assertFalse(player.sword_trail)

    def test_skip_tutorial_clears_feedback_before_next_arena(self):
        world = World(seed=9)
        world.start()
        world.tutorial.step = 'combo'
        world.tutorial_hits = 3
        world.enemies[0].pos = world.player.pos + Vector2(30, 0)
        world.player.combo = 3
        world.player.combo_window = 1
        world.attack(Vector2(1, 0))
        for _ in range(30):
            world.update(1 / 120, Vector2())
            if world.impacts:
                break
        self.assertTrue(world.impacts)
        world.skip_tutorial()
        self.assertEqual(world.stage, 'arena')
        self.assertEqual(world.impact, 0)
        self.assertEqual(world.shake, 0)
        self.assertFalse(world.impacts)
        self.assertFalse(world.particles)

    def test_terminal_screen_feedback_decays_without_moving_actors(self):
        world = World(seed=9)
        world.start()
        world.tutorial.step = 'combo'
        world.enemies[0].pos = world.player.pos + Vector2(30, 0)
        world.player.combo = 3
        world.player.combo_window = 1
        world.attack(Vector2(1, 0))
        for _ in range(30):
            world.update(1 / 120, Vector2())
            if world.impacts:
                break
        self.assertTrue(world.impacts)
        world.stage = 'victory'
        before = world.player.pos.copy()
        for _ in range(60):
            world.update(1 / 60, Vector2(1, 0))
        self.assertEqual(world.player.pos, before)
        self.assertEqual(world.shake, 0)
        self.assertEqual(world.impact, 0)
        self.assertFalse(world.impacts)
        self.assertFalse(world.particles)
        self.assertFalse(world.player.sword_trail)


if __name__ == '__main__':
    unittest.main()
