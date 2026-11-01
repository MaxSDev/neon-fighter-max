"""Frame-independent actors and combat geometry, independent of rendering."""

from dataclasses import dataclass, field
import math

from pygame import Vector2

from neon.settings import clamp_position
from neon.weapon import attack_timing, sword_pose


@dataclass
class Player:
    pos: Vector2 = field(default_factory=lambda: Vector2(240, 158))
    facing: Vector2 = field(default_factory=lambda: Vector2(1, 0))
    hp: int = 100
    combo: int = 0
    combo_window: float = 0
    attack_left: float = 0
    attack_duration: float = 0.26
    invulnerable: float = 0
    dash_left: float = 0
    dash_cooldown: float = 0
    dash_direction: Vector2 = field(default_factory=Vector2)
    walk_time: float = 0
    moving: bool = False
    hit_ids: set = field(default_factory=set)
    previous_attack_elapsed: float = 0
    previous_pos: Vector2 = field(default_factory=Vector2)
    sword_trail: list = field(default_factory=list)
    trail_clock: float = 0

    @property
    def strike_active(self):
        elapsed = self.attack_duration - self.attack_left
        windup, strike, _ = attack_timing(self.combo == 4)
        return self.attack_left > 0 and elapsed >= windup and self.previous_attack_elapsed <= windup + strike

    def attack(self, aim):
        if self.attack_left > 0 or self.dash_left > 0 or self.hp <= 0:
            return False
        if aim.length_squared():
            self.facing = aim.normalize()
        self.combo = self.combo % 4 + 1 if self.combo_window > 0 else 1
        self.attack_duration = sum(attack_timing(self.combo == 4))
        self.attack_left = self.attack_duration
        self.combo_window = 0.85
        self.hit_ids.clear()
        self.previous_attack_elapsed = 0
        self.previous_pos = self.pos.copy()
        self.sword_trail.clear()
        return True

    def dodge(self, direction):
        if self.dash_cooldown > 0 or self.hp <= 0:
            return False
        self.dash_direction = direction.normalize() if direction.length_squared() else self.facing.copy()
        self.dash_left = 0.16
        self.dash_cooldown = 0.8
        self.invulnerable = max(self.invulnerable, 0.23)
        self.attack_left = 0
        self.sword_trail.clear()
        return True

    def hurt(self, amount):
        if self.invulnerable > 0 or self.hp <= 0:
            return False
        self.hp = max(0, self.hp - amount)
        self.invulnerable = 0.85
        return True

    def update(self, dt, movement):
        self.previous_pos = self.pos.copy()
        self.previous_attack_elapsed = self.attack_duration - self.attack_left if self.attack_left > 0 else 0
        dash_dt = min(dt, self.dash_left)
        if dash_dt > 0:
            self.pos += self.dash_direction * 330 * dash_dt
        direction = movement.normalize() if movement.length_squared() else Vector2()
        self.moving = bool(direction.length_squared())
        speed = 64 if self.attack_left > 0 else 105
        self.pos += direction * speed * (dt - dash_dt)
        self.walk_time += dt * (12 if self.moving else 3)
        for attr in ('attack_left', 'combo_window', 'invulnerable', 'dash_left', 'dash_cooldown'):
            setattr(self, attr, max(0, getattr(self, attr) - dt))
        if self.combo_window == 0:
            self.combo = 0
        clamp_position(self.pos)
        self.trail_clock += dt
        self.sword_trail = [(stamp, pose) for stamp, pose in self.sword_trail if self.trail_clock - stamp < 0.055]
        if self.attack_left > 0:
            pose = sword_pose(self)
            if pose.phase == 'strike':
                self.sword_trail.append((self.trail_clock, pose))
                self.sword_trail = self.sword_trail[-12:]


@dataclass(eq=False)
class Enemy:
    pos: Vector2
    kind: str = 'drone'
    hp: int = 58
    max_hp: int = 58
    speed: float = 39
    velocity: Vector2 = field(default_factory=Vector2)
    stun: float = 0
    flash: float = 0
    cooldown: float = 0.7
    windup: float = 0
    age: float = 0
    facing: Vector2 = field(default_factory=lambda: Vector2(-1, 0))

    def hit(self, damage, direction, finisher=False):
        self.hp = max(0, self.hp - damage)
        self.velocity = direction * (240 if finisher else 130)
        self.stun = 0.3 if finisher else 0.18
        self.flash = 0.12
        self.windup = 0
        self.cooldown = max(self.cooldown, 0.5)

    def update(self, dt, player):
        self.age += dt
        self.flash = max(0, self.flash - dt)
        self.cooldown = max(0, self.cooldown - dt)
        self.pos += self.velocity * (1 - math.exp(-12 * dt)) / 12
        self.velocity *= math.exp(-12 * dt)
        clamp_position(self.pos)
        if self.stun > 0:
            self.stun = max(0, self.stun - dt)
            return False
        offset = player.pos - self.pos
        distance = offset.length()
        if distance:
            self.facing = offset / distance
        if self.windup > 0:
            self.windup = max(0, self.windup - dt)
            if self.windup == 0:
                self.cooldown = 1.05
                return distance <= 28 and player.hurt(18 if self.kind == 'brute' else 12)
        elif distance < 23 and self.cooldown == 0:
            self.windup = 0.42
        elif distance > 18:
            self.pos += self.facing * min(self.speed * dt, distance - 18)
            clamp_position(self.pos)
        return False
