"""Save deterministic rendering fixtures, not evidence of manual play."""

import os
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame

from neon.app import Game
from neon.world import World
from neon.enemies import create_enemy


def capture_sequence(game, output):
    """Contact sheet of actual simulation poses, including attack recovery."""
    sheet = pygame.Surface((1400, 1120))
    sheet.fill((9, 15, 27))
    font = pygame.font.Font(None, 24)
    labels = ('Preparación', 'Golpe inicial', 'Golpe central', 'Recuperación', 'Reposo')
    for combo in range(1, 5):
        world = World(seed=4)
        world.start()
        world.scene_age = 1
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
    game = Game(preferences_path=None)

    def save(name):
        if game.world.stage not in ('boss_dying', 'player_dying'):
            game.world.scene_age = max(1, game.world.scene_age)
        game.renderer.draw(game.canvas, game.world, (345, 153), 2)
        pygame.transform.scale(game.canvas, (960, 540), game.window)
        game.renderer.draw_ui(game.window, game.world, (345, 153), 2, game.audio, game.menu_page)
        pygame.image.save(game.window, output / f'{name}.png')

    try:
        save('menu')
        game.menu_page = 'settings'
        save('settings')
        game.menu_page = 'main'
        game.world.start()
        save('tutorial')
        for step in ('attack', 'combo', 'dodge', 'complete'):
            game.world.tutorial.step = step
            if step == 'dodge':
                game.world.tutorial.warning = 0.5
                game.world.tutorial.aim = (game.world.player.pos + pygame.Vector2(0, -10) - game.world.tutorial.emitter).normalize()
            save(f'training-{step}')
        game.world.practice_mode = True
        game.world.tutorial.age = 2
        save('practice-choice')
        game.world.skip_tutorial()
        game.world.wave = 2
        game.world.spawn_wave()
        game.world.spawn_queue.clear()
        game.world.enemies = [create_enemy(pygame.Vector2(pos), kind) for pos, kind in (
            ((110, 130), 'drone'), ((365, 125), 'ranged'), ((170, 205), 'fast'),
            ((390, 192), 'drone'), ((270, 98), 'ranged'))]
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
        game.world.kills = 23
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
        game.world.skip_tutorial()
        game.world.spawn_wave()
        game.world.update(0.25, pygame.Vector2())
        save('spawn-warning')
        game.world = World(seed=4)
        game.world.stage = 'arena'
        game.world.wave = 2
        shooter = create_enemy(pygame.Vector2(350, 155), 'ranged')
        shooter.cooldown = 0
        shooter.update(0.01, game.world.player)
        game.world.enemies = [shooter]
        save('ranged-warning')
        for _ in range(100):
            shooter.update(1 / 120, game.world.player)
            if shooter.shots:
                break
        game.world.projectiles = shooter.shots[:]
        for shot in game.world.projectiles:
            shot.update(0.25, game.world.player, game.world.player.pos)
        save('ranged-shot')
        game.world.projectiles.clear()
        game.world.wave = 3
        game.world.boss_announced = game.world.boss_spawned = True
        boss = create_enemy(pygame.Vector2(350, 170), 'sentinel')
        boss.cooldown = 0
        boss.update(0.01, game.world.player)
        game.world.enemies = [boss]
        save('sentinel-energy')
        boss = create_enemy(game.world.player.pos + pygame.Vector2(30, 0), 'sentinel')
        boss.cooldown = 0
        boss.update(0.01, game.world.player)
        game.world.enemies = [boss]
        save('sentinel-melee')
        boss.hp = 0
        game.world.update(1 / 120, pygame.Vector2())
        game.world.update(0.25, pygame.Vector2())
        save('sentinel-destruction')
        for age, name in ((0.9, 'sentinel-core-failing'), (1.45, 'sentinel-explosion'),
                          (2.1, 'sentinel-aftermath'), (2.9, 'sentinel-victory-fade')):
            while game.world.sequence_elapsed < age:
                game.world.update(min(1 / 60, age - game.world.sequence_elapsed), pygame.Vector2())
            save(name)
        game.world = World(seed=4)
        game.world.start()
        game.world.skip_tutorial()
        game.world.player.hp = 0
        game.world.update(1 / 120, pygame.Vector2())
        for age, name in ((0.65, 'player-collapse'), (1.4, 'player-fade')):
            while game.world.sequence_elapsed < age:
                game.world.update(min(1 / 60, age - game.world.sequence_elapsed), pygame.Vector2())
            save(name)
        game.world = World(seed=4)
        game.world.stage = 'arena'
        game.world.wave = 3
        game.world.boss_announced = game.world.boss_spawned = True
        boss = create_enemy(pygame.Vector2(320, 170), 'sentinel')
        boss.hp = boss.max_hp // 2
        game.world.enemies = [boss]
        game.world.update(1 / 120, pygame.Vector2())
        save('sentinel-overload')
        for index, pattern in enumerate(('fan', 'area', 'radial', 'pressure')):
            game.world = World(seed=4)
            game.world.stage = 'arena'
            game.world.wave = 3
            game.world.player.pos.update(180, 165)
            game.world.boss_announced = game.world.boss_spawned = True
            boss = create_enemy(pygame.Vector2(210 if pattern == 'pressure' else 320, 165), 'sentinel')
            boss.hp = boss.max_hp // 2
            boss.phase = 2
            boss.phase_announced = True
            boss.pattern_index = index
            boss.cooldown = 0
            game.world.enemies = [boss]
            game.world.update(1 / 120, pygame.Vector2())
            save(f'sentinel-{pattern}')
            if pattern == 'area':
                for _ in range(140):
                    game.world.update(1 / 120, pygame.Vector2())
                save('sentinel-area-impact')
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
    print(f'Render fixtures available: {len(list(output.glob("*.png")))} PNG files in {output}')


if __name__ == '__main__':
    main()
