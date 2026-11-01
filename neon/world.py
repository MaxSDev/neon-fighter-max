"""Game progression and combat orchestration; no window or asset loading."""

from dataclasses import dataclass
import math
import random

from pygame import Vector2

from neon.combat import Enemy, Player
from neon.settings import BASE_SWORD_DAMAGE, COMBO_DAMAGE_MULTIPLIERS, CYAN, ORANGE, PURPLE, clamp_position
from neon.weapon import sword_contact


@dataclass
class Particle:
    pos: Vector2
    velocity: Vector2
    color: tuple
    life: float
    total: float
    size: int = 2


@dataclass
class DamageText:
    pos: Vector2
    text: str
    color: tuple
    life: float = 0.65


@dataclass
class Impact:
    pos: Vector2
    direction: Vector2
    finisher: bool
    life: float = 0.18


class World:
    def __init__(self, seed=None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.stage = 'menu'
        self.player = Player()
        self.enemies = []
        self.particles = []
        self.damage_texts = []
        self.impacts = []
        self.paused = False
        self.wave = 0
        self.intermission = 0
        self.tutorial_hits = 0
        self.elapsed = 0
        self.kills = 0
        self.hitstop = 0
        self.impact = 0
        self.shake = 0
        self.attack_buffer = 0

    @property
    def playing(self):
        return self.stage in ('tutorial', 'arena')

    def start(self):
        self.__init__(self.seed)
        self.stage = 'tutorial'
        self.enemies = [Enemy(Vector2(322, 154), kind='dummy', hp=999, max_hp=999, speed=0)]

    def skip_tutorial(self):
        if self.stage != 'tutorial':
            return
        self.stage = 'arena'
        self.enemies.clear()
        self.player = Player()
        self.intermission = 1.6
        self.attack_buffer = 0
        self.impacts.clear()
        self.particles.clear()
        self.damage_texts.clear()
        self.hitstop = self.impact = self.shake = 0

    def toggle_pause(self):
        if self.playing:
            self.paused = not self.paused
            self.attack_buffer = 0

    def attack(self, aim):
        if not self.playing or self.paused:
            return
        if not self.player.attack(aim):
            self.attack_buffer = 0.18

    def dodge(self, direction):
        if self.playing and not self.paused and self.player.dodge(direction):
            self.burst(self.player.pos, CYAN, 10)

    def burst(self, pos, color, count):
        for _ in range(count):
            angle = self.rng.uniform(0, math.tau)
            velocity = Vector2(math.cos(angle), math.sin(angle)) * self.rng.uniform(30, 105)
            life = self.rng.uniform(0.15, 0.4)
            self.particles.append(Particle(pos.copy(), velocity, color, life, life))
        self.particles = self.particles[-220:]

    def spawn_wave(self):
        self.wave += 1
        for index in range(2 + self.wave * 2):
            # Entry points alternate around the perimeter, away from the player.
            angle = index * 2.399 + self.wave
            pos = Vector2(240 + math.cos(angle) * 204, 154 + math.sin(angle) * 78)
            if pos.distance_to(self.player.pos) < 85:
                pos = Vector2(480 - self.player.pos.x, 90 if self.player.pos.y > 154 else 230)
            brute = self.wave >= 2 and index % 3 == 0
            hp = 100 if brute else 52 + self.wave * 6
            enemy = Enemy(pos, 'brute' if brute else 'drone', hp, hp, 30 if brute else 34 + self.wave * 5)
            self.enemies.append(enemy)
            self.burst(pos, PURPLE, 12)

    def update(self, dt, movement, aim=None):
        if self.paused:
            return
        if not self.playing:
            if self.stage in ('victory', 'defeat'):
                dt = min(max(dt, 0), 0.25)
                self._update_feedback(dt)
                self.hitstop = max(0, self.hitstop - dt)
                self.player.trail_clock += dt
                self.player.sword_trail = [(stamp, pose) for stamp, pose in self.player.sword_trail
                                           if self.player.trail_clock - stamp < 0.055]
            return
        # Substeps keep sword active windows and contact checks reliable at low FPS.
        remaining = min(max(dt, 0), 0.25)
        while remaining > 1e-8 and self.playing:
            step = min(remaining, 1 / 120)
            self._step(step, movement, aim)
            remaining -= step

    def _update_feedback(self, dt):
        self.impact = max(0, self.impact - dt)
        self.shake = max(0, self.shake - dt * 18)
        for particle in self.particles:
            particle.life -= dt
            particle.pos += particle.velocity * dt
            particle.velocity *= math.exp(-5 * dt)
        self.particles = [p for p in self.particles if p.life > 0]
        for label in self.damage_texts:
            label.life -= dt
            label.pos.y -= dt * 22
        self.damage_texts = [label for label in self.damage_texts if label.life > 0]
        for impact in self.impacts:
            impact.life -= dt
        self.impacts = [impact for impact in self.impacts if impact.life > 0]

    def _step(self, dt, movement, aim):
        self._update_feedback(dt)
        if self.hitstop > 0:
            self.hitstop = max(0, self.hitstop - dt)
            return
        if self.player.hp <= 0:
            self.stage = 'defeat'
            return
        self.elapsed += dt
        player = self.player
        player.update(dt, movement)
        if aim is not None and aim.length_squared() and player.attack_left == 0:
            player.facing = aim.normalize()
        if self.attack_buffer > 0:
            self.attack_buffer = max(0, self.attack_buffer - dt)
            if player.attack_left == 0 and player.dash_left == 0:
                player.attack(aim if aim is not None else player.facing)
                self.attack_buffer = 0
        if player.strike_active:
            self._resolve_strike()
        for enemy in self.enemies:
            if enemy.kind == 'dummy':
                enemy.flash = max(0, enemy.flash - dt)
                continue
            if enemy.hp <= 0:
                continue
            if enemy.update(dt, player):
                self.burst(player.pos, ORANGE, 18)
                self.damage_texts.append(DamageText(player.pos + Vector2(0, -23), '-18' if enemy.kind == 'brute' else '-12', ORANGE))
                self.shake = max(self.shake, 2)
        # Soft body separation avoids enemies collapsing into one unreadable sprite.
        for index, first in enumerate(self.enemies):
            for second in self.enemies[index + 1:]:
                delta = second.pos - first.pos
                distance = delta.length()
                if 0 < distance < 16:
                    push = delta / distance * (16 - distance) * min(0.5, dt * 8)
                    first.pos -= push
                    second.pos += push
                    clamp_position(first.pos)
                    clamp_position(second.pos)
        self.enemies = [e for e in self.enemies if e.hp > 0]
        if player.hp <= 0:
            self.stage = 'defeat'
        elif self.stage == 'tutorial' and self.tutorial_hits >= 4:
            self.skip_tutorial()
        elif self.stage == 'arena' and not self.enemies:
            if self.wave == 3:
                self.stage = 'victory'
            elif self.intermission > 0:
                self.intermission = max(0, self.intermission - dt)
                if self.intermission == 0:
                    self.spawn_wave()
            else:
                self.intermission = 2
                player.hp = min(100, player.hp + 15)

    def _resolve_strike(self):
        player = self.player
        finisher = player.combo == 4
        for enemy in self.enemies:
            if enemy.hp <= 0 or enemy in player.hit_ids:
                continue
            contact = sword_contact(player, enemy.pos + Vector2(0, -10), 9)
            if contact is None:
                continue
            player.hit_ids.add(enemy)
            damage = round(BASE_SWORD_DAMAGE * COMBO_DAMAGE_MULTIPLIERS[player.combo - 1])
            direction = enemy.pos - player.pos
            direction = direction.normalize() if direction.length_squared() else player.facing
            enemy.hit(damage, direction, finisher)
            self.burst(contact, PURPLE if finisher else CYAN, 22 if finisher else 10)
            self.impacts.append(Impact(contact, direction, finisher))
            self.impacts = self.impacts[-24:]
            self.damage_texts.append(DamageText(enemy.pos + Vector2(0, -23), str(damage), CYAN))
            self.hitstop = 0.055 if finisher else 0.028
            self.shake = max(self.shake, 2.8 if finisher else 1)
            if finisher:
                self.impact = 0.065
            if self.stage == 'tutorial':
                self.tutorial_hits += 1
            if enemy.hp == 0:
                self.kills += 1
                self.burst(enemy.pos, ORANGE, 16)
