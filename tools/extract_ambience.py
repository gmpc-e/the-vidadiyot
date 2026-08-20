"""Cut the ambience sheet — the small moving things that make a room inhabited.

Source: `~/Downloads/the-vidadiyot/map/props/phase2-p9.png`, Priority 4 of
`docs/ART_PROMPTS_PHASE2.md`: a flickering fluorescent tube, a dripping pipe and
a set of cobwebs.

⚠️ **Two of the sheet's five rows are unusable and are not listed here.** The
corner-cobweb row is painted on a wall panel and the light-shaft row on a room
interior — both opaque rectangles of scene, where §0 asks for pure black. There
is no keying a subject off a painted background: the panel would arrive in game
as a visible rectangle around the web. They are rejected at the sheet, not
patched in the extractor.

Bands are given explicitly rather than found. The usable rows are separated by
the *unusable* ones, and a row scan cannot tell "a wall with a web on it" from
"a web" — so the boundaries are measured once, here, where they can be read.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_ambience.py
"""
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritelib import (flatten_color, key_by_fill, slice_strip,       # noqa: E402
                       strip_columns)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROPS = os.path.join(ROOT, "assets", "props")
SHEET = os.path.expanduser("~/Downloads/the-vidadiyot/map/props/phase2-p9.png")

LUMA_CUT = 20

# name -> (band, frames, target height)
# The tube hangs from the ceiling and the drip falls from a pipe, so both are
# positioned from their *top*; `slice_strip` keeps each frame's offset inside
# the strip's shared box, which preserves that without any anchoring code.
STRIPS = {
    "lamp":  ((18, 180), 4, 22),
    "drip":  ((420, 585), 4, 26),
}
# The cobwebs are five separate props, not an animation, so each is trimmed to
# its own content instead of sharing a canvas.
WEBS = ((805, 995), 5, 24)
# ⚠️ ...and they are **repainted** after scaling. A web is 1px strands of pale
# silk on black; averaged down from 200px to 30px the strands blend with the
# black around them and land at luma 12-17 — dark smudges, which is what the
# first cut shipped. The shape survives in the alpha, so the colour is replaced
# with a constant. See `spritelib.flatten_color`.
SILK = (138, 142, 152)
SILK_ALPHA = 0.6      # a veil, not a sheet — see `flatten_color`


def _cut_props(sheet, band, expect, target_h, prefix, flat=None):
    y0, y1 = band
    row = pygame.Surface((sheet.get_width(), y1 - y0), pygame.SRCALPHA)
    row.blit(sheet, (0, 0), (0, y0, sheet.get_width(), y1 - y0))
    cols = strip_columns(row, gutter=16, luma_cut=LUMA_CUT, min_width=20)
    if len(cols) != expect:
        raise SystemExit(f"{prefix}: found {len(cols)} props, expected {expect} "
                         f"(at {cols})")
    written = []
    for i, (x0, x1) in enumerate(cols):
        cell = pygame.Surface((x1 - x0, y1 - y0), pygame.SRCALPHA)
        cell.blit(row, (0, 0), (x0, 0, x1 - x0, y1 - y0))
        key_by_fill(cell, LUMA_CUT)
        rect = cell.get_bounding_rect()
        trimmed = pygame.Surface(rect.size, pygame.SRCALPHA)
        trimmed.blit(cell, (0, 0), rect)
        scale = target_h / trimmed.get_height()
        out = pygame.transform.smoothscale(
            trimmed, (max(1, round(trimmed.get_width() * scale)), target_h))
        if flat:
            out = flatten_color(out, flat, SILK_ALPHA)
        path = os.path.join(PROPS, f"{prefix}_{i}.png")
        pygame.image.save(out, path)
        written.append(path)
    return written


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    if not os.path.exists(SHEET):
        raise SystemExit(f"no sheet at {SHEET}")
    sheet = pygame.image.load(SHEET).convert_alpha()
    os.makedirs(PROPS, exist_ok=True)

    for name, (band, frames, h) in STRIPS.items():
        for i, f in enumerate(slice_strip(sheet, h, expect=frames,
                                          luma_cut=LUMA_CUT, band=band,
                                          gutter=16)):
            path = os.path.join(PROPS, f"{name}_{i}.png")
            pygame.image.save(f, path)
            print(f"  wrote {os.path.relpath(path, ROOT)} ({f.get_width()}x{f.get_height()})")

    band, n, h = WEBS
    for path in _cut_props(sheet, band, n, h, "cobweb", flat=SILK):
        img = pygame.image.load(path)
        print(f"  wrote {os.path.relpath(path, ROOT)} "
              f"({img.get_width()}x{img.get_height()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
