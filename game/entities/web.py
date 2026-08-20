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
    """Little Snir's web. Painted since §21; the drawn version is the fallback."""
    # What `PlayState` plays when this lands on the player. Kept here rather
    # than branched on by type at the call site, so a new projectile brings its
    # own sound with it instead of needing the play loop edited too.
    hit_sound = "web_hit"

    def __init__(self, x, y, direction, sprite=None):
        s = settings.WEB_SIZE
        super().__init__(x, y, s, s)
        self.sprite = sprite
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
        if self.sprite:
            # The painted web is drawn head-forward with its trail streaming
            # behind, so it has to be turned to face where it is going — unlike
            # the drawn version, which is radially symmetrical and never needed
            # to know. Screen y grows downward, hence the negated angle.
            angle = -math.degrees(math.atan2(self.vel.y, self.vel.x)) if self.vel.length_squared() else 0
            img = pygame.transform.rotate(self.sprite, angle)
            surface.blit(img, img.get_rect(center=(cx, cy)))
            return
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
