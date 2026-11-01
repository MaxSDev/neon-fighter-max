"""Game progression and combat orchestration; no window or asset loading."""

from dataclasses import dataclass
from collections import deque
import math
import random
import pygame

from pygame import Vector2

from neon.combat import Enemy, Player
from neon.settings import ARENA, OBSTACLES, BASE_SWORD_DAMAGE, COMBO_DAMAGE_MULTIPLIERS, CYAN, ORANGE, PURPLE, clamp_position
from neon.balance import (ENEMIES, WAVES, MAX_ACTIVE_ENEMIES, SPAWN_INTERVAL, SPAWN_WARNING,
                          SPAWN_PLAYER_DISTANCE, WAVE_BREAK, WAVE_HEAL, BOSS_DESTRUCTION_TIME,
                          BOSS_EXPLOSION_AT, PLAYER_DEFEAT_TIME, MAX_PROJECTILES)
from neon.weapon import sword_contact
from neon.enemies import create_enemy
from neon.tutorial import Tutorial


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


@dataclass
class SpawnTicket:
    kind: str
    pos: Vector2
    left: float = SPAWN_WARNING


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
        self.spawn_queue = deque()
        self.pending_spawn = None
        self.spawn_timer = 0
        self.spawn_history = []
        self.projectiles = []
        self.boss_announced = False
        self.boss_spawned = False
        self.boss_defeated = False
        self.boss_destruction = 0
        self.boss_death_pos = None
        self.destruction_tick = 0
        self.tutorial = Tutorial()
        self.audio_events = deque(maxlen=128)
        self.sequence_elapsed = 0
        self.boss_exploded = False
        self.scene_age = 1

    def emit(self, event):
        self.audio_events.append(event)

    def drain_audio_events(self):
        events = list(self.audio_events)
        self.audio_events.clear()
        return events

    def _set_stage(self, stage):
        if self.stage != stage:
            self.stage = stage
            self.scene_age = 0

    @property
    def playing(self):
        return self.stage in ('tutorial', 'arena')

    def start(self):
        self.__init__(self.seed)
        self._set_stage('tutorial')
        self.enemies = [Enemy(Vector2(322, 154), kind='dummy', hp=999, max_hp=999, speed=0)]

    def skip_tutorial(self):
        if self.stage != 'tutorial':
            return
        self._set_stage('arena')
        self.enemies.clear()
        self.projectiles.clear()
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
        else:
            self.emit('swing_heavy' if self.player.combo == 4 else 'swing')

    def dodge(self, direction):
        if self.playing and not self.paused and self.player.dodge(direction):
            self.burst(self.player.pos, CYAN, 10)
            self.emit('dash')
            if self.stage == 'tutorial' and self.tutorial.step == 'dodge':
                self.tutorial.dashes += 1

    def burst(self, pos, color, count):
        for _ in range(count):
            angle = self.rng.uniform(0, math.tau)
            velocity = Vector2(math.cos(angle), math.sin(angle)) * self.rng.uniform(30, 105)
            life = self.rng.uniform(0.15, 0.4)
            self.particles.append(Particle(pos.copy(), velocity, color, life, life))
        self.particles = self.particles[-220:]

    def spawn_wave(self):
        if self.wave >= len(WAVES):
            return
        self.wave += 1
        self.spawn_queue.extend(WAVES[self.wave - 1])
        self.intermission = 0
        self.spawn_timer = 0
        self.emit('wave_start')

    @staticmethod
    def spawn_bounds_valid(pos, kind):
        half_width = 24 if kind == 'sentinel' else 12
        height = 48 if kind == 'sentinel' else 24
        body = pygame.Rect(round(pos.x - half_width), round(pos.y - height), half_width * 2, height + 4)
        return ARENA.contains(body) and not any(body.colliderect(rect) for rect in OBSTACLES)

    def spawn_position_valid(self, pos, kind):
        distance = 120 if kind == 'sentinel' else SPAWN_PLAYER_DISTANCE
        return (self.spawn_bounds_valid(pos, kind)
                and pos.distance_to(self.player.pos) >= distance
                and all(pos.distance_to(e.pos) > ENEMIES[kind].radius + e.radius + 12 for e in self.enemies))

    def find_spawn_position(self, kind):
        candidates = [Vector2(x, y) for x in range(48, 442, 32) for y in range(96, 237, 28)]
        self.rng.shuffle(candidates)
        return next((pos for pos in candidates if self.spawn_position_valid(pos, kind)), None)

    def _update_spawns(self, dt):
        self.spawn_timer = max(0, self.spawn_timer - dt)
        if self.pending_spawn is not None:
            ticket = self.pending_spawn
            ticket.left = max(0, ticket.left - dt)
            if ticket.left == 0:
                # Revalidate after the warning: the player may have moved into it.
                if not self.spawn_position_valid(ticket.pos, ticket.kind):
                    self.pending_spawn = None
                    self.spawn_timer = 0.1
                    return
                enemy = create_enemy(ticket.pos, ticket.kind)
                self.enemies.append(enemy)
                self.spawn_queue.popleft()
                self.spawn_history.append((self.elapsed, ticket.kind, ticket.pos.copy()))
                self.boss_spawned |= ticket.kind == 'sentinel'
                if ticket.kind == 'sentinel':
                    self.emit('boss_spawn')
                self.burst(ticket.pos, PURPLE, 12)
                self.pending_spawn = None
                self.spawn_timer = SPAWN_INTERVAL
        elif self.spawn_queue and self.spawn_timer == 0 and len(self.enemies) < MAX_ACTIVE_ENEMIES:
            kind = self.spawn_queue[0]
            pos = self.find_spawn_position(kind)
            if pos is not None:
                self.pending_spawn = SpawnTicket(kind, pos)

    def _collect_dead(self):
        for enemy in self.enemies:
            if enemy.hp > 0:
                continue
            self.kills += 1
            self.emit('enemy_destroy' if enemy.kind != 'sentinel' else 'boss_destroy')
            self.burst(enemy.pos, ORANGE, 16)
            if enemy.kind == 'sentinel':
                self.boss_defeated = True
                self.boss_destruction = BOSS_DESTRUCTION_TIME
                self.boss_death_pos = enemy.pos.copy()
                self.sequence_elapsed = 0
                self.player.dash_left = 0
                self.attack_buffer = 0
                self._set_stage('boss_dying')
                self.projectiles.clear()
                self.spawn_queue.clear()
                self.pending_spawn = None
                self.burst(enemy.pos + Vector2(0, -18), ORANGE, 35)
        self.enemies = [enemy for enemy in self.enemies if enemy.hp > 0]

    def _advance_progression(self, dt):
        if self.enemies or self.spawn_queue or self.pending_spawn:
            self._update_spawns(dt)
            return
        if self.intermission > 0:
            self.intermission = max(0, self.intermission - dt)
            if self.intermission == 0:
                if self.boss_announced:
                    self.spawn_queue.append('sentinel')
                    self.spawn_timer = 0
                else:
                    self.spawn_wave()
        else:
            self.intermission = WAVE_BREAK
            self.player.hp = min(100, self.player.hp + WAVE_HEAL)
            self.projectiles.clear()
            if self.wave == len(WAVES):
                self.boss_announced = True

    def update(self, dt, movement, aim=None):
        if self.paused:
            return
        self.scene_age += min(max(dt, 0), 0.25)
        if self.stage in ('boss_dying', 'player_dying'):
            self._update_sequence(min(max(dt, 0), 0.25))
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

    def _begin_player_defeat(self):
        self._set_stage('player_dying')
        self.sequence_elapsed = 0
        self.player.attack_left = 0
        self.player.dash_left = 0
        self.attack_buffer = 0
        self.projectiles.clear()
        self.emit('defeat')
        self.burst(self.player.pos + Vector2(0, -10), CYAN, 24)

    def _update_sequence(self, dt):
        self.sequence_elapsed += dt
        self._update_feedback(dt)
        # Finish the killing swing while freezing translation, enemies and spawns.
        if self.hitstop > 0:
            self.hitstop = max(0, self.hitstop - dt)
        else:
            self.player.update(dt, Vector2())
        if self.stage == 'boss_dying':
            self.boss_destruction = max(0, BOSS_DESTRUCTION_TIME - self.sequence_elapsed)
            self.destruction_tick += dt
            if self.sequence_elapsed < BOSS_EXPLOSION_AT and self.destruction_tick >= 0.12:
                self.destruction_tick = 0
                self.burst(self.boss_death_pos + Vector2(0, -18), ORANGE, 5)
            if self.sequence_elapsed >= BOSS_EXPLOSION_AT and not self.boss_exploded:
                self.boss_exploded = True
                self.emit('hit_heavy')
                self.burst(self.boss_death_pos + Vector2(0, -18), ORANGE, 60)
                for _ in range(18):
                    velocity = Vector2(self.rng.uniform(-65, 65), self.rng.uniform(-60, 25))
                    self.particles.append(Particle(self.boss_death_pos + Vector2(0, -18), velocity,
                                                   self.rng.choice((CYAN, ORANGE, PURPLE)), 1.2, 1.2, 3))
            if self.boss_destruction == 0:
                self._set_stage('victory')
                self.emit('victory')
        elif self.sequence_elapsed >= PLAYER_DEFEAT_TIME:
            self._set_stage('defeat')

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
            self._begin_player_defeat()
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
                self.emit('swing_heavy' if player.combo == 4 else 'swing')
                self.attack_buffer = 0
        if player.strike_active:
            self._resolve_strike()
        if any(enemy.kind == 'sentinel' and enemy.hp <= 0 for enemy in self.enemies):
            self._collect_dead()
            return
        for enemy in self.enemies:
            if enemy.kind == 'dummy':
                enemy.flash = max(0, enemy.flash - dt)
                continue
            if enemy.hp <= 0:
                continue
            was_preparing = enemy.windup > 0
            if enemy.update(dt, player):
                self.burst(player.pos, ORANGE, 18)
                self.damage_texts.append(DamageText(player.pos + Vector2(0, -23), f'-{enemy.stats.damage}', ORANGE))
                self.shake = max(self.shake, 2)
                self.emit('player_hurt')
            if enemy.kind == 'sentinel' and not was_preparing and enemy.windup > 0:
                self.emit('boss_attack')
            if enemy.shots:
                self.emit('enemy_shot')
            self.projectiles.extend(enemy.shots[:max(0, MAX_PROJECTILES - len(self.projectiles))])
            enemy.shots.clear()
        for shot in self.projectiles:
            if shot.update(dt, player, player.previous_pos):
                self.burst(player.pos + Vector2(0, -10), ORANGE, 12)
                self.damage_texts.append(DamageText(player.pos + Vector2(0, -23), f'-{shot.damage}', ORANGE))
                self.shake = max(self.shake, 1.5)
            if shot.contact:
                self.emit('projectile_hit')
                if shot.training and shot.evaded:
                    self.tutorial.evaded = True
        self.projectiles = [shot for shot in self.projectiles if shot.alive]
        # Soft body separation avoids enemies collapsing into one unreadable sprite.
        for index, first in enumerate(self.enemies):
            for second in self.enemies[index + 1:]:
                delta = second.pos - first.pos
                distance = delta.length()
                spacing = first.radius + second.radius
                if 0 < distance < spacing:
                    push = delta / distance * (spacing - distance) * min(0.5, dt * 8)
                    first.pos -= push
                    second.pos += push
                    clamp_position(first.pos, first.radius)
                    clamp_position(second.pos, second.radius)
        self._collect_dead()
        if player.hp <= 0:
            self._begin_player_defeat()
        elif self.stage == 'tutorial':
            previous_step = self.tutorial.step
            moved = player.pos.distance_to(player.previous_pos) if movement.length_squared() and player.dash_left == 0 else 0
            shot = self.tutorial.update(dt, moved, player)
            if shot is not None:
                self.projectiles.append(shot)
                self.emit('enemy_shot')
            if self.tutorial.step != previous_step:
                self.emit('tutorial_step')
            if self.tutorial.finished:
                self.skip_tutorial()
        elif self.stage == 'arena':
            self._advance_progression(dt)

    def _resolve_strike(self):
        if self.stage == 'tutorial' and self.tutorial.step == 'movement':
            return
        player = self.player
        finisher = player.combo == 4
        for enemy in self.enemies:
            if enemy.hp <= 0 or enemy in player.hit_ids:
                continue
            contact = sword_contact(player, enemy.pos + Vector2(0, -18 if enemy.kind == 'sentinel' else -10), enemy.radius)
            if contact is None:
                continue
            player.hit_ids.add(enemy)
            damage = round(BASE_SWORD_DAMAGE * COMBO_DAMAGE_MULTIPLIERS[player.combo - 1])
            direction = enemy.pos - player.pos
            direction = direction.normalize() if direction.length_squared() else player.facing
            enemy.hit(damage, direction, finisher)
            if enemy.kind == 'dummy':
                enemy.hp = max(100, enemy.hp)
            self.emit('hit_heavy' if finisher else 'hit')
            self.emit('enemy_hurt')
            if finisher:
                self.emit('spark')
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
                if self.tutorial.register_hit(player.combo):
                    player.combo = 0
                    player.combo_window = 0
                    self.emit('tutorial_step')
