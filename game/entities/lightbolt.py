"""LightBolt — Emri's close-range lightning.

Drawn as a jagged bolt rather than a ball: it is redrawn each frame from a fresh
random zigzag along its travel axis, which is what makes it read as *electricity*
instead of a fast yellow dot. Damages on contact, fizzles on walls.
"""
import math
import random
import pygame

import settings
from game.entities.entity import Entity

CORE = (255, 252, 220)
ARC = (255, 210, 90)
GLOW = (200, 130, 30)


class LightBolt(Entity):
    def __init__(self, x, y, direction, damage):
        s = settings.BOLT_SIZE
        super().__init__(x, y, s, s)
        d = pygame.Vector2(direction)
        self.dir = d.normalize() if d.length() else pygame.Vector2(1, 0)
        self.vel = self.dir * settings.BOLT_SPEED
        self.damage = damage
        self.life = settings.BOLT_LIFETIME
        self.dead = False

    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= dt
        if self.life <= 0:
            self.dead = True

    def on_hit(self, player):
        player.take_damage(self.damage)

    def _zigzag(self, cx, cy, length, jitter):
        """Points along the travel axis, kicked sideways at random."""
        perp = pygame.Vector2(-self.dir.y, self.dir.x)
        pts = []
        for i in range(6):
            t = i / 5.0
            off = 0 if i in (0, 5) else random.uniform(-jitter, jitter)
            p = (pygame.Vector2(cx, cy) - self.dir * length * (t - 0.5) + perp * off)
            pts.append((p.x, p.y))
        return pts

    def draw(self, surface, camera):
        off = camera.offset
        cx, cy = self.pos.x - off.x, self.pos.y - off.y
        glow = self._zigzag(cx, cy, 26, 5)
        pygame.draw.lines(surface, GLOW, False, glow, 5)
        pygame.draw.lines(surface, ARC, False, glow, 3)
        pygame.draw.lines(surface, CORE, False, self._zigzag(cx, cy, 22, 3), 1)
        pygame.draw.circle(surface, CORE, (int(cx), int(cy)), 3)
        # a couple of short forks so it crackles rather than streaks
        for _ in range(2):
            a = random.uniform(0, math.tau)
            r = random.uniform(5, 11)
            pygame.draw.line(surface, ARC, (cx, cy),
                             (cx + math.cos(a) * r, cy + math.sin(a) * r), 1)
