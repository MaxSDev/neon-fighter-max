"""Fixed-direction energy shots with swept relative-motion collision."""

from dataclasses import dataclass

from pygame import Vector2

from neon.balance import PROJECTILES
from neon.settings import ARENA


@dataclass
class Projectile:
    pos: Vector2
    velocity: Vector2
    damage: int
    radius: int
    life: float
    alive: bool = True

    @classmethod
    def launch(cls, pos, direction, damage, kind):
        stats = PROJECTILES[kind]
        return cls(pos.copy(), direction.normalize() * stats.speed, damage, stats.radius, stats.lifetime)

    def update(self, dt, player, previous_player_pos):
        if not self.alive or self.life <= 0:
            self.alive = False
            return False
        travel = min(dt, max(0, self.life))
        start = self.pos - (previous_player_pos + Vector2(0, -10))
        self.pos += self.velocity * travel
        # Ignore player motion after this projectile's remaining lifetime.
        portion = travel / dt if dt > 0 else 0
        player_end = Vector2(previous_player_pos).lerp(player.pos, portion)
        end = self.pos - (player_end + Vector2(0, -10))
        segment = end - start
        fraction = max(0, min(1, -start.dot(segment) / segment.length_squared())) if segment.length_squared() else 0
        closest = start + segment * fraction
        self.life -= dt
        if closest.length_squared() <= (8 + self.radius) ** 2:
            # Contact consumes the shot even if the player is invulnerable.
            self.alive = False
            return player.hurt(self.damage)
        if self.life <= 0 or not ARENA.collidepoint(self.pos):
            self.alive = False
        return False
