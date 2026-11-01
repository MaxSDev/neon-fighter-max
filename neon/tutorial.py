"""Small contextual training objectives and a harmless energy emitter."""

from dataclasses import dataclass, field

from pygame import Vector2

from neon.projectiles import Projectile


@dataclass
class Tutorial:
    step: str = 'movement'
    distance: float = 0
    chain: int = 0
    confirmation: float = 0
    age: float = 0
    dashes: int = 0
    evaded: bool = False
    emitter: Vector2 = field(default_factory=lambda: Vector2(410, 155))
    aim: Vector2 = field(default_factory=lambda: Vector2(-1, 0))
    warning: float = 0
    shot_timer: float = 0.6

    @property
    def message(self):
        if self.confirmation > 0:
            return '¡COMBO CONFIRMADO!'
        return {
            'movement': 'Usa W A S D para moverte',
            'attack': 'Click izquierdo o J para atacar',
            'combo': 'Encadena 4 ataques para ejecutar un golpe poderoso',
            'dodge': 'Presiona SHIFT para esquivar',
            'complete': 'ENTRENAMIENTO COMPLETADO',
        }[self.step]

    def advance(self, step):
        self.step = step
        self.age = 0

    def register_hit(self, combo):
        if self.step == 'attack':
            self.advance('combo')
            self.chain = 0
            return True
        if self.step == 'combo' and self.confirmation == 0:
            self.chain = combo if combo == self.chain + 1 else (1 if combo == 1 else 0)
            if self.chain == 4:
                self.confirmation = 0.85
        return False

    def update(self, dt, moved, player):
        self.age += dt
        if self.step == 'movement':
            self.distance += moved
            if self.distance >= 80:
                self.advance('attack')
        elif self.step == 'combo' and self.confirmation > 0:
            self.confirmation = max(0, self.confirmation - dt)
            if self.confirmation == 0:
                self.advance('dodge')
        elif self.step == 'dodge':
            # Two actual dodges also suffice: no precision gate can trap training.
            if self.evaded or (self.dashes >= 2 and self.age >= 2.5):
                self.advance('complete')
                self.warning = 0
                return None
            if self.warning > 0:
                self.warning = max(0, self.warning - dt)
                if self.warning == 0:
                    self.shot_timer = 1.5
                    return Projectile(self.emitter.copy(), self.aim * 75, 0, 5, 4, training=True)
            else:
                self.shot_timer = max(0, self.shot_timer - dt)
                if self.shot_timer == 0:
                    target = player.pos + Vector2(0, -10) - self.emitter
                    self.aim = target.normalize() if target.length_squared() else Vector2(-1, 0)
                    self.warning = 0.9
        return None

    @property
    def finished(self):
        return self.step == 'complete' and self.age >= 1.4
