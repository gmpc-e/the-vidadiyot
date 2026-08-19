"""Interactables: things the player triggers with the interact key.

M3 has Door. FusePanel, PAConsole, and MainGate follow in later milestones and
plug into the same "nearest interactable within range -> interact()" flow.
"""
import pygame

from game.world.palette import color_rgb


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
        """Distance from `point` to the nearest edge of the door (0 if inside)."""
        cx = max(self.rect.left, min(point[0], self.rect.right))
        cy = max(self.rect.top, min(point[1], self.rect.bottom))
        return pygame.Vector2(cx, cy).distance_to(point)

    def draw(self, surface, camera):
        r = self.rect.move(-round(camera.offset.x), -round(camera.offset.y))
        rgb = color_rgb(self.color)
        if self.locked:
            self._draw_closed(surface, r, rgb)
        else:
            self._draw_open(surface, r, rgb)

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
