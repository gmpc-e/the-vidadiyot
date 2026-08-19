"""Entity base: position, velocity, hitbox, update/draw.

Position is the entity's *center* in world space. The hitbox is an axis-aligned
rect kept centered on the position — collision code works on the hitbox.
"""
import pygame


class Entity:
    def __init__(self, x, y, w, h):
        self.pos = pygame.Vector2(x, y)      # center, world space
        self.vel = pygame.Vector2(0, 0)      # px/sec
        self.size = pygame.Vector2(w, h)
        self.color = (200, 200, 200)         # placeholder until sprites exist
        self.sprite = None                    # set once art is loaded

    @property
    def hitbox(self):
        r = pygame.Rect(0, 0, int(self.size.x), int(self.size.y))
        r.center = (round(self.pos.x), round(self.pos.y))
        return r

    def update(self, dt):
        self.pos += self.vel * dt

    def move_and_collide(self, dt, collider):
        """Move by self.vel one axis at a time, snapping out of solid rects.

        `collider` exposes solid_rects(box) -> list[Rect]. Shared by the player
        and monsters so both resolve walls (and locked doors) identically.
        """
        # X axis
        self.pos.x += self.vel.x * dt
        box = self.hitbox
        for r in collider.solid_rects(box):
            if box.colliderect(r):
                if self.vel.x > 0:
                    box.right = r.left
                elif self.vel.x < 0:
                    box.left = r.right
        self.pos.x = box.centerx

        # Y axis
        self.pos.y += self.vel.y * dt
        box = self.hitbox
        for r in collider.solid_rects(box):
            if box.colliderect(r):
                if self.vel.y > 0:
                    box.bottom = r.top
                elif self.vel.y < 0:
                    box.top = r.bottom
        self.pos.y = box.centery

    def draw(self, surface, camera):
        r = self.hitbox
        r.topleft = (r.x - round(camera.offset.x), r.y - round(camera.offset.y))
        if self.sprite:
            surface.blit(self.sprite, r.topleft)
        else:
            pygame.draw.rect(surface, self.color, r)
