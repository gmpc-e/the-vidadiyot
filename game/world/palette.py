"""Shared color/symbol registry for the room ↔ book matching system (§2.8).

Also owns how that colour is *drawn* onto an object, so the door plate, the
locker plate and the blackboard all say "this is the red room" the same way.

Each classroom has a color; each book carries the matching color. Returning a
book is a pure visual match — no memorization. Keep names stable: the map data
(`tools/gen_map.py`) and gameplay both look colors up by name.
"""

import pygame

ROOM_COLORS = {
    "red":    (220, 80, 80),
    "blue":   (90, 140, 240),
    "green":  (100, 200, 120),
    "yellow": (230, 200, 80),
    "purple": (180, 120, 220),
}


def color_rgb(name, default=(255, 255, 255)):
    return ROOM_COLORS.get(name, default)


TINT_STRENGTH = 0.42       # how far a room's object is pulled toward its colour
_TINTED = {}               # (id(surface), colour, strength) -> tinted copy


def tint(surface, rgb, strength=TINT_STRENGTH):
    """A copy of `surface` washed toward `rgb`, cached.

    This replaced drawing a coloured plate on the door and a coloured label on
    the locker. Both were small flat rectangles of raw palette colour, and on
    painted art they read as UI stuck to the scene rather than as part of it —
    the thing that kept getting reported. Washing the *whole object* toward its
    room colour says the same thing with nothing added to the picture: the red
    room's door is warm, the blue room's locker is cool, and neither has a box
    on it.

    Multiplying by a saturated colour would crush the painting (blue is
    (90, 140, 240), so it scales every red channel to 0.35), so the colour is
    lifted toward white first and only `strength` of it is applied.
    """
    key = (id(surface), rgb, strength)
    if key not in _TINTED:
        wash = tuple(int(c + (255 - c) * (1.0 - strength)) for c in rgb)
        out = surface.copy()
        out.fill((*wash, 255), special_flags=pygame.BLEND_RGBA_MULT)
        _TINTED[key] = out
    return _TINTED[key]
