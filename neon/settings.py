"""Shared display, arena and color constants."""

import pygame

INTERNAL_SIZE = (480, 270)
WINDOW_SIZE = (960, 540)
FPS = 60
BASE_SWORD_DAMAGE = 22
COMBO_DAMAGE_MULTIPLIERS = (1.0, 1.15, 1.30, 2.10)
ARENA = pygame.Rect(24, 62, 432, 182)
CYAN = (86, 235, 237)
PURPLE = (169, 113, 242)
ORANGE = (255, 154, 87)
WHITE = (222, 240, 245)
MUTED = (111, 143, 163)
INK = (9, 15, 27)


def clamp_position(pos, radius=8):
    pos.x = max(ARENA.left + radius, min(ARENA.right - radius, pos.x))
    pos.y = max(ARENA.top + radius, min(ARENA.bottom - radius, pos.y))
