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
    'drone': EnemyStats(58, 12, 39, 0.42, 1.05),
    'fast': EnemyStats(44, 8, 49, 0.23, 0.64),
    'ranged': EnemyStats(48, 10, 35, 0.60, 1.60),
    'sentinel': EnemyStats(520, 24, 28, 0.65, 1.25, 48, 36, 17),
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
BOSS_ENERGY_WINDUP = 0.90
BOSS_ENERGY_COOLDOWN = 1.80
BOSS_ENERGY_DAMAGE = 18
BOSS_RECOVERY = 0.55
BOSS_ENERGY_SPREAD = (-16, 0, 16)
BOSS_DESTRUCTION_TIME = 0.85


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
