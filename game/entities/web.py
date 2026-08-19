"""WebProjectile — Little Snir's curly-hair web.

Drawn as a messy tangle of curly strands. On contact it doesn't hurt; instead it
*entangles* the player, who must mash Space to break free (see Player.take_web).
"""
import math
import pygame

import settings
from game.entities.entity import Entity

STRAND = (230, 228, 235)
STRAND_D = (150, 135, 120)


class WebProjectile(Entity):
    def __init__(self, x, y, direction):
        s = settings.WEB_SIZE
        super().__init__(x, y, s, s)
        d = pygame.Vector2(direction)
        self.vel = d.normalize() * settings.WEB_SPEED if d.length() else pygame.Vector2()
        self.life = settings.WEB_LIFETIME
        self.dead = False
        self._spin = 0.0

    def update(self, dt):
        self._spin += dt * 6
        self.pos += self.vel * dt
        self.life -= dt
        if self.life <= 0:
            self.dead = True

    def on_hit(self, player):
        player.take_web()

    def draw(self, surface, camera):
        cx = self.pos.x - camera.offset.x
        cy = self.pos.y - camera.offset.y
        r = settings.WEB_SIZE / 2
        # a ball of overlapping curly arcs
        for i in range(6):
            a = self._spin + i * (math.tau / 6)
            ox = math.cos(a) * r * 0.4
            oy = math.sin(a) * r * 0.4
            box = pygame.Rect(cx + ox - r, cy + oy - r, r * 2, r * 2)
            col = STRAND if i % 2 else STRAND_D
            pygame.draw.arc(surface, col, box, a, a + math.pi * 1.2, 2)
        pygame.draw.circle(surface, STRAND, (int(cx), int(cy)), 2)
