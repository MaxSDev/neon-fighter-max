"""Exercise real input handlers and rendering with SDL's headless driver."""

import os
import unittest

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame

from neon.app import Game


class AppTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.frame(1 / 60, [], pygame.Vector2(), (320, 150))

    def tearDown(self):
        pygame.quit()

    def key(self, key, movement=None):
        self.game.frame(1 / 60, [pygame.event.Event(pygame.KEYDOWN, key=key)],
                        movement or pygame.Vector2(), (320, 150))

    def test_keyboard_mouse_pause_skip_and_restart(self):
        self.key(pygame.K_RETURN)
        self.assertEqual(self.game.world.stage, 'tutorial')
        before = self.game.world.player.pos.copy()
        self.game.frame(0.1, [], pygame.Vector2(1, 0), (320, 150))
        self.assertGreater(self.game.world.player.pos.x, before.x)
        self.key(pygame.K_j)
        self.assertGreater(self.game.world.player.attack_left, 0)
        self.key(pygame.K_LSHIFT, pygame.Vector2(1, 0))
        self.assertGreater(self.game.world.player.dash_left, 0)
        self.key(pygame.K_ESCAPE)
        self.assertTrue(self.game.world.paused)
        self.key(pygame.K_ESCAPE)
        skip = self.game.renderer.buttons['skip'].center
        self.game.frame(1 / 60, [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)], pygame.Vector2(), skip)
        self.assertEqual(self.game.world.stage, 'arena')
        self.assertEqual(self.game.world.player.attack_left, 0)
        self.game.world.player.hp = 0
        self.game.frame(1 / 60, [], pygame.Vector2(), (320, 150))
        self.assertEqual(self.game.world.stage, 'defeat')
        self.key(pygame.K_r)
        self.assertEqual(self.game.world.stage, 'tutorial')

    def test_all_screens_and_finisher_render(self):
        for stage in ('menu', 'tutorial', 'arena', 'victory', 'defeat'):
            self.game.world.stage = stage
            self.game.renderer.draw(self.game.canvas, self.game.world, (300, 160), 1)
            pygame.transform.scale(self.game.canvas, (960, 540), self.game.window)
            self.game.renderer.draw_ui(self.game.window, self.game.world, (300, 160), 1)
        self.game.world.start()
        self.game.world.player.combo = 3
        self.game.world.player.combo_window = 1
        self.game.world.attack(pygame.Vector2(1, 0))
        self.game.world.enemies[0].pos = self.game.world.player.pos + pygame.Vector2(27, 0)
        for _ in range(30):
            self.game.frame(1 / 120, [], pygame.Vector2(), (320, 158))
            if self.game.world.impact > 0:
                break
        self.assertGreater(self.game.world.impact, 0)
        self.assertTrue(self.game.world.particles)
        self.game.world.toggle_pause()
        self.game.frame(1 / 60, [], pygame.Vector2(), (320, 150))
        self.assertIn('resume', self.game.renderer.buttons)

    def test_focus_loss_pauses_and_quit_closes(self):
        self.game.world.start()
        self.game.frame(1 / 60, [pygame.event.Event(pygame.WINDOWFOCUSLOST)], pygame.Vector2(), (320, 150))
        self.assertTrue(self.game.world.paused)
        self.game.frame(1 / 60, [pygame.event.Event(pygame.QUIT)], pygame.Vector2(), (320, 150))
        self.assertFalse(self.game.running)

    def test_native_text_fits_footer_and_camera_does_not_move_hud(self):
        renderer = self.game.renderer
        footer = renderer.text(self.game.window,
            'WASD mover   /   RATÓN apuntar   /   CLIC o J atacar   /   SHIFT esquivar   /   ESC pausa',
            (240, 262), size=12, center=True)
        self.assertGreaterEqual(footer.left, 0)
        self.assertLessEqual(footer.right, 960)
        self.assertLessEqual(footer.bottom, 540)
        self.game.world.start()
        self.game.frame(0, [], pygame.Vector2(), (320, 150))
        before = pygame.image.tobytes(self.game.window.subsurface((0, 0, 960, 60)), 'RGB')
        self.game.world.shake = 2.8
        self.game.frame(0, [], pygame.Vector2(), (320, 150))
        after = pygame.image.tobytes(self.game.window.subsurface((0, 0, 960, 60)), 'RGB')
        self.assertEqual(before, after)

    def test_impact_has_no_fixed_slash_at_screen_center(self):
        from neon.settings import WHITE

        world = self.game.world
        world.start()
        world.player.pos.update(100, 100)
        world.impact = 0.065
        self.game.renderer.draw(self.game.canvas, world, (300, 160), 1)
        # This pixel was on the old hardcoded diagonal, unrelated to contact.
        self.assertNotEqual(self.game.canvas.get_at((200, 173))[:3], WHITE)

    def test_new_enemies_telegraphs_and_boss_health_bar_render(self):
        from neon.enemies import create_enemy
        from neon.settings import ORANGE

        world = self.game.world
        world.stage = 'arena'
        world.enemies = [create_enemy(pygame.Vector2(pos), kind) for pos, kind in (
            ((100, 140), 'fast'), ((390, 120), 'ranged'), ((350, 190), 'sentinel'))]
        boss = world.enemies[-1]
        for attack_kind in ('melee', 'energy'):
            boss.attack_kind = attack_kind
            boss.windup = 0.3
            self.game.frame(0, [], pygame.Vector2(), (320, 150))
            self.assertEqual(self.game.window.get_at((300, 100))[:3], ORANGE)


if __name__ == '__main__':
    unittest.main()
