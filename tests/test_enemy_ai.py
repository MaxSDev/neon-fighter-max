import unittest

from pygame import Vector2

from neon.combat import Player
from neon.enemies import create_enemy
from neon.projectiles import Projectile


class EnemyAITests(unittest.TestCase):
    def test_fast_attacks_are_shorter_and_more_frequent(self):
        counts = []
        for kind in ('drone', 'fast'):
            player = Player()
            enemy = create_enemy(player.pos + Vector2(15, 0), kind)
            attacks = 0
            for _ in range(1200):
                before = enemy.windup
                enemy.update(1 / 120, player)
                if before > 0 and enemy.windup == 0:
                    attacks += 1
                player.hp = 100
                player.invulnerable = 0
            counts.append(attacks)
        self.assertGreater(counts[1], counts[0])
        self.assertLess(create_enemy(Vector2(), 'fast').stats.windup, create_enemy(Vector2(), 'drone').stats.windup)

    def test_ranged_retreats_then_telegraphs_and_locks_shot_direction(self):
        player = Player()
        enemy = create_enemy(player.pos + Vector2(30, 0), 'ranged')
        before = enemy.pos.distance_to(player.pos)
        enemy.update(0.1, player)
        self.assertGreater(enemy.pos.distance_to(player.pos), before)
        enemy.cooldown = 0
        enemy.update(0.01, player)
        self.assertGreater(enemy.windup, 0)
        self.assertFalse(enemy.shots)
        direction = enemy.locked_aim.copy()
        player.pos.y += 50
        for _ in range(100):
            enemy.update(1 / 120, player)
            if enemy.shots:
                break
        self.assertEqual(len(enemy.shots), 1)
        self.assertLess(enemy.shots[0].velocity.normalize().distance_to(direction), 0.001)

    def test_projectile_sweeps_hits_once_and_is_consumed_during_dash(self):
        for dodge in (False, True):
            player = Player()
            if dodge:
                player.dodge(Vector2(0, 1))
            shot = Projectile(player.pos + Vector2(-50, -10), Vector2(1000, 0), 10, 3, 2)
            hurt = shot.update(0.1, player, player.pos)
            self.assertEqual(hurt, not dodge)
            self.assertEqual(player.hp, 100 if dodge else 90)
            self.assertFalse(shot.alive)
            self.assertFalse(shot.update(0.1, player, player.pos))

    def test_projectiles_expire_and_leave_valid_bounds(self):
        player = Player()
        shot = Projectile(Vector2(400, 100), Vector2(100, 0), 10, 3, 0.01)
        shot.update(0.02, player, player.pos)
        self.assertFalse(shot.alive)
        shot = Projectile(Vector2(450, 100), Vector2(100, 0), 10, 3, 2)
        shot.update(0.2, player, player.pos)
        self.assertFalse(shot.alive)

    def test_expired_projectile_cannot_hit_later_player_motion(self):
        player = Player()
        player.pos.update(240, 150)
        shot = Projectile(Vector2(240, 140), Vector2(), 10, 3, 0.01)
        shot.update(0.1, player, Vector2(200, 150))
        self.assertEqual(player.hp, 100)
        self.assertFalse(shot.alive)

    def test_sentinel_announces_energy_and_melee_and_recovers(self):
        player = Player()
        boss = create_enemy(player.pos + Vector2(100, 0), 'sentinel')
        boss.cooldown = 0
        boss.update(0.01, player)
        self.assertEqual(boss.attack_kind, 'energy')
        self.assertGreater(boss.windup, 0)
        for _ in range(130):
            boss.update(1 / 120, player)
            if boss.shots:
                break
        self.assertEqual(len(boss.shots), 3)
        self.assertGreater(boss.recovery, 0)
        boss = create_enemy(player.pos + Vector2(25, 0), 'sentinel')
        boss.cooldown = 0
        boss.update(0.01, player)
        self.assertEqual(boss.attack_kind, 'melee')
        self.assertEqual(player.hp, 100)
        for _ in range(100):
            boss.update(1 / 120, player)
            if player.hp < 100:
                break
        self.assertEqual(player.hp, 76)

    def test_sentinel_melee_can_be_dodged_after_warning(self):
        player = Player()
        boss = create_enemy(player.pos + Vector2(25, 0), 'sentinel')
        boss.cooldown = 0
        boss.update(0.01, player)
        for _ in range(60):
            boss.update(1 / 120, player)
        self.assertEqual(player.hp, 100)
        player.dodge(Vector2(-1, 0))
        for _ in range(22):
            player.update(1 / 120, Vector2())
            boss.update(1 / 120, player)
        self.assertEqual(player.hp, 100)
        self.assertGreater(boss.recovery, 0)


if __name__ == '__main__':
    unittest.main()
