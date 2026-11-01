"""Enemy creation and specialized AI. Basic melee remains in combat.py."""

from dataclasses import dataclass, field

from pygame import Vector2

from neon.balance import (ENEMIES, RANGED_NEAR, RANGED_FAR, BOSS_ENERGY_WINDUP,
                          BOSS_ENERGY_COOLDOWN, BOSS_ENERGY_DAMAGE, BOSS_ENERGY_SPREAD, BOSS_RECOVERY)
from neon.combat import Enemy
from neon.projectiles import Projectile
from neon.settings import clamp_position


@dataclass(eq=False)
class RangedEnemy(Enemy):
    locked_aim: Vector2 = field(default_factory=lambda: Vector2(1, 0))
    attack_kind: str = 'energy'

    def update(self, dt, player):
        if self.advance_reaction(dt):
            return False
        delta = player.pos - self.pos
        distance = delta.length()
        direction = delta.normalize() if distance else self.facing
        if self.windup > 0:
            self.windup = max(0, self.windup - dt)
            if self.windup == 0:
                muzzle = self.pos + Vector2(0, -10) + self.locked_aim * 12
                self.shots.append(Projectile.launch(muzzle, self.locked_aim, self.stats.damage, 'ranged'))
                self.cooldown = self.stats.cooldown
        elif self.cooldown == 0 and distance < 240:
            self.locked_aim = direction.copy()
            self.facing = direction.copy()
            self.windup = self.stats.windup
        else:
            self.facing = direction.copy()
            if distance < RANGED_NEAR:
                self.pos -= direction * self.speed * dt
            elif distance > RANGED_FAR:
                self.pos += direction * self.speed * dt
            clamp_position(self.pos, self.radius)
        return False


@dataclass(eq=False)
class Sentinel(Enemy):
    locked_aim: Vector2 = field(default_factory=lambda: Vector2(1, 0))
    attack_kind: str = 'melee'
    recovery: float = 0
    attack_count: int = 0

    @property
    def windup_duration(self):
        return BOSS_ENERGY_WINDUP if self.attack_kind == 'energy' else self.stats.windup

    def update(self, dt, player):
        if self.advance_reaction(dt):
            return False
        delta = player.pos - self.pos
        distance = delta.length()
        direction = delta.normalize() if distance else self.facing
        if self.windup > 0:
            self.windup = max(0, self.windup - dt)
            if self.windup == 0:
                self.attack_count += 1
                self.recovery = BOSS_RECOVERY
                if self.attack_kind == 'energy':
                    for angle in BOSS_ENERGY_SPREAD:
                        shot_direction = self.locked_aim.rotate(angle)
                        muzzle = self.pos + Vector2(0, -18) + shot_direction * 20
                        self.shots.append(Projectile.launch(muzzle, shot_direction, BOSS_ENERGY_DAMAGE, 'sentinel'))
                    self.cooldown = BOSS_ENERGY_COOLDOWN
                else:
                    self.cooldown = self.stats.cooldown
                    return distance <= self.stats.reach and player.hurt(self.stats.damage)
        elif self.recovery > 0:
            self.recovery = max(0, self.recovery - dt)
        elif self.cooldown == 0 and (distance <= self.stats.trigger or self.attack_count % 2 == 1 or distance > 90):
            self.attack_kind = 'energy' if self.attack_count % 2 == 1 or distance > 90 else 'melee'
            self.locked_aim = direction.copy()
            self.facing = direction.copy()
            self.windup = self.windup_duration
        else:
            self.facing = direction.copy()
            if distance > self.stats.trigger - 5:
                self.pos += direction * min(self.speed * dt, distance - self.stats.trigger + 5)
                clamp_position(self.pos, self.radius)
        return False


def create_enemy(pos, kind):
    stats = ENEMIES[kind]
    enemy_class = {'ranged': RangedEnemy, 'sentinel': Sentinel}.get(kind, Enemy)
    return enemy_class(pos.copy(), kind, stats.hp, stats.hp, stats.speed)
