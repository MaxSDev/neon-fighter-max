"""Pygame event loop and fixed 2x presentation."""

import pygame

from neon.renderer import Renderer
from neon.settings import FPS, INTERNAL_SIZE, WINDOW_SIZE
from neon.world import World
from neon.audio import AudioManager
from neon.preferences import DEFAULT_PREFERENCES


class Game:
    def __init__(self, preferences_path=DEFAULT_PREFERENCES):
        pygame.display.init()
        pygame.font.init()
        self.window = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption('NEON FIGHTER MAX')
        self.canvas = pygame.Surface(INTERNAL_SIZE)
        self.renderer = Renderer()
        self.world = World()
        self.audio = AudioManager(preferences_path=preferences_path)
        self.menu_page = 'main'
        self.clock = pygame.time.Clock()
        self.running = True
        self.time = 0
        self.movement = pygame.Vector2()
        pygame.mouse.set_visible(False)

    def action(self, name):
        self.audio.play('button')
        if name in ('play', 'training'):
            self.world.start(practice=name == 'training')
            self.menu_page = 'main'
        elif name == 'restart':
            self.world.start()
            self.world.skip_tutorial()
        elif name in ('skip', 'continue'):
            self.world.skip_tutorial()
        elif name == 'resume':
            self.world.toggle_pause()
        elif name == 'menu':
            self.world = World()
            self.menu_page = 'main'
        elif name == 'settings':
            self.menu_page = 'settings'
        elif name == 'back':
            self.menu_page = 'main'
        elif name == 'quit':
            self.running = False
        elif name == 'mute':
            self.audio.toggle_mute()
        elif name in ('music_down', 'music_up', 'effects_down', 'effects_up'):
            category, direction = name.split('_')
            self.audio.adjust(category, -0.1 if direction == 'down' else 0.1)

    def handle_event(self, event, mouse):
        world = self.world
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.WINDOWFOCUSLOST:
            if world.playing and not world.paused:
                world.toggle_pause()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if world.stage == 'menu':
                    self.menu_page = 'main'
                else:
                    world.toggle_pause()
            elif event.key == pygame.K_RETURN and world.stage == 'menu' and self.menu_page == 'main':
                self.action('play')
            elif event.key == pygame.K_RETURN and world.stage == 'tutorial':
                self.action('skip')
            elif event.key == pygame.K_m:
                self.audio.toggle_mute()
            elif event.key in (pygame.K_F5, pygame.K_F6, pygame.K_F7, pygame.K_F8):
                category = 'music' if event.key in (pygame.K_F5, pygame.K_F6) else 'effects'
                self.audio.adjust(category, -0.1 if event.key in (pygame.K_F5, pygame.K_F7) else 0.1)
            elif event.key == pygame.K_r and world.stage in ('victory', 'defeat'):
                self.action('restart')
            elif event.key == pygame.K_j:
                world.attack(pygame.Vector2(mouse) - world.player.pos)
            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                world.dodge(self.movement)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Buttons are laid out during drawing; an overlay click cannot attack.
            for name, rect in self.renderer.buttons.items():
                if rect.collidepoint(mouse):
                    self.action(name)
                    return
            world.attack(pygame.Vector2(mouse) - world.player.pos)

    def frame(self, dt, events=None, movement=None, mouse=None):
        if mouse is None:
            mouse = tuple(value // 2 for value in pygame.mouse.get_pos())
        if movement is None:
            keys = pygame.key.get_pressed()
            movement = pygame.Vector2(int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
                                      int(keys[pygame.K_s]) - int(keys[pygame.K_w]))
        self.movement = movement
        for event in pygame.event.get() if events is None else events:
            self.handle_event(event, mouse)
        self.world.update(dt, movement, pygame.Vector2(mouse) - self.world.player.pos)
        self.audio.update(dt, self.world)
        if not self.world.paused:
            self.time += dt
        self.renderer.draw(self.canvas, self.world, mouse, self.time)
        # Nearest-neighbor scaling preserves the intentional pixel grid.
        pygame.transform.scale(self.canvas, WINDOW_SIZE, self.window)
        self.renderer.draw_ui(self.window, self.world, mouse, self.time, self.audio, self.menu_page)
        pygame.display.flip()

    def run(self, smoke_test=False):
        frames = 0
        try:
            while self.running:
                dt = min(self.clock.tick(FPS) / 1000, 0.25)
                self.frame(dt)
                frames += 1
                if smoke_test and frames >= 120:
                    break
        finally:
            pygame.mouse.set_visible(True)
            pygame.quit()
        return frames
