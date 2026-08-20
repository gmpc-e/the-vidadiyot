"""Procedural classroom furnishing — makes a room read as a *classroom* (§1).

**The furniture is solid, and the layout is what makes that survivable.** It was
non-solid for a long time and the reason is still true: a monster's hitbox is
44x44 against a 32px tile, so a room furnished with desks at their original
58px spacing is impassable for the thing that lives in it. Walking straight
through a desk reads as a bug, though, so the desks became collidable and the
**grid opened up to match** — three columns at 86px instead of four at 58, which
leaves a 66px lane between desks and a 54px lane between rows. `LANE_MIN` is the
number that matters and `tests/test_world_and_assets.py` walks a 44px agent from
the doorway to the return locker to prove the room is still crossable.

Two things are deliberately **not** solid: litter and anything hanging on a wall
(posters, the clock, the blackboard). They have no depth to walk into.

⚠️ **Doorways are kept clear explicitly.** The scenery locker bank runs along the
front wall — which is the wall the classroom's own door is in — so before this it
was painted straight across the doorway, and made solid it would have sealed the
room. `build()` takes the doorways and nothing solid is placed in them.

Each room's furniture is baked into one Surface at load and blitted whole, so
the per-frame cost is a single blit and the layout never shimmers between
frames. Layout is seeded from the room id, so a given room looks the same on
every run while different rooms don't look copy-pasted.

There are two furnishing strategies and they draw the same room. `_painted()`
blits the art extracted by `tools/extract_props.py`; `_drawn()` is the original
`pygame.draw` version, kept as the fallback because the art is regenerated into
`assets/` from source that lives outside the repo — a fresh checkout still has to
furnish a room. If the classrooms ever look suddenly geometric, the props are
missing, not broken.

The palette stays dark and desaturated on purpose — §1's rule is that the
environment is background and the actors are what stay bright and legible.
"""
import random

import pygame

from game.core.assets import load
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

# Room-local home of the **Return Locker** (roadmap §5). This is not decoration:
# `PlayState` puts the real `Locker` interactable here, so furnishing must leave
# it alone — and leave the lane in front of it clear, because it is the spot a
# player walks to while being chased. It sits on its own wall, away from the
# scenery locker bank, so the one locker that matters doesn't hide in a run of
# identical ones.
LOCKER_SLOT = pygame.Rect(10, 96, 22, 32)
LOCKER_LANE = 46          # px of floor kept clear to the right of it

LITTER_VARIANTS = 6

# The widest thing that has to fit between two solid pieces: a monster is 44x44.
# Everything below is spaced against this with room to spare, because a lane the
# exact width of the mover is one that only a perfectly-aligned mover fits down.
LANE_MIN = 52
# How far in front of a doorway stays clear of furniture. A player backing
# through a door while being shot at should not catch on a desk.
DOOR_CLEARANCE = 40


class _Room:
    """The surface being furnished, plus where the solid pieces ended up.

    Both furnishing strategies take one of these instead of a bare Surface, so
    "draw it" and "you can walk into it" stay one call and cannot drift apart —
    which is exactly how the locker bank ended up painted across a doorway.
    """

    def __init__(self, size, doorways):
        self.surf = pygame.Surface(size, pygame.SRCALPHA)
        self.w, self.h = size
        self.solids = []
        # doorways, widened by the lane a player needs to get through them
        self.clear = [pygame.Rect(d).inflate(DOOR_CLEARANCE * 2, DOOR_CLEARANCE * 2)
                      for d in doorways]

    def blocked(self, rect):
        """True if `rect` would stand in a doorway, so it must not be placed."""
        return rect.collidelist(self.clear) != -1

    def solid(self, rect):
        """Record a solid footprint. False if it fell in a doorway and was not."""
        rect = pygame.Rect(rect)
        if self.blocked(rect):
            return False
        self.solids.append(rect)
        return True


def _prop(name):
    return load(f"props/{name}.png")


def _blit(room, name, x, y, shadow=False, solid=None):
    """Blit a painted prop by its top-left. False if the art isn't installed.

    `shadow` lays a dark ellipse under the piece first. Free-standing furniture
    needs it on the painted parquet: the floor and the wood are the same brown,
    so without a contact shadow a desk floats rather than stands. Wall-mounted
    pieces don't get one — they aren't on the floor.
    """
    img = _prop(name)
    if img is None:
        return False
    w, h = img.get_size()
    # `solid` is the *footprint*: how much of the piece stops a body, given as
    # (inset_x, inset_top). A desk seen from above is mostly desk, but the top
    # few pixels are the far edge you should be able to stand behind.
    if solid is not None:
        inset_x, inset_top = solid
        if not room.solid(pygame.Rect(x + inset_x, y + inset_top,
                                      w - inset_x * 2, h - inset_top)):
            return False          # it stands in a doorway; draw nothing at all
    if shadow:
        pad = pygame.Surface((w, 5), pygame.SRCALPHA)
        pygame.draw.ellipse(pad, (0, 0, 0, 90), (0, 0, w, 5))
        room.surf.blit(pad, (x, y + h - 4))
    room.surf.blit(img, (x, y))
    return True


# ── the painted room ─────────────────────────────────────────────────────---
def _painted(room, rng):
    """The room colour is deliberately unused here — see the blackboard note."""
    surf, w, h = room.surf, room.w, room.h
    board = _prop("blackboard")
    if board and board.get_width() < w - 20:
        surf.blit(board, ((w - board.get_width()) // 2, 6))
        # No room-colour mark on the board. There were three of them saying the
        # same thing — the door plate on the way in, the locker's label, and a
        # coloured icon chalked here — and on painted art the third one just read
        # as a bright box floating on a blackboard. The door tells you whose room
        # it is; the locker tells you where the book goes. That is enough.

    # Wall-mounted, so nothing to walk into: no footprint on any of these.
    _blit(room, "clock", w - 42, 14)
    _blit(room, f"poster_{rng.choice('abc')}", 26, 12)
    if w > 300:
        _blit(room, f"poster_{rng.choice('abc')}", w - 98, 56)

    desk = _prop("teacher_desk")
    if desk:
        _blit(room, "teacher_desk", (w - desk.get_width()) // 2, 60,
              shadow=True, solid=(2, 6))
    _blit(room, "bookshelf", w - 46, 104, shadow=True, solid=(1, 8))

    # A run of lockers along the front wall — scenery, unlike LOCKER_SLOT, and
    # ⚠️ that is the wall the classroom's own door is in. `_blit` drops any
    # segment standing in the doorway rather than drawing a wall across it.
    bank = _prop("locker_bank")
    if bank and h > 200:
        y = h - bank.get_height() - 10
        for i in range(max(1, (w - 180) // bank.get_width())):
            _blit(room, "locker_bank", 120 + i * bank.get_width(), y, solid=(0, 4))

    _student_desks(room, rng, painted=True)
    _litter(room, rng, painted=True)


def _student_desks(room, rng, painted):
    """A grid of desks with aisles a 44px monster can actually walk down.

    ⚠️ **The spacing is the whole reason the desks can be solid.** It was 4
    columns at 58px, which puts 38px between two 19px desks — narrower than the
    thing that has to live in the room. Three columns at 86px leaves 66px, and
    74px rows leave 52px, both clear of `LANE_MIN`. Widening the desks or adding
    a column back re-seals the room, which is what the traversability test in
    `tests/test_world_and_assets.py` is there to catch.

    The chairs are drawn but never solid: they are small, they are tucked under
    the desk's footprint, and making them collidable turns each desk into an
    L-shaped snag.
    """
    w, h = room.w, room.h
    cols, rows = 3, 3
    gap_x, gap_y = 86, 74
    x0 = max(LOCKER_SLOT.right + LOCKER_LANE, (w - cols * gap_x) // 2 + 18)
    y0 = 112
    for r in range(rows):
        for c in range(cols):
            x, y = x0 + c * gap_x + rng.randint(-2, 2), y0 + r * gap_y
            if x + 30 > w - 10 or y + 34 > h - 56:
                continue
            if painted:
                fallen = rng.random() < 0.12
                _blit(room, "chair_fallen" if fallen else "chair", x + 5, y + 20,
                      shadow=not fallen)
                _blit(room, f"desk_{rng.choice('abc')}", x, y, shadow=True,
                      solid=(1, 5))
            else:
                _chair(room.surf, x + 7, y + 18)
                if room.solid(pygame.Rect(x, y + 3, 26, 13)):
                    _desk(room.surf, x, y)


def _litter(room, rng, painted):
    """Paper on the floor. Never solid — you walk over litter, not into it."""
    w, h = room.w, room.h
    for _ in range(rng.randint(5, 9)):
        px, py = rng.randint(8, max(9, w - 14)), rng.randint(60, max(61, h - 12))
        if painted and _blit(room, f"litter_{rng.randrange(LITTER_VARIANTS)}", px, py):
            continue
        pygame.draw.rect(room.surf, PAPER, (px, py, rng.randint(3, 5), rng.randint(2, 4)))


# ── the drawn room (fallback when the painted props aren't installed) ────---
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


def _drawn(room, rgb, rng):
    surf, w, h = room.surf, room.w, room.h
    _blackboard(surf, pygame.Rect(0, 0, w, h), rgb, rng)
    _clock(surf, w - 30, 22)
    _poster(surf, 16, 12, rng)
    if w > 260:
        _poster(surf, w - 64, 54, rng)
    td_w = 46
    if room.solid(pygame.Rect(w // 2 - td_w // 2, 60, td_w, 16)):
        _desk(surf, w // 2 - td_w // 2, 56, td_w, 20)
    # scenery lockers along the front wall, mirroring the painted layout
    if h > 200 and room.solid(pygame.Rect(120, h - 44, max(26, (w - 200) // 26 * 26), 20)):
        _lockers(surf, 120, h - 44, max(1, (w - 200) // 26), rgb)
    _student_desks(room, rng, painted=False)
    _litter(room, rng, painted=False)


def build(room_rect, color, room_id, doorways=()):
    """Bake one classroom's furniture. Returns (overlay Surface, solid rects).

    `doorways` are room-local rects that must stay walkable; the solids come
    back room-local too, so the caller offsets them into world space.
    """
    rng = random.Random(hash(room_id) & 0xFFFF)
    room = _Room(room_rect.size, doorways)
    if _prop("desk_a"):
        _painted(room, rng)
    else:
        _drawn(room, color_rgb(color), rng)
    return room.surf, room.solids
