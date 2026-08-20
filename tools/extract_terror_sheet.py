"""Cut Little Terror's character sheet — walk, fireball wind-up, hurt.

Source: `~/Downloads/the-vidadiyot/monsters/little-terror/little_terror_sheet_v3.png`.

v3 is a **superset of v2**: the same three front-facing rows, plus a "PROFILE
DIRECTIONS" panel beside them and a neutral-stand reference strip below. v2 is
kept only as the fallback if v3 is ever lost.

⚠️ **Crops are measured, not found.** The profile panel sits *beside* rows 2 and
3 rather than under them, so a row scan merges 570px of sheet into one band — and
every row carries a painted caption ("1. WALK", "WIND-UP") that a band scan would
happily hand to the keyer. Both are layout facts no scan can reason about, so the
boxes are written down here where they can be read and corrected.

⚠️ **The sheet has no back-facing walk.** Its neutral-stand strip includes a BACK
pose, but one still frame is not a cycle, so Little Terror can walk toward the
camera and sideways and not away from it. That is the one thing to ask for if she
is ever given the player's full four-way facing.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_terror_sheet.py
"""
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritelib import key_by_fill, slice_strip, strip_columns        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, "assets", "sprites")
SHEET = os.path.expanduser(
    "~/Downloads/the-vidadiyot/monsters/little-terror/little_terror_sheet_v3.png")
BACK_SHEET = os.path.expanduser(
    "~/Downloads/the-vidadiyot/monsters/little-terror/little-terror-back-face-sheet.png")
BACK_ROW = (30, 160, 1490, 240)     # "OPTION A", below its caption and numerals

# Glows key at a higher cut than characters do — see `_pick`.
GLOW_CUT = 42

# Little Terror stands 54px in game — the height every other monster is cut to.
TALL = 54

# name -> (crop, frames). Boxes start *below* each painted caption.
ROWS = {
    "terror_walk":       ((20, 70, 585, 285), 3),
    "terror_cast":       ((20, 400, 585, 285), 3),
    "terror_hurt":       ((20, 735, 585, 230), 3),
    "terror_walk_side":  ((640, 175, 380, 160), 3),
    "terror_cast_side":  ((640, 405, 380, 165), 3),
    "terror_hurt_side":  ((640, 632, 380, 173), 3),
}

# ⚠️ The fire and impact rows are cut by **gutter detection, not even division**.
# Their items are wildly different widths — an ember is 52px and a comet is 156 —
# so splitting the span into equal cells sliced straight through the fireball and
# shipped two half-moons. Even division is only ever right for evenly spaced
# frames; these are a catalogue, and a catalogue has gutters.
FIRE = (20, 995, 1000, 118)
FIREBALL_PICK = 3        # "FIREBALL LARGE": the small one reads as a dot at
                         # speed, and this is a *fireball*
IMPACT = (20, 1175, 470, 105)
IMPACT_PICK = 1          # "RING IMPACT": a burst that is not a starfield

# Bigger than the 14px collision box on purpose: FIREBALL_SIZE is what can hit
# you, and a projectile drawn at exactly its hitbox reads as a pebble.
FIREBALL_H = 30
IMPACT_H = 30


# ⚠️ Each cell of the three front rows carries a small purple ①②③ in its top-left
# corner. They cannot be cropped out vertically — the figure's horns and hair
# reach into the same rows — and they are close enough in brightness to the art
# that no luma cut separates them. They *are* at a fixed offset in every cell,
# though, because the cells are evenly spaced: so they are painted out before the
# strip is cut. Blanking beats keying when the position is known and the colour
# is not.
NUMERAL = (44, 40)          # px of the cell's top-left corner to erase


def _cut(sheet, crop, n, target_h, luma_cut=22, numerals=False):
    x, y, w, h = crop
    sub = pygame.Surface((w, h), pygame.SRCALPHA)
    sub.blit(sheet, (0, 0), crop)
    if numerals:
        step = w / n
        for i in range(n):
            sub.fill((0, 0, 0, 0), (int(i * step), 0, *NUMERAL))
    return slice_strip(sub, target_h, cells=n, luma_cut=luma_cut)


def _pick(sheet, crop, index, target_h, luma_cut=20):
    """One item out of a catalogue row, found by its gutters and keyed hard.

    ⚠️ `luma_cut` matters here in a way it does not for a character. These are
    glows with a soft falloff into the black, and a low cut leaves the falloff
    *opaque* — the impact burst shipped with a visible dark rectangle around it,
    which is what a "box" on screen when something is hit turns out to be.
    """
    x, y, w, h = crop
    sub = pygame.Surface((w, h), pygame.SRCALPHA)
    sub.blit(sheet, (0, 0), crop)
    cols = strip_columns(sub, gutter=14, luma_cut=luma_cut, min_width=20)
    x0, x1 = cols[index]
    cell = pygame.Surface((x1 - x0, h), pygame.SRCALPHA)
    cell.blit(sub, (0, 0), (x0, 0, x1 - x0, h))
    key_by_fill(cell, GLOW_CUT)
    rect = cell.get_bounding_rect()
    trimmed = pygame.Surface(rect.size, pygame.SRCALPHA)
    trimmed.blit(cell, (0, 0), rect)
    scale = target_h / trimmed.get_height()
    return pygame.transform.smoothscale(
        trimmed, (max(1, round(trimmed.get_width() * scale)), target_h))


def _cut_back():
    """Little Terror's back-facing walk, three frames out of an eight-frame row.

    The sheet offers three options of eight frames each; A has the clearest leg
    motion. Frames 0, 2 and 4 are a quarter-cycle apart, which is
    contact / passing / contact — the shape `Entity.PINGPONG` expects.
    """
    if not os.path.exists(BACK_SHEET):
        return []
    sheet = pygame.image.load(BACK_SHEET).convert_alpha()
    eight = _cut(sheet, BACK_ROW, 8, TALL, numerals=True)
    return [eight[0], eight[2], eight[4]]


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    if not os.path.exists(SHEET):
        raise SystemExit(f"no sheet at {SHEET}")
    sheet = pygame.image.load(SHEET).convert_alpha()
    os.makedirs(SPRITES, exist_ok=True)

    for name, (crop, n) in ROWS.items():
        numerals = not name.endswith("_side")     # only the front rows carry them
        for i, f in enumerate(_cut(sheet, crop, n, TALL, numerals=numerals)):
            path = os.path.join(SPRITES, f"{name}_{i}.png")
            pygame.image.save(f, path)
            print(f"  wrote {os.path.relpath(path, ROOT)} "
                  f"({f.get_width()}x{f.get_height()})")

    for name, crop, pick, h in (("fireball", FIRE, FIREBALL_PICK, FIREBALL_H),
                                ("fire_impact", IMPACT, IMPACT_PICK, IMPACT_H)):
        img = _pick(sheet, crop, pick, h)
        pygame.image.save(img, os.path.join(SPRITES, f"{name}.png"))
        print(f"  wrote assets/sprites/{name}.png "
              f"({img.get_width()}x{img.get_height()})")

    back = _cut_back()
    for i, f in enumerate(back):
        path = os.path.join(SPRITES, f"terror_walk_up_{i}.png")
        pygame.image.save(f, path)
        print(f"  wrote {os.path.relpath(path, ROOT)} "
              f"({f.get_width()}x{f.get_height()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
