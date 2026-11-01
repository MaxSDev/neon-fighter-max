"""Small, announced overload hazards; shared by boss AI and presentation."""

from dataclasses import dataclass

from pygame import Vector2

from neon.balance import (BOSS_ENERGY_SPREAD, OVERLOAD_FAN_ANGLES, OVERLOAD_RADIAL_ANGLES,
                          OVERLOAD_AREA_RADIUS, OVERLOAD_AREA_DAMAGE)
from neon.settings import ARENA


def projectile_angles(attack_kind):
    return {'energy': BOSS_ENERGY_SPREAD, 'fan': OVERLOAD_FAN_ANGLES,
            'radial': OVERLOAD_RADIAL_ANGLES}.get(attack_kind, ())


@dataclass
class EnergyZone:
    pos: Vector2
    warning: float
    radius: float = OVERLOAD_AREA_RADIUS
    damage: int = OVERLOAD_AREA_DAMAGE
    resolved: bool = False
    flash_left: float = 0.25
    just_resolved: bool = False

    @property
    def alive(self):
        return not self.resolved or self.flash_left > 0

    def update(self, dt, player):
        self.just_resolved = False
        if self.resolved:
            self.flash_left = max(0, self.flash_left - dt)
            return False
        self.warning = max(0, self.warning - dt)
        if self.warning == 0:
            self.resolved = self.just_resolved = True
            return self.pos.distance_squared_to(player.pos) <= (self.radius + 8) ** 2 and player.hurt(self.damage)
        return False


def prepare_zones(player_pos, direction, warning):
    """At most two fixed marks, with space left elsewhere in the arena."""
    side = Vector2(-direction.y, direction.x)
    positions = []
    margin = OVERLOAD_AREA_RADIUS + 4
    for candidate in (player_pos.copy(), player_pos + side * 64):
        candidate.x = max(ARENA.left + margin, min(ARENA.right - margin, candidate.x))
        candidate.y = max(ARENA.top + margin, min(ARENA.bottom - margin, candidate.y))
        if all(candidate.distance_to(other) >= OVERLOAD_AREA_RADIUS * 2 for other in positions):
            positions.append(candidate)
    return [EnergyZone(pos, warning) for pos in positions]
