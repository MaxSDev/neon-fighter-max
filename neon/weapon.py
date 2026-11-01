"""Shared hand-anchored sword poses and swept blade collision geometry."""

from dataclasses import dataclass
import math

from pygame import Vector2


@dataclass(frozen=True)
class SwordPose:
    hand: Vector2
    heel: Vector2
    tip: Vector2
    angle: float
    phase: str


def attack_timing(finisher):
    # Duration remains compatible with the existing combo and input buffer.
    return (0.06, 0.15, 0.11) if finisher else (0.045, 0.145, 0.07)


def smoothstep(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)


def sword_pose(player, elapsed=None, position=None):
    position = player.pos if position is None else position
    # A fixed hand on the visible arm: aim never translates it around the torso.
    hand = position + Vector2(6 if player.facing.x >= 0 else -6, -10)
    base = math.atan2(player.facing.y, player.facing.x)
    rest = 0.45
    offset, phase = rest, 'idle'
    extension = 0
    finisher = player.combo == 4
    if elapsed is not None or player.attack_left > 0:
        elapsed = player.attack_duration - player.attack_left if elapsed is None else elapsed
        windup, strike, recovery = attack_timing(finisher)
        spread = 1.48 if finisher else 1.13
        reverse = -1 if player.combo % 2 == 0 else 1
        start, end = -spread * reverse, spread * reverse
        if elapsed < windup:
            phase = 'windup'
            offset = rest + (start - rest) * smoothstep(elapsed / windup)
            extension = smoothstep(elapsed / windup)
        elif elapsed < windup + strike:
            phase = 'strike'
            offset = start + (end - start) * smoothstep((elapsed - windup) / strike)
            extension = 1
        else:
            phase = 'recovery'
            offset = end + (rest - end) * smoothstep((elapsed - windup - strike) / recovery)
            extension = 1 - smoothstep((elapsed - windup - strike) / recovery)
    angle = base + offset
    direction = Vector2(math.cos(angle), math.sin(angle))
    reach = 39 + 9 * extension if finisher else 39
    return SwordPose(hand, hand + direction * 5, hand + direction * reach, angle, phase)


def sword_contact(player, center, radius):
    """Return contact on the blade swept this simulation step, or None.

    Sample at most four degrees apart. With a 48px blade the maximum chord
    deviation is under 0.03px, well below the visible blade's 2px half-width.
    The target center is in visual world coordinates (body, rather than feet).
    """
    if player.attack_left <= 0:
        return None
    windup, strike, _ = attack_timing(player.combo == 4)
    elapsed = player.attack_duration - player.attack_left
    start = max(player.previous_attack_elapsed, windup)
    end = min(elapsed, windup + strike)
    if start > end or elapsed < windup:
        return None
    spread = 1.48 if player.combo == 4 else 1.13
    # Smoothstep's maximum derivative is 1.5; bound spacing even near mid-swing.
    steps = max(1, math.ceil((end - start) / strike * 2 * spread * 1.5 / math.radians(4)))
    for index in range(steps + 1):
        fraction = index / steps
        sample_time = start + (end - start) * fraction
        frame_time = elapsed - player.previous_attack_elapsed
        movement_fraction = (sample_time - player.previous_attack_elapsed) / frame_time if frame_time > 0 else 1
        position = player.previous_pos.lerp(player.pos, max(0, min(1, movement_fraction)))
        pose = sword_pose(player, sample_time, position)
        blade = pose.tip - pose.heel
        along = max(0, min(1, (center - pose.heel).dot(blade) / blade.length_squared()))
        closest = pose.heel + blade * along
        if closest.distance_squared_to(center) <= (radius + 2) ** 2:
            return closest
    return None
