"""Fireball — the Little Terror's 'Purple Chaos' projectile.

Drawn procedurally: a bright white-purple core, a soft glow, and a short trail
behind it. Flies straight toward where the player was when it was cast, damages
on contact, and fizzles on walls or after its lifetime.
"""
import math
import pygame

import settings
from game.entities.entity import Entity

CORE = (245, 235, 255)
PURPLE = (170, 70, 230)
GLOW = (120, 40, 190)


class Fireball(Entity):
    def __init__(self, x, y, direction, damage):
        s = settings.FIREBALL_SIZE
        super().__init__(x, y, s, s)
        d = pygame.Vector2(direction)
        self.vel = d.normalize() * settings.FIREBALL_SPEED if d.length() else pygame.Vector2()
        self.damage = damage
        self.life = settings.FIREBALL_LIFETIME
        self.dead = False
        self._t = 0.0
        self._trail = []            # recent positions for the tail

    def update(self, dt):
        self._t += dt
        self._trail.append((self.pos.x, self.pos.y))
        if len(self._trail) > 6:
            self._trail.pop(0)
        self.pos += self.vel * dt
        self.life -= dt
        if self.life <= 0:
            self.dead = True

    def on_hit(self, player):
        player.take_damage(self.damage)

    def draw(self, surface, camera):
        off = camera.offset
        # trail
        for i, (tx, ty) in enumerate(self._trail):
            r = 2 + i
            a = int(30 + i * 20)
            self._blob(surface, tx - off.x, ty - off.y, r, (*GLOW, a))
        cx = self.pos.x - off.x
        cy = self.pos.y - off.y
        flick = 1.0 + 0.15 * math.sin(self._t * 30)
        self._blob(surface, cx, cy, int(10 * flick), (*GLOW, 90))     # outer glow
        self._blob(surface, cx, cy, int(6 * flick), (*PURPLE, 220))   # body
        pygame.draw.circle(surface, CORE, (int(cx), int(cy)), 3)      # hot core

    def _blob(self, surface, x, y, r, rgba):
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, rgba, (r, r), r)
        surface.blit(s, (x - r, y - r))
