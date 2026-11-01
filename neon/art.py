"""Original procedural pixel art. No downloaded fonts, sprites or textures."""

import math
import random

import pygame

from neon.settings import CYAN, INK, ORANGE, PURPLE


def glow(surface, center, color, radius):
    halo = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for size in range(radius, 1, -3):
        alpha = int(24 * (1 - size / radius))
        pygame.draw.circle(halo, (*color, alpha), (radius, radius), size)
    surface.blit(halo, (center[0] - radius, center[1] - radius))


def make_background():
    rng = random.Random(27)
    surface = pygame.Surface((480, 270))
    surface.fill(INK)
    for y in range(58, 250, 16):
        for x in range(16, 465, 16):
            tone = rng.randrange(19, 27)
            pygame.draw.rect(surface, (tone, tone + 10, tone + 19), (x, y, 15, 15))
            pygame.draw.line(surface, (tone + 5, tone + 15, tone + 24), (x, y), (x + 14, y))
            if rng.random() < 0.22:
                pygame.draw.line(surface, (33, 46, 56), (x + 3, y + 12), (x + 7, y + 12))
    # Inlaid floor circuit and segmented containment ring.
    pygame.draw.ellipse(surface, (32, 54, 67), (126, 99, 228, 117), 1)
    pygame.draw.ellipse(surface, (32, 54, 67), (132, 103, 216, 109), 1)
    pygame.draw.line(surface, (37, 58, 71), (240, 82), (240, 232))
    pygame.draw.line(surface, (37, 58, 71), (96, 157), (384, 157))
    for x in (36, 430):
        pygame.draw.lines(surface, (32, 63, 74), False, [(x, 80), (x + 12, 92), (x + 12, 214), (x, 226)])
    for x in range(20, 461, 22):
        pygame.draw.rect(surface, (34, 43, 64), (x, 43, 20, 17))
        pygame.draw.line(surface, (65, 76, 98), (x + 1, 44), (x + 18, 44))
        pygame.draw.rect(surface, (12, 23, 38), (x + 4, 49, 12, 6))
    for x in (20, 450):
        pygame.draw.rect(surface, (39, 47, 66), (x, 61, 10, 185))
        for y in range(76, 238, 38):
            color = CYAN if x == 20 else PURPLE
            pygame.draw.rect(surface, color, (x + 3, y, 3, 18))
            glow(surface, (x + 5, y + 9), color, 38)
    for x in range(34, 448, 12):
        color = (105, 80, 48) if (x // 12) % 2 else (35, 43, 52)
        pygame.draw.polygon(surface, color, [(x, 246), (x + 5, 246), (x + 1, 251), (x - 4, 251)])
    for x, y in ((44, 68), (400, 68), (43, 221), (410, 220)):
        pygame.draw.rect(surface, (8, 17, 28), (x + 2, y + 4, 25, 12))
        pygame.draw.rect(surface, (42, 55, 72), (x, y, 25, 12))
        pygame.draw.rect(surface, (66, 76, 95), (x + 1, y, 23, 2))
        pygame.draw.rect(surface, (14, 25, 39), (x + 4, y + 4, 17, 5))
        for dx in (6, 10, 14, 18):
            pygame.draw.line(surface, (76, 99, 113), (x + dx, y + 5), (x + dx, y + 7))
        pygame.draw.rect(surface, PURPLE, (x + 2, y + 3, 1, 5))
    # Abandoned terminals sit outside the playable floor.
    for x in (78, 364):
        pygame.draw.rect(surface, (9, 17, 29), (x, 38, 38, 21))
        pygame.draw.rect(surface, (53, 67, 83), (x, 38, 38, 2))
        pygame.draw.rect(surface, (22, 56, 68), (x + 4, 42, 30, 11))
        for row in range(3):
            pygame.draw.rect(surface, (62, 134, 143), (x + 7, 44 + row * 3, 8 + row * 5, 1))
    for _ in range(32):
        x, y = rng.randrange(40, 440), rng.randrange(80, 238)
        pygame.draw.rect(surface, (44, 48, 62), (x, y, rng.randrange(1, 4), 1))
    return surface


# Hand-authored 18 x 25 silhouettes, shaded armor and luminous visors.
ROBOT = (
    '      aaaaaa      ',
    '     abbbbbba     ',
    '    abccccccba    ',
    '    abccccccba    ',
    '    abeeeeeeba    ',
    '    abeeee eba    ',
    '     abbbbba      ',
    '   aaaddddaaa     ',
    '  abbcbbbbcbba    ',
    ' abccbcddcbccba   ',
    ' abbcbbecbbc bba  ',
    ' abbbbbeebbb bba  ',
    '  abbccbbccbbba   ',
    '  abbcddddcbba    ',
    '   abbbbbbbba     ',
    '   aadddddaa      ',
    '   abba abba      ',
    '   abca acba      ',
    '   abca acba      ',
    '   abba abba      ',
    '  abcca accba     ',
    '  aaaa   aaaa     ',
)


def make_robot(kind, frame=0, flipped=False, flash=False):
    colors = {
        'player': {'a': (9, 18, 30), 'b': (57, 87, 113), 'c': (128, 163, 181), 'd': (27, 45, 68), 'e': CYAN},
        'drone': {'a': (20, 15, 30), 'b': (96, 58, 91), 'c': (160, 100, 129), 'd': (49, 31, 57), 'e': ORANGE},
        'brute': {'a': (22, 16, 28), 'b': (115, 72, 64), 'c': (185, 128, 94), 'd': (58, 39, 46), 'e': ORANGE},
        'dummy': {'a': (15, 23, 36), 'b': (77, 72, 113), 'c': (136, 129, 173), 'd': (40, 37, 65), 'e': PURPLE},
    }[kind]
    sprite = pygame.Surface((24, 28), pygame.SRCALPHA)
    for y, row in enumerate(ROBOT):
        for x, code in enumerate(row):
            if code == ' ':
                continue
            shift = 0
            if y >= 16 and frame:
                shift = frame if x < 9 else -frame
            color = (235, 252, 255) if flash else colors[code]
            sprite.set_at((x + 3, y + 2 + shift), color)
    if kind == 'player':
        pygame.draw.line(sprite, PURPLE, (6, 9), (4, 16), 2)
        pygame.draw.line(sprite, (92, 63, 137), (4, 16), (3, 18), 2)
    if kind == 'brute':
        pygame.draw.rect(sprite, colors['c'], (2, 10, 4, 5))
        pygame.draw.rect(sprite, colors['c'], (18, 10, 4, 5))
    return pygame.transform.flip(sprite, flipped, False)


def sword_polygon(origin, angle, reach, width=3):
    direction = pygame.Vector2(math.cos(angle), math.sin(angle))
    side = pygame.Vector2(-direction.y, direction.x)
    origin = pygame.Vector2(origin)
    return [origin + side * width, origin + direction * reach,
            origin - side * width, origin - direction * 4]
