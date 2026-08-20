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

# A **shining** pickup is one that was won rather than found — the book a teacher
# drops when it dies (§5). It gets a slow halo and a pair of crossed glints, both
# in warm white rather than the item's own colour, so the read is "prize" and not
# "another red thing in a red room". Kept to two rings and four spokes: this sits
# on a 640x360 screen and anything busier turns into a smudge.
SHINE_COLOR   = (255, 240, 196)
SHINE_RADIUS  = 16       # px, at the peak of the pulse
SHINE_PERIOD  = 1.6      # seconds per breath
SHINE_SPIN    = 1.1      # radians/sec the glints rotate
SHINE_SPOKE   = 12       # px, half-length of each glint arm
# ⚠️ **`BLEND_RGB_ADD` ignores the source alpha**, so setting a low alpha on the
# rings does nothing at all — the full colour is added wherever a ring was drawn,
# which is why the first two attempts came out as a flat white disc with a hard
# edge. The falloff has to live in the *colour*: rings are drawn largest first,
# each one brighter than the last, so the innermost overwrite makes the centre
# the brightest point and the rim adds almost nothing.
SHINE_RINGS   = 7
SHINE_PEAK    = (146, 132, 96)   # how much the very centre is brightened by
SHINE_SPOKE_C = (104, 94, 70)


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
        self.shining = False        # won, not found — see SHINE_* above
        self._t = 0.0

    def update(self, dt):
        self._t += dt

    def draw(self, surface, camera):
        bob = math.sin(self._t * 3.0) * 3.0
        cx = self.pos.x - camera.offset.x
        cy = self.pos.y - camera.offset.y + bob
        r = PICKUP_SIZE / 2
        if self.shining:
            self._draw_shine(surface, cx, cy)
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

    def _draw_shine(self, surface, cx, cy):
        """The halo and glints, drawn *under* the icon so they never hide it.

        Everything is composited on one scratch surface and blitted with
        additive blending — drawing translucent rings straight onto the scene
        one at a time darkens the overlaps into rims, which reads as a bullseye
        rather than as light.
        """
        pulse = 0.5 + 0.5 * math.sin(self._t * math.tau / SHINE_PERIOD)
        peak = SHINE_RADIUS * (0.78 + 0.22 * pulse)
        size = int(SHINE_RADIUS * 2 + 4)
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        mid = size // 2
        lit = 0.62 + 0.38 * pulse
        for i in range(SHINE_RINGS):
            rad = max(1, int(peak * (SHINE_RINGS - i) / SHINE_RINGS))
            step = lit * (i + 1) / SHINE_RINGS
            pygame.draw.circle(layer, tuple(int(c * step) for c in SHINE_PEAK),
                               (mid, mid), rad)
        spoke = tuple(int(c * lit) for c in SHINE_SPOKE_C)
        for i in range(4):
            a = self._t * SHINE_SPIN + i * (math.tau / 4)
            dx, dy = math.cos(a) * SHINE_SPOKE, math.sin(a) * SHINE_SPOKE
            pygame.draw.line(layer, spoke, (mid - dx, mid - dy), (mid + dx, mid + dy))
        surface.blit(layer, (cx - mid, cy - mid), special_flags=pygame.BLEND_RGB_ADD)
