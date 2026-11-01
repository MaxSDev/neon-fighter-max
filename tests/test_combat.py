import unittest

from pygame import Vector2

from neon.combat import Enemy, Player
from neon.weapon import sword_contact


class CombatTests(unittest.TestCase):
    def test_diagonal_movement_has_same_speed(self):
        straight, diagonal = Player(), Player()
        start = straight.pos.copy()
        straight.update(0.1, Vector2(1, 0))
        diagonal.update(0.1, Vector2(1, 1))
        self.assertAlmostEqual(straight.pos.distance_to(start), diagonal.pos.distance_to(start))

    def test_sword_rejects_targets_behind_and_out_of_range(self):
        player = Player()
        player.attack(Vector2(1, 0))
        player.update(0.13, Vector2())
        self.assertIsNotNone(sword_contact(player, player.pos + Vector2(32, -10), 7))
        self.assertIsNone(sword_contact(player, player.pos + Vector2(-32, -10), 7))
        self.assertIsNone(sword_contact(player, player.pos + Vector2(80, -10), 7))

    def test_combo_advances_to_finisher_then_wraps(self):
        player = Player()
        for expected in (1, 2, 3, 4, 1):
            self.assertTrue(player.attack(Vector2(1, 0)))
            self.assertEqual(player.combo, expected)
            player.update(0.34, Vector2())

    def test_combo_expires(self):
        player = Player()
        player.attack(Vector2(1, 0))
        player.update(1.2, Vector2())
        player.attack(Vector2(1, 0))
        self.assertEqual(player.combo, 1)

    def test_damage_grants_invulnerability(self):
        player = Player()
        self.assertTrue(player.hurt(12))
        self.assertFalse(player.hurt(12))
        self.assertEqual(player.hp, 88)
        player.update(1, Vector2())
        self.assertTrue(player.hurt(12))

    def test_dodge_is_invulnerable_and_has_cooldown(self):
        player = Player()
        self.assertTrue(player.dodge(Vector2(1, 0)))
        self.assertFalse(player.hurt(12))
        self.assertFalse(player.dodge(Vector2(1, 0)))
        player.update(1, Vector2())
        self.assertTrue(player.dodge(Vector2(1, 0)))

    def test_enemy_chases_and_telegraphs_attack(self):
        player = Player()
        enemy = Enemy(Vector2(100, 140))
        before = enemy.pos.distance_to(player.pos)
        enemy.update(0.1, player)
        self.assertLess(enemy.pos.distance_to(player.pos), before)
        enemy.pos = player.pos + Vector2(10, 0)
        enemy.update(0.7, player)
        self.assertGreater(enemy.windup, 0)
        self.assertEqual(player.hp, 100)
        enemy.update(0.5, player)
        self.assertEqual(player.hp, 88)


if __name__ == '__main__':
    unittest.main()
