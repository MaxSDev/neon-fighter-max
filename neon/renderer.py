"""Cached pixel art, combat effects, HUD and Spanish game screens."""

import math

import pygame

from neon.art import glow, make_background, make_robot, sword_polygon
from neon.settings import CYAN, INK, MUTED, ORANGE, PURPLE, WHITE
from neon.weapon import sword_pose


class Renderer:
    def __init__(self):
        self.background = make_background()
        self.scene = pygame.Surface((480, 270))
        self.fonts = {size: pygame.font.Font(None, size * 2) for size in (12, 14, 16, 18, 22, 28, 42, 56)}
        self.effects = pygame.Surface((480, 270), pygame.SRCALPHA)
        self.camera_offset = (0, 0)
        self.sprites = {(kind, frame, flip, flash): make_robot(kind, frame, flip, flash)
                        for kind in ('player', 'drone', 'brute', 'dummy')
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
        actors = [(enemy.pos.y, enemy, enemy.kind) for enemy in world.enemies]
        if world.stage != 'menu':
            actors.append((world.player.pos.y, world.player, 'player'))
        for _, actor, kind in sorted(actors, key=lambda item: item[0]):
            self._actor(self.scene, actor, kind)
        if world.stage != 'menu':
            self._sword(self.scene, world.player)
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

    def draw_ui(self, target, world, mouse, time):
        """Draw crisp text after integer scaling; coordinates stay in world units."""
        self.buttons.clear()
        offset = pygame.Vector2(self.camera_offset)
        for label in world.damage_texts:
            self.text(target, label.text, label.pos + offset, label.color, 16, True)
        for enemy in world.enemies:
            if enemy.kind == 'dummy':
                self.text(target, 'DRON DE PRÁCTICA', enemy.pos + offset + (0, -34), WHITE, 12, True)
            elif enemy.windup > 0:
                self.text(target, '!', enemy.pos + offset + (0, -34), ORANGE, 18, True)
        if world.stage == 'menu':
            self._menu(target, mouse, time)
        else:
            self._hud(target, world)
            if world.paused:
                self._overlay(target, 'SISTEMA EN PAUSA', 'Respira. La arena puede esperar.')
                self.button(target, 'resume', 'CONTINUAR  /  ESC', (156, 151, 168, 28), mouse, True)
                self.button(target, 'menu', 'VOLVER AL INICIO', (156, 188, 168, 25), mouse)
            elif world.stage in ('victory', 'defeat'):
                victory = world.stage == 'victory'
                self._overlay(target, 'SECTOR LIBERADO' if victory else 'SEÑAL PERDIDA',
                              'Tres oleadas. Una máquina imparable.' if victory else 'Tu núcleo se apagó. Vuelve a intentarlo.')
                self.text(target, f'{world.kills} bajas  /  {int(world.elapsed)} s', (240, 142), MUTED, 16, True)
                self.button(target, 'restart', 'REINICIAR  /  R', (156, 166, 168, 28), mouse, True)
                self.button(target, 'menu', 'VOLVER AL INICIO', (156, 204, 168, 25), mouse)
            else:
                if world.stage == 'tutorial':
                    self.ui_rect(target, INK, (111, 39, 258, 20))
                    self.text(target, f'CALIBRACIÓN  /  Conecta 4 golpes: {world.tutorial_hits}/4', (240, 49), WHITE, 14, True)
                    self.button(target, 'skip', 'OMITIR  >', (377, 30, 88, 19), mouse)
                elif world.intermission > 0:
                    self.text(target, f'OLEADA {world.wave + 1}  /  {math.ceil(world.intermission)}', (240, 116), CYAN, 28, True)
                    self.text(target, 'Núcleo estabilizado · Prepárate', (240, 137), WHITE, 14, True)
                self._crosshair(target, mouse)
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
        pygame.draw.ellipse(target, (10, 17, 26), (x - 10, y - 3, 20, 7))
        if player and actor.dash_left > 0:
            for index in (3, 2, 1):
                pos = actor.pos - actor.dash_direction * index * 7
                pygame.draw.ellipse(target, (25, 66, 82), (pos.x - 7, pos.y - 10, 14, 10), 1)
        if not player and actor.windup > 0:
            pygame.draw.circle(target, ORANGE, (x, y), 24, 1)
            pygame.draw.circle(target, (130, 70, 50), (x, y), max(3, int(24 * actor.windup / 0.42)), 1)
        age = actor.walk_time if player else actor.age * 8
        moving = actor.moving if player else kind != 'dummy' and actor.windup == 0 and actor.stun == 0
        frame = (1 if math.sin(age) > 0 else -1) if moving else 0
        flash = (actor.invulnerable > 0 and int(actor.invulnerable * 22) % 2 == 0) if player else actor.flash > 0
        sprite = self.sprites[kind, frame, actor.facing.x < 0, flash]
        bob = -1 if moving and frame == 1 else 0
        target.blit(sprite, (x - 12, y - 24 + bob))
        if not player and kind != 'dummy' and actor.hp < actor.max_hp:
            pygame.draw.rect(target, (15, 19, 30), (x - 11, y - 29, 22, 3))
            pygame.draw.rect(target, ORANGE, (x - 11, y - 29, max(1, int(22 * actor.hp / actor.max_hp)), 2))
        if kind == 'dummy':
            pygame.draw.circle(target, PURPLE, (x, y + 1), 14, 1)

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
        self.text(target, 'ENTRENAMIENTO' if world.stage == 'tutorial' else f'OLEADA  {world.wave}/3', (372, 9), WHITE, 16)
        self.ui_rect(target, INK, (0, 254, 480, 16))
        self.text(target, 'WASD mover   /   RATÓN apuntar   /   CLIC o J atacar   /   SHIFT esquivar   /   ESC pausa', (240, 262), MUTED, 12, True)

    def _overlay(self, target, title, subtitle):
        veil = pygame.Surface(target.get_size(), pygame.SRCALPHA)
        veil.fill((5, 10, 22, 215))
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
        self.button(target, 'quit', 'SALIR', (191, 217, 98, 22), mouse)
        self.text(target, 'ENTER para jugar   ·   Pixel art original / sin conexión', (240, 258), MUTED, 12, True)

    def _crosshair(self, target, mouse):
        x, y = mouse
        for start, end in (((x - 5, y), (x - 2, y)), ((x + 2, y), (x + 5, y)),
                           ((x, y - 5), (x, y - 2)), ((x, y + 2), (x, y + 5))):
            self.ui_line(target, CYAN, start, end)
