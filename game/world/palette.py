"""Shared color/symbol registry for the room ↔ book matching system (§2.8).

Each classroom has a color; each book carries the matching color. Returning a
book is a pure visual match — no memorization. Keep names stable: the map data
(`tools/gen_map.py`) and gameplay both look colors up by name.
"""

ROOM_COLORS = {
    "red":    (220, 80, 80),
    "blue":   (90, 140, 240),
    "green":  (100, 200, 120),
    "yellow": (230, 200, 80),
    "purple": (180, 120, 220),
}


def color_rgb(name, default=(255, 255, 255)):
    return ROOM_COLORS.get(name, default)
