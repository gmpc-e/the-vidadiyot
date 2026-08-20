"""Roni's Royal Blade in flight — the player's thrown weapon.

This is the first projectile that travels *outward* from the player, so unlike
the monster casts it damages monsters rather than the player and dies on the
first thing it hits. PlayState keeps it in its own list for that reason.

It spins as it flies and drags a short streak behind it, which is what makes a
34px sprite read as a thrown blade rather than a sliding decal.
"""
import pygame

import settings
from game.entities.entity import Entity

STREAK = (196, 150, 236)
SPARK = (240, 220, 255)


class Knife(Entity):
    def __init__(self, x, y, direction, damage, sprite=None):
        s = settings.KNIFE_SIZE
        super().__init__(x, y, s, s)
        d = pygame.Vector2(direction)
        self.dir = d.normalize() if d.length() else pygame.Vector2(1, 0)
        self.vel = self.dir * settings.KNIFE_SPEED
        self.damage = damage
        self.sprite = sprite
        self.dead = False
        self.travelled = 0.0
        self._spin = 0.0
        self._trail = []

    def update(self, dt):
        self._spin += dt * 14
        self._trail.append((self.pos.x, self.pos.y))
        if len(self._trail) > 5:
            self._trail.pop(0)
        step = self.vel * dt
        self.pos += step
        self.travelled += step.length()
        if self.travelled >= settings.KNIFE_RANGE:
            self.dead = True

    def on_hit(self, monster):
        """Returns True if the blade finished the monster off."""
        self.dead = True
        # pass the blade's own heading: where it *landed* is inside the monster
        return monster.take_hit(self.pos - self.dir * 8, self.damage,
                                direction=self.dir)

    def draw(self, surface, camera):
        """Just the blade.

        ⚠️ **No streak trail.** It was five drawn lines behind the knife, added
        when the knife itself was a 3px circle and needed help reading as a
        thrown object. It is a painted blade now, and the trail was drawing a
        second, cruder weapon behind the real one. `_trail` is still recorded —
        it is two lines of bookkeeping and the next effect that wants a path
        will want it — but nothing draws it.
        """
        off = camera.offset
        cx, cy = self.pos.x - off.x, self.pos.y - off.y
        if self.sprite:
            angle = -self.dir.angle_to(pygame.Vector2(1, 0)) - self._spin * 40
            img = pygame.transform.rotate(self.sprite, angle)
            surface.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))
        else:
            pygame.draw.circle(surface, SPARK, (int(cx), int(cy)), 3)
