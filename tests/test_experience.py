"""Interactive tutorial and delayed ending acceptance checks."""

import unittest

from pygame import Vector2

from neon.world import World
from neon.balance import BOSS_DESTRUCTION_TIME, PLAYER_DEFEAT_TIME


class ExperienceTests(unittest.TestCase):
    def test_boss_death_locks_combat_and_waits_for_full_sequence(self):
        from neon.enemies import create_enemy

        world = World(seed=4)
        world.stage = 'arena'
        boss = create_enemy(Vector2(300, 150), 'sentinel')
        boss.hp = 0
        world.enemies = [boss]
        world.update(1 / 120, Vector2())
        self.assertEqual(world.stage, 'boss_dying')
        position = world.player.pos.copy()
        for _ in range(round((BOSS_DESTRUCTION_TIME - 0.1) * 120)):
            world.attack(Vector2(1, 0))
            world.update(1 / 120, Vector2(1, 0))
        self.assertEqual(world.stage, 'boss_dying')
        self.assertEqual(world.player.pos, position)
        for _ in range(30):
            world.update(1 / 120, Vector2())
        self.assertEqual(world.stage, 'victory')
        events = world.drain_audio_events()
        self.assertEqual(events.count('boss_destroy'), 1)
        self.assertEqual(events.count('victory'), 1)

    def test_player_death_is_delayed(self):
        world = World()
        world.start()
        world.skip_tutorial()
        world.player.hp = 0
        world.update(0.01, Vector2())
        self.assertEqual(world.stage, 'player_dying')
        for _ in range(round((PLAYER_DEFEAT_TIME - 0.1) * 120)):
            world.update(1 / 120, Vector2())
        self.assertEqual(world.stage, 'player_dying')
        for _ in range(30):
            world.update(1 / 120, Vector2())
        self.assertEqual(world.stage, 'defeat')

    def test_tutorial_requires_movement_contact_combo_and_dodge(self):
        world = World(seed=4)
        world.start()
        self.assertEqual(world.tutorial.step, 'movement')
        for _ in range(100):
            world.update(1 / 120, Vector2(1, 0))
        self.assertEqual(world.tutorial.step, 'attack')
        dummy = world.enemies[0]

        def hit():
            dummy.pos = world.player.pos + Vector2(26, 0)
            world.attack(Vector2(1, 0))
            for _ in range(48):
                world.update(1 / 120, Vector2())

        hit()
        self.assertEqual(world.tutorial.step, 'combo')
        for _ in range(4):
            hit()
        for _ in range(120):
            world.update(1 / 120, Vector2())
        self.assertEqual(world.tutorial.step, 'dodge')
        world.dodge(Vector2(0, 1))
        for _ in range(130):
            world.update(1 / 120, Vector2())
        world.dodge(Vector2(0, -1))
        for _ in range(500):
            world.update(1 / 120, Vector2())
            if world.stage == 'arena':
                break
        self.assertEqual(world.stage, 'arena')
        self.assertEqual(world.player.hp, 100)
        self.assertFalse(world.projectiles)

    def test_real_projectile_evasion_completes_dodge_objective_without_damage(self):
        from neon.projectiles import Projectile

        world = World()
        world.start()
        world.tutorial.advance('dodge')
        world.dodge(Vector2(0, 1))
        world.projectiles.append(Projectile(world.player.pos + Vector2(-5, -10), Vector2(75, 0),
                                             0, 5, 4, training=True))
        world.update(1 / 120, Vector2())
        self.assertTrue(world.tutorial.evaded)
        self.assertEqual(world.tutorial.step, 'complete')
        self.assertEqual(world.player.hp, 100)

    def test_swing_and_contact_events_do_not_repeat_during_hitstop(self):
        world = World()
        world.start()
        world.tutorial.step = 'combo'
        world.enemies[0].pos = world.player.pos + Vector2(26, 0)
        world.attack(Vector2(1, 0))
        for _ in range(50):
            world.update(1 / 120, Vector2())
        events = world.drain_audio_events()
        self.assertEqual(events.count('swing'), 1)
        self.assertEqual(events.count('hit'), 1)
        self.assertEqual(events.count('enemy_hurt'), 1)
        self.assertFalse(world.drain_audio_events())

    def test_real_killing_swing_preserves_impact_and_starts_one_boss_sequence(self):
        from neon.enemies import create_enemy
        from neon.projectiles import Projectile

        world = World()
        world.stage = 'arena'
        boss = create_enemy(world.player.pos + Vector2(30, 0), 'sentinel')
        boss.hp = 22
        world.enemies = [boss]
        world.projectiles = [Projectile(Vector2(100, 100), Vector2(100, 0), 18, 5, 3)]
        world.attack(Vector2(1, 0))
        for _ in range(40):
            world.update(1 / 120, Vector2())
            if world.stage == 'boss_dying':
                break
        self.assertEqual(world.stage, 'boss_dying')
        self.assertTrue(world.impacts)
        self.assertFalse(world.projectiles)
        attack_left = world.player.attack_left
        world.update(1 / 120, Vector2())
        self.assertEqual(world.player.attack_left, attack_left)
        self.assertEqual(world.drain_audio_events().count('boss_destroy'), 1)


if __name__ == '__main__':
    unittest.main()
