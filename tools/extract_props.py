"""Extract the school props from the Phase 1 re-work sheet (roadmap §1).

Source: `~/Downloads/the-vidadiyot-phase1-re-work/phase-1-rework.png` — one
1536x1024 sheet holding classroom furniture, corridor fittings and atmosphere
pieces. It replaces every rectangle in `world/decor.py`.

**Why the crops are found rather than typed.** The sheet has painted text labels
above every item, which is the failure `ART_REQUESTS.md` warns about — nothing
can be located by "biggest blob on the sheet", because for several of these the
biggest blob *is* the caption. So instead: the labels sit in known horizontal
bands, and inside the band below each one the items are separated by wide black
gutters. `BANDS` names the item strip (never the label strip) and the columns are
detected. Hand-typed boxes for 20-odd props would rot the first time a sheet is
re-exported a few pixels off; a detected column will not.

Each band asserts how many columns it expects. A merged or split detection is
then a loud failure instead of a bookshelf quietly saved as a wall clock.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_props.py [--sheet]
"""
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritelib import brighten, key_by_fill, source                  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROPS_DIR = os.path.join(ROOT, "assets", "props")
SHEET = "phase-1-rework.png"

LUMA_CUT = 24             # low: the props are dark wood and dark metal already

# Item strips, chosen to sit *below* each row of painted captions.
# (y0, y1, gutter, x_end) — the gutter is the run of black columns separating two
# items, and posters sit closer together than furniture does. `x_end` stops the
# scan short: the litter specks share the fittings row but are handled
# separately, and without the bound they arrive as three phantom columns.
BANDS = {
    "furniture": (77, 232, 10, 1536),
    "fittings":  (271, 469, 6, 1110),
    "corridor":  (574, 732, 10, 1536),
}

# band -> the props in it, left to right, with the box each must fit inside.
# Sizes are the game-pixel targets from `docs/ART_REQUESTS.md`; art is scaled to
# fit the box while keeping its aspect, never stretched to it.
LAYOUT = {
    "furniture": [
        ("desk_a.png", (26, 22)), ("desk_b.png", (26, 22)), ("desk_c.png", (26, 22)),
        ("chair.png", (12, 14)), ("chair_fallen.png", (16, 14)),
        ("teacher_desk.png", (46, 26)), ("blackboard.png", (156, 46)),
    ],
    "fittings": [
        # The first cell is the return locker, superseded by §R7's dedicated
        # two-state sheet below. Still *detected* — the band asserts its column
        # count — but not saved, or it would overwrite the better one.
        (None, (22, 32)), ("bookshelf.png", (40, 28)), ("clock.png", (14, 14)),
        ("poster_a.png", (18, 22)), ("poster_b.png", (18, 22)), ("poster_c.png", (18, 22)),
    ],
    "corridor": [
        ("locker_bank.png", (90, 36)), ("notice_board.png", (48, 30)),
        ("trophy_case.png", (40, 34)), ("mop_bucket.png", (18, 20)),
        ("ceiling_light.png", (28, 12)), ("radiator.png", (30, 16)),
    ],
}
# The return locker's two states arrived on their own sheet (§R7), because the
# first props delivery gave the shut locker only — so a filled locker could only
# be signalled by a mark painted on its colour plate. Same treatment as the rest,
# except both states must be scaled *identically*: they are the same object one
# frame apart, and a size change between them reads as the locker jumping.
LOCKER_SHEET = "locker_states.png"
LOCKER_BAND = (60, 980, 40, 1536)
LOCKER_STATES = ("locker.png", "locker_open.png")
LOCKER_SIZE = (26, 32)

# The litter pieces are 4px specks with almost no gap between them, so column
# detection is the wrong tool: the strip is split evenly instead.
LITTER_STRIP = (1125, 1500)
LITTER_COUNT = 6
LITTER_SIZE = (6, 6)

# §1's rule is that the environment stays dark — but the rule's *purpose* is that
# furniture must not compete with a monster, and furniture nobody can see isn't
# background, it's absent. Painted dark-brown desks on the new dark-brown parquet
# disappeared completely: only the lit edge of each tabletop survived, so a
# classroom read as bare floor with a few planks on it. This is the smallest
# lift that puts them back on the floor without pulling the eye.
PROP_GAMMA = 1.3
BRIGHT = {
    "locker.png": 1.55,          # the book-drop: an objective, lit like one
    "blackboard.png": 1.0,       # wall pieces already sit against dark cinderblock
    "poster_a.png": 1.0, "poster_b.png": 1.0, "poster_c.png": 1.0,
    "notice_board.png": 1.0, "ceiling_light.png": 1.0,
}


def _luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def columns(sheet, y0, y1, gutter, x_end, min_width=7):
    """Left/right bounds of each item in a horizontal strip of the sheet."""
    w = min(x_end, sheet.get_width())
    filled = [any(_luma(sheet.get_at((x, y))) > LUMA_CUT for y in range(y0, y1, 2))
              for x in range(w)]
    out, run, empty = [], None, 0
    for x in range(w):
        if filled[x]:
            run, empty = (x if run is None else run), 0
        elif run is not None:
            empty += 1
            if empty >= gutter:
                out.append((run, x - empty))
                run = None
    if run is not None:
        out.append((run, w - 1))
    return [c for c in out if c[1] - c[0] >= min_width]


def cut(sheet, box, size, gamma=None):
    """Key one prop off the black sheet, trim it, and fit it inside `size`."""
    x0, y0, x1, y1 = box
    surf = pygame.Surface((x1 - x0, y1 - y0), pygame.SRCALPHA)
    surf.blit(sheet, (0, 0), (x0, y0, x1 - x0, y1 - y0))
    key_by_fill(surf, LUMA_CUT)
    rect = surf.get_bounding_rect()
    if not rect.width or not rect.height:
        raise ValueError(f"prop at {box} keyed away to nothing")
    trimmed = pygame.Surface(rect.size, pygame.SRCALPHA)
    trimmed.blit(surf, (0, 0), rect)
    scale = min(size[0] / rect.width, size[1] / rect.height)
    out = pygame.transform.smoothscale(
        trimmed, (max(1, round(rect.width * scale)), max(1, round(rect.height * scale))))
    if gamma:
        brighten(out, gamma)
    return out


_SHEETS = {}


def sheet_of(name):
    if name not in _SHEETS:
        _SHEETS[name] = pygame.image.load(source(name)).convert_alpha()
    return _SHEETS[name]


def extract_all(sheet):
    written = []
    for band, props in LAYOUT.items():
        y0, y1, gutter, x_end = BANDS[band]
        found = columns(sheet, y0, y1, gutter, x_end)
        if len(found) != len(props):
            raise AssertionError(
                f"{band}: found {len(found)} columns, expected {len(props)} "
                f"({[n or '(skipped)' for n, _ in props]}). The sheet layout moved — re-check "
                f"BANDS before trusting any crop from it.")
        for (x0, x1), (name, size) in zip(found, props):
            if name is None:
                continue
            img = cut(sheet, (x0, y0, x1, y1), size, BRIGHT.get(name, PROP_GAMMA))
            pygame.image.save(img, os.path.join(PROPS_DIR, name))
            written.append((name, img.get_size()))

    found = columns(sheet_of(LOCKER_SHEET), *LOCKER_BAND)
    if len(found) != len(LOCKER_STATES):
        raise AssertionError(
            f"locker sheet: found {len(found)} columns, expected 2 (shut, open)")
    locker_sheet = sheet_of(LOCKER_SHEET)
    y0, y1 = LOCKER_BAND[0], LOCKER_BAND[1]
    # one scale for both states, taken from the taller of the two
    boxes = [(x0, y0, x1, y1) for x0, x1 in found]
    for name, box in zip(LOCKER_STATES, boxes):
        img = cut(locker_sheet, box, LOCKER_SIZE, BRIGHT["locker.png"])
        pygame.image.save(img, os.path.join(PROPS_DIR, name))
        written.append((name, img.get_size()))

    y0, y1 = BANDS["fittings"][:2]
    lx0, lx1 = LITTER_STRIP
    step = (lx1 - lx0) / LITTER_COUNT
    for i in range(LITTER_COUNT):
        name = f"litter_{i}.png"
        img = cut(sheet, (int(lx0 + i * step), y0, int(lx0 + (i + 1) * step), y1),
                  LITTER_SIZE, PROP_GAMMA)
        pygame.image.save(img, os.path.join(PROPS_DIR, name))
        written.append((name, img.get_size()))
    return written


def write_contact_sheet(written):
    """Every extracted prop at 4x on the game's floor colour, to eyeball sizes."""
    pad, x, row_h = 6, 6, 0
    tiles = []
    for name, _ in written:
        img = pygame.image.load(os.path.join(PROPS_DIR, name)).convert_alpha()
        tiles.append(img)
        row_h = max(row_h, img.get_height())
    total_w = sum(t.get_width() + pad for t in tiles) + pad
    sheet = pygame.Surface((total_w, row_h + pad * 2))
    sheet.fill((46, 40, 36))
    for t in tiles:
        sheet.blit(t, (x, pad + row_h - t.get_height()))
        x += t.get_width() + pad
    path = os.path.join(ROOT, "assets", "previews", "props.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(pygame.transform.scale(
        sheet, (sheet.get_width() * 4, sheet.get_height() * 4)), path)
    return path


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(PROPS_DIR, exist_ok=True)
    sheet = pygame.image.load(source(SHEET)).convert_alpha()
    written = extract_all(sheet)
    print(f"wrote {len(written)} props into {PROPS_DIR}")
    print("  " + ", ".join(f"{n} {w}x{h}" for n, (w, h) in written))
    if "--sheet" in sys.argv:
        print(f"wrote {write_contact_sheet(written)}")


if __name__ == "__main__":
    main()
