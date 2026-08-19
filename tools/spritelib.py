"""Shared sprite-extraction helpers for the painted character sheets.

Every sheet lays poses out on a dark painterly background, and there is no single
trick that lifts them all — which strategy works depends on the character:

* **`MODE_FILL`** — flood-fill inward from the crop border, treating anything
  darker than `luma_cut` as background. The luma test (rather than distance from
  a seed color) is what makes this survive the vignette gradient; a seed-based
  fill stalls the moment the background shades away from the corner it sampled.
  Right for lit subjects like the knight. Note it can *split* a figure into
  islands wherever a dark region touches the border — the knight's armor shades
  below the cut — so never post-filter by "largest blob": that throws away the
  body and keeps his face. Exclude the sheets' painted pose labels by cropping
  below them instead.

* **`MODE_RAMP`** — no fill at all: alpha ramps with luminance, then the crop's
  own border is feathered out. Right for subjects that are *themselves* dark and
  would be eaten by a fill — Emri is drawn as shadow and smoke, so a fill leaves
  a floating head and two disembodied arms. The feather is what stops the kept
  vignette from reading as a rectangle around him.

`extract_terror.py` and `extract_snir.py` predate this module and keep their own
seed-based fill; it works on their sheets, so they are left alone.
"""
import os

import pygame

# Where the painted source art lives. The organised tree is searched first and
# the flat Downloads folder second, so tools keep working while art is being
# migrated into the tree rather than breaking the moment a file moves.
SOURCE_ROOTS = [
    os.path.expanduser("~/Downloads/the-vidadiyot"),
    os.path.expanduser("~/Downloads"),
]

MODE_FILL = "fill"
MODE_RAMP = "ramp"


def source(name):
    """Absolute path to a source image, searched by filename across the roots.

    Callers name the file, not its folder, so art can be filed into
    champions/monsters/menus/tiles without every tool needing an edit.
    """
    for root in SOURCE_ROOTS:
        direct = os.path.join(root, name)
        if os.path.exists(direct):
            return direct
        for dirpath, _dirs, files in os.walk(root):
            if name in files:
                return os.path.join(dirpath, name)
    raise FileNotFoundError(
        f"{name!r} not found under: " + ", ".join(SOURCE_ROOTS))


def load_source(name):
    return pygame.image.load(source(name)).convert_alpha()


def _luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def key_by_fill(surf, luma_cut):
    """Erase border-connected pixels darker than `luma_cut`, in place."""
    w, h = surf.get_size()
    stack = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
    stack += [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    seen = [[False] * h for _ in range(w)]
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or seen[x][y]:
            continue
        seen[x][y] = True
        if _luma(surf.get_at((x, y))) < luma_cut:
            surf.set_at((x, y), (0, 0, 0, 0))
            stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return surf


def key_by_ramp(surf, luma_cut, feather, gamma=0.9):
    """Alpha follows luminance, then fade out `feather` px from the crop edge.

    `gamma` shapes the curve below the cut: under 1 keeps dark pixels fairly
    solid (right for a subject made of shadow, like Emri), over 1 crushes them
    toward transparent (right for bright lettering that must lift cleanly off a
    painted scene, like the level banners).
    """
    w, h = surf.get_size()
    for y in range(h):
        for x in range(w):
            c = surf.get_at((x, y))
            lum = _luma(c)
            a = 255.0 if lum >= luma_cut else 255.0 * (lum / luma_cut) ** gamma
            if feather:
                edge = min(x, y, w - 1 - x, h - 1 - y)
                if edge < feather:
                    a *= edge / feather
            surf.set_at((x, y), (c[0], c[1], c[2], int(a)))
    return surf


def brighten(surf, gamma):
    """Lift shadows without blowing highlights: c' = 255*(c/255)**(1/gamma).

    The painted sheets are lit for a big canvas — at 48px on a dark school floor
    the knight's armor turns into an unreadable smudge. This is the §1 rule
    ("environment dark, actors bright") applied at extraction time.
    """
    w, h = surf.get_size()
    lut = [min(255, int(255 * (i / 255) ** (1.0 / gamma))) for i in range(256)]
    for y in range(h):
        for x in range(w):
            r, g, b, a = surf.get_at((x, y))
            surf.set_at((x, y), (lut[r], lut[g], lut[b], a))
    return surf


def solidify(surf, threshold=110):
    """Snap alpha to fully-on or fully-off above/below `threshold`.

    Downscaling a keyed cutout blends every figure/background boundary into
    partial alpha. On a figure the fill nibbled at — dark armor against a dark
    backdrop — those partials pile up until the character reads as a *ghost*.
    Snapping restores a solid body and, as a bonus, gives the crisp hard edge
    pixel art wants. A one-pixel rim below the threshold is dropped rather than
    kept soft, so nothing is left half-there.
    """
    w, h = surf.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, a = surf.get_at((x, y))
            surf.set_at((x, y), (r, g, b, 255 if a >= threshold else 0))
    return surf


def extract_pose(sheet, crop, target_h, mode=MODE_FILL, luma_cut=40, feather=0,
                 gamma=1.0, solid=None, alpha_gamma=0.9):
    """Crop one pose out of `sheet`, key its background, trim, scale to height."""
    x, y, w, h = crop
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.blit(sheet, (0, 0), crop)

    if mode == MODE_FILL:
        key_by_fill(surf, luma_cut)
    else:
        key_by_ramp(surf, luma_cut, feather, alpha_gamma)

    if gamma != 1.0:
        brighten(surf, gamma)

    rect = surf.get_bounding_rect()
    if rect.width == 0 or rect.height == 0:
        raise ValueError(f"crop {crop} came out empty — wrong coordinates?")
    trimmed = pygame.Surface(rect.size, pygame.SRCALPHA)
    trimmed.blit(surf, (0, 0), rect)

    scale = target_h / trimmed.get_height()
    out = pygame.transform.smoothscale(
        trimmed, (max(1, round(trimmed.get_width() * scale)), target_h))
    if solid is not None:
        solidify(out, solid)
    return out
