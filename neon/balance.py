"""Central tuning for enemies, wave composition, spawning and projectiles."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnemyStats:
    hp: int
    damage: int
    speed: float
    windup: float
    cooldown: float
    reach: float = 28
    trigger: float = 23
    radius: float = 9


ENEMIES = {
    'drone': EnemyStats(58, 12, 39, 0.36, 0.90),
    'fast': EnemyStats(44, 8, 49, 0.20, 0.54, 30, 26),
    'ranged': EnemyStats(48, 10, 35, 0.54, 1.36),
    'sentinel': EnemyStats(676, 24, 31.5, 0.60, 1.10, 48, 36, 17),
    'brute': EnemyStats(100, 18, 30, 0.42, 1.05),  # Retained for old art fixtures.
    'dummy': EnemyStats(999, 0, 0, 0.42, 1.05),
}

# Order interleaves roles while preserving the requested totals.
WAVES = (
    ('drone',) * 5,
    ('drone', 'drone', 'ranged', 'drone', 'drone', 'ranged', 'drone'),
    ('drone', 'fast', 'ranged', 'drone', 'fast', 'drone', 'ranged', 'drone', 'fast', 'drone'),
)
MAX_ACTIVE_ENEMIES = 5
SPAWN_INTERVAL = 0.85
SPAWN_WARNING = 0.70
SPAWN_PLAYER_DISTANCE = 95
WAVE_BREAK = 2.0
WAVE_HEAL = 15
RANGED_NEAR = 104
RANGED_FAR = 136
BOSS_ENERGY_WINDUP = 0.82
BOSS_ENERGY_COOLDOWN = 1.58
BOSS_ENERGY_DAMAGE = 18
BOSS_RECOVERY = 0.49
BOSS_ENERGY_SPREAD = (-16, 0, 16)
BOSS_DESTRUCTION_TIME = 3.10
BOSS_EXPLOSION_AT = 1.40
PLAYER_DEFEAT_TIME = 1.75
ENDING_FADE_TIME = 0.50


@dataclass(frozen=True)
class ProjectileStats:
    speed: float
    lifetime: float
    radius: int


PROJECTILES = {
    'ranged': ProjectileStats(100, 3.2, 3),
    'sentinel': ProjectileStats(125, 3.0, 5),
}
MAX_PROJECTILES = 32
RANGED_FIRE_GAP = 0.24
OVERLOAD_THRESHOLD = 0.50
OVERLOAD_TRANSITION = 1.15
OVERLOAD_NOTICE_TIME = 2.0
OVERLOAD_SPEED_MULTIPLIER = 1.12
OVERLOAD_MAX_PROJECTILES = 16
OVERLOAD_ORDER = ('fan', 'area', 'radial', 'pressure')
OVERLOAD_CYCLES = (OVERLOAD_ORDER, ('radial', 'area', 'fan', 'pressure'))
OVERLOAD_FAN_ANGLES = (-36, -18, 0, 18, 36)
# A 120-degree opening centered on locked aim remains free of radial bullets.
OVERLOAD_RADIAL_ANGLES = tuple(range(60, 301, 30))
OVERLOAD_AREA_RADIUS = 26
OVERLOAD_AREA_DAMAGE = 18


@dataclass(frozen=True)
class BossPattern:
    windup: float
    recovery: float
    cooldown: float


OVERLOAD_PATTERNS = {
    'fan': BossPattern(0.85, 0.55, 1.35),
    'radial': BossPattern(1.05, 0.65, 1.55),
    'area': BossPattern(1.10, 0.65, 1.50),
    'pressure': BossPattern(0.52, 0.43, 0.95),
}


def overload_pattern(index):
    cycle, slot = divmod(index, len(OVERLOAD_ORDER))
    return OVERLOAD_CYCLES[cycle % len(OVERLOAD_CYCLES)][slot]
