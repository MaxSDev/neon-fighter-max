"""Save deterministic rendering fixtures, not evidence of manual play."""

import os
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame

from neon.app import Game
from neon.world import World


def capture_sequence(game, output):
    """Contact sheet of actual simulation poses, including attack recovery."""
    sheet = pygame.Surface((1400, 1120))
    sheet.fill((9, 15, 27))
    font = pygame.font.Font(None, 24)
    labels = ('Preparación', 'Golpe inicial', 'Golpe central', 'Recuperación', 'Reposo')
    for combo in range(1, 5):
        world = World(seed=4)
        world.start()
        world.enemies.clear()
        world.player.combo = combo - 1
        world.player.combo_window = 1
        world.attack(pygame.Vector2(1, 0))
        elapsed = 0
        duration = world.player.attack_duration
        for column, fraction in enumerate((0.10, 0.32, 0.50, 0.85, 1.05)):
            while elapsed < duration * fraction:
                step = min(1 / 120, duration * fraction - elapsed)
                world.update(step, pygame.Vector2())
                elapsed += step
            game.renderer.draw(game.canvas, world, (345, 153), elapsed)
            crop = game.canvas.subsurface((170, 78, 140, 124))
            x, y = column * 280, (combo - 1) * 280
            sheet.blit(pygame.transform.scale(crop, (280, 248)), (x, y + 28))
            caption = font.render(f'{combo} / {labels[column]}', False, (222, 240, 245))
            sheet.blit(caption, caption.get_rect(center=(x + 140, y + 14)))
    pygame.image.save(sheet, output / 'combat-sequence.png')


def main():
    output = Path(__file__).resolve().parents[1] / 'docs' / 'screenshots'
    output.mkdir(parents=True, exist_ok=True)
    game = Game()

    def save(name):
        game.renderer.draw(game.canvas, game.world, (345, 153), 2)
        pygame.transform.scale(game.canvas, (960, 540), game.window)
        game.renderer.draw_ui(game.window, game.world, (345, 153), 2)
        pygame.image.save(game.window, output / f'{name}.png')

    try:
        save('menu')
        game.world.start()
        save('tutorial')
        game.world.skip_tutorial()
        game.world.wave = 2
        game.world.spawn_wave()
        game.world.intermission = 0
        save('arena')
        game.world.player.combo = 3
        game.world.player.combo_window = 1
        game.world.attack(pygame.Vector2(1, 0))
        game.world.enemies[0].pos = game.world.player.pos + pygame.Vector2(27, 0)
        for _ in range(30):
            game.world.update(1 / 120, pygame.Vector2())
            if game.world.impacts:
                break
        save('finisher')
        game.world.toggle_pause()
        save('pause')
        game.world.paused = False
        preview_enemies = game.world.enemies[:]
        game.world.enemies.clear()
        game.world.particles.clear()
        game.world.damage_texts.clear()
        game.world.impacts.clear()
        game.world.player.attack_left = 0
        game.world.player.combo = 0
        game.world.impact = 0
        game.world.shake = 0
        game.world.kills = 18
        game.world.elapsed = 76
        game.world.stage = 'victory'
        save('victory')
        game.world.enemies = preview_enemies
        game.world.player.hp = 0
        game.world.kills = 12
        game.world.stage = 'defeat'
        save('defeat')
        game.world = World(seed=4)
        game.world.start()
        game.world.enemies.clear()
        game.world.player.combo = 3
        game.world.player.combo_window = 1
        game.world.attack(pygame.Vector2(1, 0))
        game.world.update(0.13, pygame.Vector2())
        save('finisher-miss')
        capture_sequence(game, output)
    finally:
        pygame.quit()
    print(f'Saved 9 render fixtures to {output}')


if __name__ == '__main__':
    main()
