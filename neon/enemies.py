"""Enemy creation and specialized AI. Basic melee remains in combat.py."""

from dataclasses import dataclass, field

from pygame import Vector2

from neon.balance import (ENEMIES, RANGED_NEAR, RANGED_FAR, BOSS_ENERGY_WINDUP,
                          BOSS_ENERGY_COOLDOWN, BOSS_ENERGY_DAMAGE, BOSS_RECOVERY,
                          OVERLOAD_THRESHOLD, OVERLOAD_TRANSITION, OVERLOAD_NOTICE_TIME,
                          OVERLOAD_PATTERNS, overload_pattern, OVERLOAD_SPEED_MULTIPLIER, MAX_PROJECTILES)
from neon.combat import Enemy
from neon.projectiles import Projectile
from neon.settings import clamp_position
from neon.boss_patterns import projectile_angles, prepare_zones


@dataclass(eq=False)
class RangedEnemy(Enemy):
    locked_aim: Vector2 = field(default_factory=lambda: Vector2(1, 0))
    attack_kind: str = 'energy'

    def update(self, dt, player, can_fire=True):
        if self.advance_reaction(dt):
            return False
        delta = player.pos - self.pos
        distance = delta.length()
        direction = delta.normalize() if distance else self.facing
        if self.windup > 0:
            if self.windup <= dt and not can_fire:
                return False
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
    phase: int = 1
    phase_announced: bool = False
    phase_transition_left: float = 0
    phase_notice: float = 0
    pattern_index: int = 0
    pressure_hits: int = 0
    zones: list = field(default_factory=list)

    def check_phase(self):
        if self.phase == 1 and 0 < self.hp <= self.max_hp * OVERLOAD_THRESHOLD:
            self.phase = 2
            self.phase_transition_left = OVERLOAD_TRANSITION
            self.phase_notice = OVERLOAD_NOTICE_TIME
            self.windup = self.recovery = self.cooldown = 0
            self.attack_kind = 'overload'
            self.shots.clear()
            self.zones.clear()
            return True
        return False

    def hit(self, damage, direction, finisher=False):
        super().hit(damage, direction, finisher)
        if self.hp == 0:
            self.windup = 0
            self.shots.clear()
            self.zones.clear()
        else:
            self.check_phase()

    @property
    def windup_duration(self):
        if self.phase == 2 and self.attack_kind in OVERLOAD_PATTERNS:
            return OVERLOAD_PATTERNS[self.attack_kind].windup
        return BOSS_ENERGY_WINDUP if self.attack_kind == 'energy' else self.stats.windup

    def update(self, dt, player, hazards_clear=True, shot_budget=MAX_PROJECTILES):
        if self.hp <= 0:
            return False
        self.check_phase()
        self.phase_notice = max(0, self.phase_notice - dt)
        if self.phase_transition_left > 0:
            self.advance_reaction(dt)
            self.phase_transition_left = max(0, self.phase_transition_left - dt)
            return False
        if self.advance_reaction(dt):
            return False
        delta = player.pos - self.pos
        distance = delta.length()
        direction = delta.normalize() if distance else self.facing
        if self.windup > 0:
            angles = projectile_angles(self.attack_kind)
            if self.windup <= dt and len(angles) > shot_budget:
                return False
            self.windup = max(0, self.windup - dt)
            if self.windup == 0:
                self.attack_count += 1
                pattern = OVERLOAD_PATTERNS.get(self.attack_kind) if self.phase == 2 else None
                self.recovery = pattern.recovery if pattern else BOSS_RECOVERY
                self.cooldown = pattern.cooldown if pattern else (BOSS_ENERGY_COOLDOWN if angles else self.stats.cooldown)
                if self.phase == 2:
                    if self.attack_kind == 'pressure':
                        self.pressure_hits += 1
                        if self.pressure_hits >= 2:
                            self.pattern_index += 1
                            self.pressure_hits = 0
                    else:
                        self.pattern_index += 1
                if angles:
                    for angle in angles:
                        shot_direction = self.locked_aim.rotate(angle)
                        muzzle = self.pos + Vector2(0, -18) + shot_direction * 20
                        self.shots.append(Projectile.launch(muzzle, shot_direction, BOSS_ENERGY_DAMAGE, 'sentinel'))
                elif self.attack_kind != 'area':
                    return distance <= self.stats.reach and player.hurt(self.stats.damage)
        elif self.recovery > 0:
            self.recovery = max(0, self.recovery - dt)
        elif self.phase == 2:
            chosen = overload_pattern(self.pattern_index)
            ready = self.cooldown == 0 and hazards_clear and len(projectile_angles(chosen)) <= shot_budget
            if ready and (chosen != 'pressure' or distance <= self.stats.trigger):
                self.attack_kind = chosen
                self.locked_aim = direction.copy()
                self.facing = direction.copy()
                self.windup = self.windup_duration
                if chosen == 'area':
                    self.zones.extend(prepare_zones(player.pos, direction, self.windup))
            elif distance > self.stats.trigger - 5:
                self.pos += direction * min(self.speed * OVERLOAD_SPEED_MULTIPLIER * dt, distance - self.stats.trigger + 5)
                clamp_position(self.pos, self.radius)
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
