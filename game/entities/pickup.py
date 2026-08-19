"""Collectible pickups: keys, books, fuses, id cards.

Some items have a `variant` — books carry a color name that must match the
classroom they belong to (§2.8). The variant drives both the pickup's on-screen
color and the delivery match.
"""
import math
import pygame

from game.entities.entity import Entity
from game.world.palette import color_rgb
from game.ui.icons import draw_key, draw_book, draw_bottle

# per-type icon color, used when an item has no variant
ITEM_COLORS = {
    "key":     (240, 200, 80),
    "book":    (120, 180, 240),
    "fuse":    (230, 130, 90),
    "id_card": (170, 220, 150),
    "health":  (230, 70, 80),
}
PICKUP_SIZE = 16


def item_color(item_type, variant=None):
    """Display color for an item: variant color if it has one, else type color."""
    if variant:
        return color_rgb(variant)
    return ITEM_COLORS.get(item_type, (255, 255, 255))


class Pickup(Entity):
    def __init__(self, x, y, item_type, variant=None):
        super().__init__(x, y, PICKUP_SIZE, PICKUP_SIZE)
        self.item_type = item_type
        self.variant = variant
        self.color = item_color(item_type, variant)
        self.collected = False
        self.guarded = False        # if True, a living monster blocks collection
        self._t = 0.0

    def update(self, dt):
        self._t += dt

    def draw(self, surface, camera):
        bob = math.sin(self._t * 3.0) * 3.0
        cx = self.pos.x - camera.offset.x
        cy = self.pos.y - camera.offset.y + bob
        r = PICKUP_SIZE / 2
        # soft shadow on the ground
        pygame.draw.ellipse(surface, (0, 0, 0),
                            pygame.Rect(cx - r, self.pos.y - camera.offset.y + r - 2, PICKUP_SIZE, 6))
        icon_rect = pygame.Rect(int(cx - r), int(cy - r), PICKUP_SIZE, PICKUP_SIZE)
        if self.item_type == "book":
            draw_book(surface, icon_rect, self.color)
        elif self.item_type == "key":
            draw_key(surface, icon_rect, self.color)
        elif self.item_type == "health":
            draw_bottle(surface, icon_rect, self.color)
        else:
            pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]  # diamond
            pygame.draw.polygon(surface, self.color, pts)
            pygame.draw.polygon(surface, (255, 255, 255), pts, 1)
