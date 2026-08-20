"""DarkTome — the teachers' projectile: a flung book trailing smoke.

The first projectile in the game with **painted art** rather than a procedural
shape. Fireball and LightBolt draw themselves out of circles and zigzags, which
is why they need no assets; this one is `sprites/tome.png` off the §R8 sheet, and
the sprite is passed in at construction the way monster sprites are, because
projectiles are built inside `PlayState` and have no access to the asset cache.

A missing sprite is not fatal — it falls back to a drawn slab. Art can go absent
in a fresh checkout before `extract_teacher.py` has run, and a crash there would
be a poor trade for a book that looks like a brick for one frame.
"""
import math

import pygame

import settings
from game.entities.entity import Entity

SMOKE = (58, 40, 78)
PAGE = (222, 212, 186)
COVER = (74, 58, 62)


class DarkTome(Entity):
    hit_sound = "tome_hit"

    def __init__(self, x, y, direction, damage, sprite=None):
        s = settings.TOME_SIZE
        super().__init__(x, y, s, s)
        d = pygame.Vector2(direction)
        self.vel = d.normalize() * settings.TOME_SPEED if d.length() else pygame.Vector2()
        self.damage = damage
        self.life = settings.TOME_LIFETIME
        self.dead = False
        self.sprite = sprite
        self._t = 0.0
        self._trail = []

    def update(self, dt):
        self._t += dt
        self._trail.append((self.pos.x, self.pos.y))
        if len(self._trail) > 7:
            self._trail.pop(0)
        self.pos += self.vel * dt
        self.life -= dt
        if self.life <= 0:
            self.dead = True

    def on_hit(self, player):
        player.take_damage(self.damage)

    def draw(self, surface, camera):
        off = camera.offset
        for i, (tx, ty) in enumerate(self._trail):     # ragged smoke behind it
            r = 2 + i // 2
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*SMOKE, 24 + i * 16), (r, r), r)
            surface.blit(s, (tx - off.x - r, ty - off.y - r))

        cx, cy = self.pos.x - off.x, self.pos.y - off.y
        if self.sprite:
            # A thrown book tumbles. Rotating the sprite rather than animating it
            # costs one transform per frame and reads better than a book sliding
            # through the air face-on.
            img = pygame.transform.rotate(self.sprite, (self._t * 260) % 360)
            surface.blit(img, img.get_rect(center=(cx, cy)))
            return
        r = settings.TOME_SIZE // 2
        pygame.draw.rect(surface, COVER, (cx - r, cy - r, r * 2, r * 2))
        pygame.draw.line(surface, PAGE, (cx, cy - r + 1), (cx, cy + r - 1))
