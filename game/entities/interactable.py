"""Interactables: things the player triggers with the interact key.

Door gates a classroom; Locker is the delivery point inside it. Both are rects
with a room color, resolved by the same "nearest interactable within range ->
interact()" flow in PlayState.
"""
import pygame

from game.core.assets import load
from game.world.palette import color_rgb, tint

DOOR_SPRITES = {True: "sprites/door_closed.png", False: "sprites/door_open.png"}


def rect_dist(rect, point):
    """Distance from `point` to the nearest edge of `rect` (0 if inside)."""
    cx = max(rect.left, min(point[0], rect.right))
    cy = max(rect.top, min(point[1], rect.bottom))
    return pygame.Vector2(cx, cy).distance_to(point)


class Door:
    """A classroom door. Locked doors block movement until a key is spent.

    The door keeps its classroom color visible even once unlocked, so the player
    still knows which colored book belongs inside (§2.8).
    """
    def __init__(self, rect, room_id, color):
        self.rect = pygame.Rect(rect)
        self.room_id = room_id
        self.color = color            # color name, matches the classroom
        self.locked = True

    @property
    def blocks(self):
        return self.locked

    def try_unlock(self, inventory):
        """Spend one key to unlock. Returns True on success."""
        if self.locked and inventory.remove("key"):
            self.locked = False
            return True
        return False

    def dist_to(self, point):
        return rect_dist(self.rect, point)

    def draw(self, surface, camera):
        r = self.rect.move(-round(camera.offset.x), -round(camera.offset.y))
        rgb = color_rgb(self.color)
        img = load(DOOR_SPRITES[self.locked])
        if img is None:                       # no painted art on this checkout
            (self._draw_closed if self.locked else self._draw_open)(surface, r, rgb)
            return
        if img.get_size() != r.size:
            img = pygame.transform.smoothscale(img, r.size)
        surface.blit(tint(img, rgb), r.topleft)

    def _draw_closed(self, surface, r, rgb):
        # two wooden panels with a seam, a color plate, a lock and a handle
        pygame.draw.rect(surface, (78, 56, 38), r)
        pygame.draw.rect(surface, (48, 34, 22), r, 2)
        mid = r.centerx
        pygame.draw.line(surface, (48, 34, 22), (mid, r.top + 2), (mid, r.bottom - 2), 1)
        for panel in (pygame.Rect(r.left + 4, r.top + 4, r.width // 2 - 7, r.height - 8),
                      pygame.Rect(mid + 3, r.top + 4, r.width // 2 - 7, r.height - 8)):
            pygame.draw.rect(surface, (96, 70, 48), panel, 1)
        # colored plate = which book belongs here
        plate = pygame.Rect(0, 0, 12, 12); plate.center = (mid, r.top + 10)
        pygame.draw.rect(surface, rgb, plate)
        pygame.draw.rect(surface, (20, 16, 12), plate, 1)
        # lock body + shackle
        lock = pygame.Rect(0, 0, 8, 7); lock.center = (mid, r.centery + 4)
        pygame.draw.arc(surface, (230, 210, 120), pygame.Rect(lock.x + 1, lock.y - 4, 6, 8), 3.14, 6.28, 2)
        pygame.draw.rect(surface, (230, 210, 120), lock)
        pygame.draw.rect(surface, (60, 50, 20), lock, 1)

    def _draw_open(self, surface, r, rgb):
        # dark threshold with the door swung to one side, colored frame kept
        pygame.draw.rect(surface, (24, 22, 26), r)
        leaf = pygame.Rect(r.left, r.top, 5, r.height)
        pygame.draw.rect(surface, (78, 56, 38), leaf)
        pygame.draw.rect(surface, rgb, r, 2)


class Locker:
    """The book's home — a classroom's delivery point (§5).

    Mirrors Door: a rect, the room's id and color, `dist_to`, `draw`. Two things
    it deliberately does *not* do:

    * **It never blocks.** Same reason nothing in `world/decor.py` is solid — a
      monster's hitbox is 44x44, and a 22px box standing 10px off the wall would
      leave a pocket the room's guardian could wedge itself into.
    * **It never gates itself.** Whether the book may go in is PlayState's call
      (right color, room cleared); the locker only records that it happened, so
      the closed/filled art is the one thing it owns.

    It claims the top slot of the painted locker bank (`decor.LOCKER_BANK`), so
    the objective and the scenery read as one run of lockers instead of a prop
    parked next to a prop.
    """
    def __init__(self, rect, room_id, color):
        self.rect = pygame.Rect(rect)
        self.room_id = room_id
        self.color = color
        self.filled = False           # its book is home; the door hangs open

    def dist_to(self, point):
        return rect_dist(self.rect, point)

    def draw(self, surface, camera):
        r = self.rect.move(-round(camera.offset.x), -round(camera.offset.y))
        rgb = color_rgb(self.color)
        img = load("props/locker_open.png" if self.filled else "props/locker.png")
        if img is None:
            self._draw_flat(surface, r, rgb)
        else:
            # Anchored bottom-left, never scaled to the rect: the open state is
            # wider than the shut one because the door swings out, so stretching
            # each to the same box would make the locker body jump the moment a
            # book went in. The body stays put and the door appears beside it.
            surface.blit(tint(img, rgb), (r.left, r.bottom - img.get_height()))

    def _draw_flat(self, surface, r, rgb):
        """Fallback locker, for a checkout with no painted props installed."""
        pygame.draw.rect(surface, (96, 99, 110), r)
        pygame.draw.rect(surface, (38, 40, 48), r, 1)
        for i in range(3):
            y = r.top + 22 + i * 3
            pygame.draw.line(surface, (62, 64, 74), (r.left + 5, y), (r.right - 6, y), 1)
        pygame.draw.rect(surface, (188, 186, 176), (r.right - 6, r.centery + 2, 2, 6))
