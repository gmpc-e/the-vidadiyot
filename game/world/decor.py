"""Procedural classroom furnishing — makes a room read as a *classroom* (§1).

Everything here is **floor-layer and non-solid**. That is the hard constraint,
not a style choice: a monster's hitbox is 44x44 against a 32px tile, so a room
furnished with solid desks in rows would be impassable for the monsters that
have to live in it, and every fight would turn into a geometry puzzle.

Each room's furniture is baked into one Surface at load and blitted whole, so
the per-frame cost is a single blit and the layout never shimmers between
frames. Layout is seeded from the room id, so a given room looks the same on
every run while different rooms don't look copy-pasted.

The palette stays dark and desaturated on purpose — §1's rule is that the
environment is background and the actors are what stay bright and legible.
"""
import random

import pygame

from game.world.palette import color_rgb

BOARD = (34, 46, 40)
BOARD_FRAME = (74, 58, 40)
CHALK = (150, 160, 155)
DESK = (86, 63, 42)
DESK_TOP = (104, 78, 52)
DESK_DARK = (54, 39, 26)
METAL = (78, 80, 90)
PAPER = (176, 172, 160)
WALL_ITEM = (62, 58, 66)


def _desk(surf, x, y, w=26, h=16):
    """A student desk seen from above: top, front edge, and two legs."""
    pygame.draw.rect(surf, DESK_DARK, (x, y + h - 4, w, 4))
    pygame.draw.rect(surf, DESK, (x, y, w, h - 2))
    pygame.draw.rect(surf, DESK_TOP, (x + 1, y + 1, w - 2, h - 6))
    pygame.draw.rect(surf, DESK_DARK, (x, y, w, h - 2), 1)
    pygame.draw.rect(surf, METAL, (x + 3, y + h - 3, 2, 3))
    pygame.draw.rect(surf, METAL, (x + w - 5, y + h - 3, 2, 3))


def _chair(surf, x, y):
    pygame.draw.rect(surf, DESK_DARK, (x, y, 12, 10))
    pygame.draw.rect(surf, METAL, (x, y, 12, 3))


def _blackboard(surf, rect, rgb, rng):
    """The board on the back wall, with the room's color chalked on it."""
    b = pygame.Rect(rect.width // 2 - 78, 6, 156, 40)
    pygame.draw.rect(surf, BOARD_FRAME, b.inflate(6, 6), border_radius=2)
    pygame.draw.rect(surf, BOARD, b)
    for i in range(rng.randint(3, 5)):                  # chalk scribble
        y = b.top + 9 + i * 7
        x0 = b.left + rng.randint(6, 22)
        pygame.draw.line(surf, CHALK, (x0, y), (x0 + rng.randint(40, 100), y), 1)
    swatch = pygame.Rect(b.right - 26, b.top + 8, 16, 16)   # this room's color
    pygame.draw.rect(surf, rgb, swatch)
    pygame.draw.rect(surf, (18, 18, 22), swatch, 1)
    pygame.draw.rect(surf, (200, 195, 180), (b.left + 4, b.bottom - 4, 10, 3))  # chalk tray


def _clock(surf, cx, cy):
    pygame.draw.circle(surf, WALL_ITEM, (cx, cy), 7)
    pygame.draw.circle(surf, (208, 206, 198), (cx, cy), 6)
    pygame.draw.circle(surf, (40, 40, 46), (cx, cy), 6, 1)
    pygame.draw.line(surf, (40, 40, 46), (cx, cy), (cx, cy - 4), 1)
    pygame.draw.line(surf, (40, 40, 46), (cx, cy), (cx + 3, cy), 1)


def _poster(surf, x, y, rng):
    w, h = rng.randint(14, 20), rng.randint(16, 22)
    pygame.draw.rect(surf, PAPER, (x, y, w, h))
    pygame.draw.rect(surf, (40, 38, 44), (x, y, w, h), 1)
    for i in range(3):
        pygame.draw.line(surf, (120, 116, 108),
                         (x + 3, y + 5 + i * 4), (x + w - 4, y + 5 + i * 4), 1)


def _lockers(surf, x, y, count, rgb):
    """A run of narrow lockers against the wall."""
    for i in range(count):
        r = pygame.Rect(x, y + i * 34, 22, 32)
        pygame.draw.rect(surf, METAL, r)
        pygame.draw.rect(surf, (44, 46, 54), r, 1)
        pygame.draw.line(surf, (44, 46, 54), (r.left + 2, r.top + 7), (r.right - 3, r.top + 7), 1)
        pygame.draw.rect(surf, (168, 166, 158), (r.right - 6, r.centery, 2, 5))   # handle
        if i % 2 == 0:                                   # a color tag here and there
            pygame.draw.rect(surf, rgb, (r.left + 3, r.top + 3, 5, 3))


def build(room_rect, color, room_id):
    """Bake one classroom's furniture into a transparent overlay Surface."""
    rng = random.Random(hash(room_id) & 0xFFFF)
    surf = pygame.Surface(room_rect.size, pygame.SRCALPHA)
    w, h = room_rect.size
    rgb = color_rgb(color)

    _blackboard(surf, pygame.Rect(0, 0, w, h), rgb, rng)
    _clock(surf, w - 30, 22)
    _poster(surf, 16, 12, rng)
    if w > 260:
        _poster(surf, w - 64, 54, rng)

    # teacher's desk, centered under the board and turned to face the class
    td_w = 46
    _desk(surf, w // 2 - td_w // 2, 56, td_w, 20)

    # locker bank down one wall — the school signifier, and the spot §5's
    # book-return locker will eventually claim
    _lockers(surf, 10, 92, min(5, (h - 120) // 34), rgb)

    # student desks: a grid spread down the room, with aisles wide enough for a
    # 44px monster — see the module docstring on why nothing here is solid
    cols, rows = 4, 4
    gap_x, gap_y = 58, 62
    grid_w = cols * gap_x
    x0 = (w - grid_w) // 2 + 18   # nudged clear of the locker bank
    y0 = 118
    for r in range(rows):
        for c in range(cols):
            if y0 + r * gap_y + 30 > h - 12:
                continue
            jitter = rng.randint(-2, 2)
            x = x0 + c * gap_x + jitter
            y = y0 + r * gap_y
            _chair(surf, x + 7, y + 18)
            _desk(surf, x, y)

    # a little mess on the floor
    for _ in range(rng.randint(4, 7)):
        px, py = rng.randint(8, w - 14), rng.randint(60, h - 12)
        pygame.draw.rect(surf, PAPER, (px, py, rng.randint(3, 5), rng.randint(2, 4)))
    return surf
