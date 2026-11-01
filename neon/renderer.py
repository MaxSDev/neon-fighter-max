"""Cached pixel art, combat effects, HUD and Spanish game screens."""

import math

import pygame

from neon.art import glow, make_background, make_robot, sword_polygon
from neon.settings import CYAN, INK, MUTED, ORANGE, PURPLE, WHITE
from neon.weapon import sword_pose
from neon.balance import (ENEMIES, BOSS_ENERGY_SPREAD, BOSS_DESTRUCTION_TIME, BOSS_EXPLOSION_AT,
                          PLAYER_DEFEAT_TIME, ENDING_FADE_TIME, SPAWN_WARNING, WAVES)


class Renderer:
    def __init__(self):
        self.background = make_background()
        self.scene = pygame.Surface((480, 270))
        self.fonts = {size: pygame.font.Font(None, size * 2) for size in (12, 14, 16, 18, 22, 28, 42, 56)}
        self.effects = pygame.Surface((480, 270), pygame.SRCALPHA)
        self.camera_offset = (0, 0)
        self.sprites = {(kind, frame, flip, flash): make_robot(kind, frame, flip, flash)
                        for kind in ('player', *ENEMIES)
                        for frame in (-1, 0, 1) for flip in (False, True) for flash in (False, True)}
        self.buttons = {}

    def text(self, target, message, pos, color=WHITE, size=14, center=False):
        image = self.fonts[size].render(message, False, color)
        pos = (round(pos[0] * 2), round(pos[1] * 2))
        rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        target.blit(image, rect)
        return rect

    @staticmethod
    def ui_rect(target, color, rect, width=0):
        pygame.draw.rect(target, color, tuple(round(value * 2) for value in rect), width * 2)

    @staticmethod
    def ui_line(target, color, start, end, width=1):
        pygame.draw.line(target, color, tuple(round(v * 2) for v in start), tuple(round(v * 2) for v in end), width * 2)

    def button(self, target, key, label, rect, mouse, primary=False):
        rect = pygame.Rect(rect)
        self.buttons[key] = rect
        hover = rect.collidepoint(mouse)
        color = CYAN if primary else PURPLE
        self.ui_rect(target, (29, 60, 74) if hover else (17, 30, 46), rect)
        self.ui_rect(target, color if hover or primary else (72, 65, 101), rect, 1)
        self.ui_rect(target, color, (rect.x, rect.y, 3, rect.height))
        self.text(target, label, rect.center, WHITE, 16, True)

    def draw(self, target, world, mouse, time):
        self.scene.blit(self.background, (0, 0))
        self._ambient(self.scene, time)
        self._spawn_warning(self.scene, world, time)
        actors = [(enemy.pos.y, enemy, enemy.kind) for enemy in world.enemies]
        if world.stage == 'tutorial' and world.tutorial.step == 'movement':
            actors = []
        fallen = world.stage == 'defeat' or (world.stage == 'player_dying' and world.sequence_elapsed > 0.35)
        if world.stage != 'menu' and not fallen:
            actors.append((world.player.pos.y, world.player, 'player'))
        for _, actor, kind in sorted(actors, key=lambda item: item[0]):
            self._actor(self.scene, actor, kind)
        if world.stage not in ('menu', 'player_dying', 'defeat'):
            self._sword(self.scene, world.player)
        for shot in world.projectiles:
            direction = shot.velocity.normalize()
            pygame.draw.line(self.scene, (133, 49, 88), shot.pos - direction * 9, shot.pos, shot.radius * 2)
            pygame.draw.circle(self.scene, ORANGE, shot.pos, shot.radius)
            pygame.draw.circle(self.scene, (255, 235, 192), shot.pos, max(1, shot.radius - 2))
        if world.boss_destruction > 0 or (world.stage == 'victory' and world.boss_death_pos is not None):
            self._boss_destruction(self.scene, world, time)
        if world.stage in ('player_dying', 'defeat'):
            self._player_destruction(self.scene, world)
        if world.stage == 'tutorial' and world.tutorial.step == 'dodge':
            self._training_emitter(self.scene, world)
        for particle in world.particles:
            size = max(1, round(particle.size * particle.life / particle.total))
            pygame.draw.rect(self.scene, particle.color, (*particle.pos, size, size))
        offset = (0, 0)
        if world.shake > 0 and world.playing and not world.paused:
            offset = (round(math.sin(time * 89) * world.shake), round(math.cos(time * 73) * world.shake / 2))
        self.camera_offset = offset
        self._impacts(self.scene, world)
        target.fill(INK)
        target.blit(self.scene, offset)
        if world.impact > 0:
            self.effects.fill((143, 99, 228, round(30 * world.impact / 0.065)))
            target.blit(self.effects, (0, 0))
        if world.stage in ('boss_dying', 'player_dying'):
            duration = BOSS_DESTRUCTION_TIME if world.stage == 'boss_dying' else PLAYER_DEFEAT_TIME
            fade = max(0, min(1, (world.sequence_elapsed - duration + ENDING_FADE_TIME) / ENDING_FADE_TIME))
            self.effects.fill((5, 10, 22, round(155 * fade)))
            target.blit(self.effects, (0, 0))
        elif world.stage in ('tutorial', 'arena') and world.scene_age < 0.3:
            self.effects.fill((5, 10, 22, round(140 * (1 - world.scene_age / 0.3))))
            target.blit(self.effects, (0, 0))

    def draw_ui(self, target, world, mouse, time, audio=None):
        """Draw crisp text after integer scaling; coordinates stay in world units."""
        self.buttons.clear()
        offset = pygame.Vector2(self.camera_offset)
        for label in world.damage_texts:
            self.text(target, label.text, label.pos + offset, label.color, 16, True)
        for enemy in world.enemies:
            if enemy.kind == 'dummy' and not (world.stage == 'tutorial' and world.tutorial.step == 'movement'):
                self.text(target, 'DRON DE PRÁCTICA', enemy.pos + offset + (0, -34), WHITE, 12, True)
            elif enemy.windup > 0:
                self.text(target, '!', enemy.pos + offset + (0, -55 if enemy.kind == 'sentinel' else -34), ORANGE, 18, True)
        if world.stage == 'menu':
            self._menu(target, mouse, time)
        else:
            self._hud(target, world)
            boss = next((enemy for enemy in world.enemies if enemy.kind == 'sentinel'), None)
            if boss is not None:
                self.ui_rect(target, INK, (110, 32, 260, 25))
                self.text(target, 'SENTINEL-X', (240, 39), ORANGE, 14, True)
                self.ui_rect(target, (56, 33, 45), (118, 49, 244, 5))
                self.ui_rect(target, ORANGE, (118, 49, round(244 * boss.hp / boss.max_hp), 5))
            if world.paused:
                self._overlay(target, 'SISTEMA EN PAUSA', 'Respira. La arena puede esperar.')
                self.button(target, 'resume', 'CONTINUAR  /  ESC', (156, 151, 168, 28), mouse, True)
                self.button(target, 'menu', 'VOLVER AL INICIO', (156, 188, 168, 25), mouse)
                if audio is not None:
                    self._audio_controls(target, mouse, audio)
            elif world.stage in ('victory', 'defeat'):
                victory = world.stage == 'victory'
                self._overlay(target, 'VICTORIA' if victory else 'SEÑAL PERDIDA',
                              'Sentinel-X derrotado' if victory else 'Tu núcleo se apagó. Vuelve a intentarlo.',
                              min(1, world.scene_age / 0.4))
                self.text(target, f'{world.kills} bajas  /  {int(world.elapsed)} s', (240, 142), MUTED, 16, True)
                self.button(target, 'restart', 'JUGAR DE NUEVO  /  R', (148, 158, 184, 27), mouse, True)
                self.button(target, 'menu', 'VOLVER AL MENÚ', (148, 192, 184, 24), mouse)
                self.button(target, 'quit', 'SALIR', (190, 224, 100, 21), mouse)
            else:
                if world.stage == 'tutorial':
                    self._tutorial_ui(target, world, mouse)
                elif world.stage == 'arena' and world.intermission > 0:
                    title = 'ALERTA: SENTINEL-X' if world.boss_announced else f'OLEADA {world.wave + 1}  /  {math.ceil(world.intermission)}'
                    self.text(target, title, (240, 116), ORANGE if world.boss_announced else CYAN, 28, True)
                    self.text(target, 'Núcleo estabilizado · Prepárate', (240, 137), WHITE, 14, True)
                elif world.stage == 'boss_dying':
                    self.text(target, 'NÚCLEO INESTABLE', (240, 49), ORANGE, 16, True)
                elif world.stage == 'player_dying':
                    self.text(target, 'REACTOR APAGÁNDOSE', (240, 49), CYAN, 16, True)
                elif world.stage == 'arena' and boss is None:
                    remaining = len(world.enemies) + len(world.spawn_queue)
                    self.ui_rect(target, INK, (151, 35, 178, 19))
                    self.text(target, f'HOSTILES RESTANTES: {remaining}', (240, 45), MUTED, 12, True)
                if world.playing:
                    self._crosshair(target, mouse)
        if world.stage == 'menu' and audio is not None:
            self._audio_controls(target, mouse, audio)
        if not world.playing or world.paused:
            x, y = mouse
            pygame.draw.polygon(target, INK, [(2*x - 2, 2*y - 2), (2*x + 16, 2*y + 12), (2*x + 8, 2*y + 14), (2*x + 2, 2*y + 22)])
            pygame.draw.polygon(target, CYAN, [(2*x, 2*y), (2*x + 12, 2*y + 10), (2*x + 6, 2*y + 12), (2*x + 2, 2*y + 16)])

    def _ambient(self, target, time):
        for index in range(13):
            x = (index * 79 + math.sin(time * 0.3 + index) * 4) % 420 + 30
            y = 65 + (index * 37 - time * (2 + index % 3)) % 174
            color = (52, 90, 108) if index % 2 else (91, 66, 123)
            pygame.draw.rect(target, color, (int(x), int(y), 1, 1))
        for x in (154, 306):
            pygame.draw.rect(target, CYAN if math.sin(time * 2) > -0.8 else (40, 76, 90), (x, 52, 20, 2))

    def _actor(self, target, actor, kind):
        player = kind == 'player'
        x, y = round(actor.pos.x), round(actor.pos.y)
        pygame.draw.ellipse(target, (10, 17, 26), (x - 17, y - 4, 34, 10) if kind == 'sentinel' else (x - 10, y - 3, 20, 7))
        if player and actor.dash_left > 0:
            for index in (3, 2, 1):
                pos = actor.pos - actor.dash_direction * index * 7
                pygame.draw.ellipse(target, (25, 66, 82), (pos.x - 7, pos.y - 10, 14, 10), 1)
        if not player and actor.windup > 0:
            if getattr(actor, 'attack_kind', 'melee') == 'energy':
                origin = actor.pos + pygame.Vector2(0, -18 if kind == 'sentinel' else -10)
                for angle in BOSS_ENERGY_SPREAD if kind == 'sentinel' else (0,):
                    direction = actor.locked_aim.rotate(angle)
                    for distance in range(22, 230, 12):
                        point = origin + direction * distance
                        if 24 <= point.x <= 456 and 62 <= point.y <= 244:
                            pygame.draw.line(target, (183, 80, 91), point, point + direction * 5)
                pygame.draw.circle(target, ORANGE, origin + actor.locked_aim * (20 if kind == 'sentinel' else 12),
                                   4 + int(actor.age * 14) % 3, 1)
            else:
                radius = round(actor.stats.reach)
                pygame.draw.circle(target, ORANGE, (x, y), radius, 1)
                pygame.draw.circle(target, (130, 70, 50), (x, y), max(3, int(radius * actor.windup / actor.stats.windup)), 1)
        age = actor.walk_time if player else actor.age * 8
        moving = actor.moving if player else kind != 'dummy' and actor.windup == 0 and actor.stun == 0 and getattr(actor, 'recovery', 0) == 0
        frame = (1 if math.sin(age) > 0 else -1) if moving else 0
        flash = (actor.invulnerable > 0 and int(actor.invulnerable * 22) % 2 == 0) if player else actor.flash > 0
        sprite = self.sprites[kind, frame, actor.facing.x < 0, flash]
        bob = -1 if moving and frame == 1 else 0
        if kind == 'sentinel' and actor.recovery > 0:
            bob = 2
        target.blit(sprite, (x - sprite.get_width() // 2, y - (48 if kind == 'sentinel' else 24) + bob))
        if kind == 'sentinel' and actor.recovery > 0:
            pygame.draw.circle(target, (117, 67, 52), (x, y - 20), 9, 1)
            pygame.draw.line(target, ORANGE, (x - 4, y - 20), (x + 4, y - 20))
        if not player and kind not in ('dummy', 'sentinel') and actor.hp < actor.max_hp:
            pygame.draw.rect(target, (15, 19, 30), (x - 11, y - 29, 22, 3))
            pygame.draw.rect(target, ORANGE, (x - 11, y - 29, max(1, int(22 * actor.hp / actor.max_hp)), 2))
        if kind == 'dummy':
            pygame.draw.circle(target, PURPLE, (x, y + 1), 14, 1)

    def _spawn_warning(self, target, world, time):
        ticket = world.pending_spawn
        if ticket is None:
            return
        radius = 20 if ticket.kind == 'sentinel' else 12
        pygame.draw.circle(target, PURPLE, ticket.pos, radius, 1)
        pygame.draw.circle(target, (91, 64, 131), ticket.pos, max(2, round(radius * ticket.left / SPAWN_WARNING)), 1)
        pygame.draw.line(target, PURPLE, ticket.pos + (-4, 0), ticket.pos + (4, 0))

    def _boss_destruction(self, target, world, time):
        pos = world.boss_death_pos
        age = world.sequence_elapsed
        if age < BOSS_EXPLOSION_AT:
            sprite = self.sprites['sentinel', 0, False, int(age * 15) % 3 == 0]
            jitter = round(math.sin(age * 70) * min(3, age * 2))
            target.blit(sprite, (pos.x - 24 + jitter, pos.y - 48 + round(age * 2)))
            color = ORANGE if int(age * 20) % 2 else (87, 38, 34)
            pygame.draw.circle(target, color, pos + (jitter, -21), max(2, round(6 - age * 2)))
        else:
            self.effects.fill((0, 0, 0, 0))
            expansion = min(1, (age - BOSS_EXPLOSION_AT) / 0.5)
            pygame.draw.circle(self.effects, (*ORANGE, round(230 * (1 - expansion))), pos + (0, -18),
                               round(10 + expansion * 40), 2)
            target.blit(self.effects, (0, 0))
            for dx, dy, width in ((-14, -3, 9), (7, 1, 12), (-3, -10, 7)):
                pygame.draw.rect(target, (52, 48, 61), (pos.x + dx, pos.y + dy, width, 3))

    def _player_destruction(self, target, world):
        pos = world.player.pos
        age = PLAYER_DEFEAT_TIME if world.stage == 'defeat' else world.sequence_elapsed
        sprite = self.sprites['player', 0, world.player.facing.x < 0, int(age * 12) % 3 == 0]
        if age > 0.35:
            # A collapsing silhouette and extinguished visor, not a frozen menu.
            fallen = pygame.transform.rotate(sprite, min(90, (age - 0.35) * 150))
            target.blit(fallen, fallen.get_rect(midbottom=(pos.x, pos.y + 3)))
            pygame.draw.rect(target, (13, 24, 37), (pos.x - 6, pos.y - 4, 12, 2))

    def _training_emitter(self, target, world):
        tutorial = world.tutorial
        x, y = tutorial.emitter
        pygame.draw.rect(target, (68, 57, 94), (x - 7, y - 8, 14, 16))
        pygame.draw.circle(target, PURPLE, tutorial.emitter, 4)
        if tutorial.warning > 0:
            for distance in range(12, 420, 12):
                point = tutorial.emitter + tutorial.aim * distance
                if 24 <= point.x <= 456 and 62 <= point.y <= 244:
                    pygame.draw.line(target, ORANGE, point, point + tutorial.aim * 5)

    def _tutorial_ui(self, target, world, mouse):
        tutorial = world.tutorial
        self.ui_rect(target, INK, (55, 36, 370, 24))
        self.text(target, tutorial.message, (240, 48), CYAN if tutorial.confirmation > 0 else WHITE, 16, True)
        self.button(target, 'skip', 'OMITIR / ENTER', (358, 63, 110, 18), mouse)
        step = ('movement', 'attack', 'combo', 'dodge', 'complete').index(tutorial.step)
        for index in range(5):
            self.ui_rect(target, CYAN if index <= step else (51, 48, 72), (205 + index * 15, 63, 10, 3))
        hint = {'movement': f'Desplazamiento: {min(100, round(tutorial.distance / 80 * 100))}%',
                'attack': 'Acércate al dron y conecta un golpe',
                'combo': f'Cadena conectada: {tutorial.chain}/4',
                'dodge': f'Evita un disparo · Dashes de práctica: {min(2, tutorial.dashes)}/2',
                'complete': 'Accediendo a la arena...'}[tutorial.step]
        self.ui_rect(target, INK, (50, 233, 380, 17))
        self.text(target, hint, (240, 241), MUTED, 14, True)

    def _audio_controls(self, target, mouse, audio):
        self.ui_rect(target, INK, (8, 185, 128, 63))
        for index, (category, label, value) in enumerate((('music', 'Música', audio.music_volume),
                                                          ('effects', 'Efectos', audio.effects_volume))):
            y = 188 + index * 20
            self.text(target, f'{label} {round(value * 100)}%', (12, y + 3), WHITE, 12)
            self.button(target, f'{category}_down', '-', (91, y, 18, 17), mouse)
            self.button(target, f'{category}_up', '+', (113, y, 18, 17), mouse)
        label = 'AUDIO NO DISPONIBLE' if not audio.enabled else ('ACTIVAR / M' if audio.muted else 'SILENCIAR / M')
        self.button(target, 'mute', label, (12, 229, 118, 16), mouse)

    def _sword(self, target, player):
        pose = sword_pose(player)
        finisher = player.combo == 4
        color = PURPLE if finisher and player.attack_left > 0 else CYAN
        self.effects.fill((0, 0, 0, 0))
        previous = None
        # Store actual world-space poses so moving attacks leave a physical trail.
        for stamp, old in player.sword_trail:
            fade = max(0, 1 - (player.trail_clock - stamp) / 0.055)
            if previous is not None:
                pygame.draw.polygon(self.effects, (*color, round(125 * fade)),
                                    [previous.heel, previous.tip, old.tip, old.heel])
            pygame.draw.line(self.effects, (*color, round(150 * fade)), old.heel, old.tip, 2)
            previous = old
        pygame.draw.line(self.effects, (*color, 65), pose.heel, pose.tip, 7)
        target.blit(self.effects, (0, 0))
        shoulder = player.pos + pygame.Vector2(3 if player.facing.x >= 0 else -3, -15)
        pygame.draw.line(target, (30, 49, 70), shoulder, pose.hand, 5)
        pygame.draw.line(target, (128, 163, 181), shoulder, pose.hand, 2)
        pygame.draw.line(target, (42, 61, 82), pose.hand, pose.heel, 3)
        direction = (pose.tip - pose.heel).normalize()
        side = pygame.Vector2(-direction.y, direction.x)
        pygame.draw.line(target, PURPLE, pose.heel - side * 4, pose.heel + side * 4, 2)
        pygame.draw.polygon(target, color, sword_polygon(pose.heel, pose.angle, pose.tip.distance_to(pose.heel), 3))
        pygame.draw.line(target, WHITE, pose.heel, pose.tip, 1)
        pygame.draw.circle(target, (156, 190, 207), pose.hand, 2)

    def _impacts(self, target, world):
        self.effects.fill((0, 0, 0, 0))
        for impact in world.impacts:
            fade = max(0, impact.life / 0.18)
            color = PURPLE if impact.finisher else CYAN
            center = impact.pos
            radius = round((1 - fade) * 12) + (8 if impact.finisher else 4)
            pygame.draw.circle(self.effects, (*color, round(210 * fade)), center, radius, 1)
            pygame.draw.circle(self.effects, (*WHITE, round(245 * fade)), center, max(1, round(3 * fade)))
            for index in range(6 if impact.finisher else 4):
                angle = math.atan2(impact.direction.y, impact.direction.x) + index * math.tau / (6 if impact.finisher else 4)
                direction = pygame.Vector2(math.cos(angle), math.sin(angle))
                pygame.draw.line(self.effects, (*WHITE, round(240 * fade)),
                                 center + direction * 2, center + direction * radius, 2 if impact.finisher else 1)
        target.blit(self.effects, (0, 0))

    def _hud(self, target, world):
        self.ui_rect(target, INK, (0, 0, 480, 30))
        self.ui_line(target, (41, 61, 80), (15, 29), (465, 29))
        self.text(target, 'MAX / NÚCLEO', (16, 5), CYAN, 12)
        self.ui_rect(target, (37, 45, 65), (16, 18, 113, 5))
        self.ui_rect(target, CYAN if world.player.hp > 30 else ORANGE, (16, 18, int(113 * world.player.hp / 100), 5))
        self.text(target, f'{world.player.hp:03d}', (135, 14), WHITE, 14)
        self.text(target, 'CADENA', (198, 5), MUTED, 12)
        for index in range(4):
            color = (PURPLE if index == 3 else CYAN) if index < world.player.combo else (42, 49, 69)
            self.ui_rect(target, color, (199 + index * 13, 18, 9, 5))
        self.text(target, 'ESQUIVA', (287, 5), MUTED, 12)
        self.ui_rect(target, (42, 49, 69), (288, 18, 44, 4))
        self.ui_rect(target, PURPLE, (288, 18, int(44 * (1 - world.player.dash_cooldown / 0.8)), 4))
        status = 'ENTRENAMIENTO' if world.stage == 'tutorial' else ('SENTINEL-X' if world.boss_spawned else f'OLEADA  {world.wave}/{len(WAVES)}')
        self.text(target, status, (372, 9), WHITE, 16)
        self.ui_rect(target, INK, (0, 254, 480, 16))
        self.text(target, 'WASD mover   /   RATÓN apuntar   /   CLIC o J atacar   /   SHIFT esquivar   /   ESC pausa', (240, 262), MUTED, 12, True)

    def _overlay(self, target, title, subtitle, opacity=1):
        veil = pygame.Surface(target.get_size(), pygame.SRCALPHA)
        veil.fill((5, 10, 22, round(215 * opacity)))
        target.blit(veil, (0, 0))
        self.ui_line(target, PURPLE, (174, 67), (306, 67))
        self.text(target, title, (240, 98), CYAN, 28, True)
        self.text(target, subtitle, (240, 121), MUTED, 14, True)

    def _menu(self, target, mouse, time):
        veil = pygame.Surface(target.get_size(), pygame.SRCALPHA)
        veil.fill((5, 10, 22, 180))
        target.blit(veil, (0, 0))
        glow(target, (480, 192), PURPLE, 220)
        self.text(target, 'PROTOCOLO 01   /   INSTALACIÓN ABANDONADA', (240, 38), MUTED, 12, True)
        self.text(target, 'NEON FIGHTER', (242, 84), (42, 62, 94), 56, True)
        self.text(target, 'NEON FIGHTER', (240, 82), WHITE, 56, True)
        self.text(target, 'M A X', (240, 117), CYAN, 42, True)
        self.ui_line(target, PURPLE, (190, 140), (290, 140))
        self.text(target, 'DESPIERTA. LUCHA. SOBREVIVE.', (240, 155), MUTED, 14, True)
        self.button(target, 'play', 'INICIAR PROTOCOLO  >', (143, 178, 194, 30), mouse, True)
        self.button(target, 'training', 'ENTRENAMIENTO', (145, 217, 125, 22), mouse)
        self.button(target, 'quit', 'SALIR', (280, 217, 65, 22), mouse)
        self.text(target, 'ENTER para jugar   ·   Pixel art original / sin conexión', (240, 258), MUTED, 12, True)

    def _crosshair(self, target, mouse):
        x, y = mouse
        for start, end in (((x - 5, y), (x - 2, y)), ((x + 2, y), (x + 5, y)),
                           ((x, y - 5), (x, y - 2)), ((x, y + 2), (x, y + 5))):
            self.ui_line(target, CYAN, start, end)
