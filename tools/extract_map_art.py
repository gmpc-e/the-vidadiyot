"""Extract the Phase 1 map art into runtime assets (roadmap §1).

Source: `~/Downloads/the-vidadiyot/map/`, painted at 1536x1024 and delivered as
crops off one master sheet. This tool turns it into three things:

* **The tileset** (`assets/tilesets/school.png`) — the flat-colour rectangles the
  map has always been made of, replaced with real material.
* **Item sprites** — book, key, potion, which are code primitives today.
* **Door sprites** — closed and open, likewise.

Two decisions worth knowing before editing this file:

**Tiles are cut from big slabs, never painted at 32px.** Image models cannot
paint a truly seamless 32x32 tile — the edges never register. So the art was
commissioned as large slabs of *material* and the seam is fixed here, by
`make_seamless()`: sample a window `f` pixels wider than the tile, then cross-fade
the run that would follow the right edge back over the left edge (and the same
vertically). The result wraps exactly, at the cost of a soft band `f` px wide
that vanishes at 32px. Run with `--preview` to write 3x3 repeats and check.

**The wall slab is an elevation, not a top-down patch.** It arrived with a dado
rail across it and a skirting strip along the bottom — both strong horizontal
features that would tile into stripes. `WALL_SAMPLE` deliberately sits in the
plain cinderblock above the rail. If the wall ever looks banded, that window
drifted down into the rail.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_map_art.py [--preview]
"""
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritelib import brighten, key_by_fill, source             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILESET_PNG = os.path.join(ROOT, "assets", "tilesets", "school.png")
SPRITES = os.path.join(ROOT, "assets", "sprites")
PREVIEW_DIR = os.path.join(ROOT, "assets", "previews")

TILE = 32

# ── the tile catalogue ───────────────────────────────────────────────────---
# Order is the tileset's column order and therefore the map's GIDs (1-based), so
# **appending is safe and reordering silently rewrites every map**. `gen_map.py`
# imports these names; `solid` is written into the .tmx as the tile property
# `tilemap.py` reads to build collision.
FLOOR, WALL, CORR, DOOR, FLOOR_CRACK, FLOOR_STAIN, FLOOR_ROT, STONE = range(1, 9)

TILE_NAMES = {
    FLOOR: "classroom floor", WALL: "wall", CORR: "corridor floor",
    DOOR: "doorway threshold", FLOOR_CRACK: "floor, cracked",
    FLOOR_STAIN: "floor, stained", FLOOR_ROT: "floor, rotted", STONE: "stone floor",
}
SOLID_TILES = (WALL,)

# Fallback colours, used when the painted slabs aren't on this machine. The art
# lives in ~/Downloads, not in the repo, so a checkout without it still has to be
# able to regenerate a playable (if ugly) map.
FALLBACK = {
    FLOOR: (46, 46, 54), WALL: (74, 70, 82), CORR: (38, 40, 50), DOOR: (122, 92, 58),
    FLOOR_CRACK: (42, 42, 50), FLOOR_STAIN: (40, 40, 48), FLOOR_ROT: (38, 38, 46),
    STONE: (44, 44, 50),
}

# Where each material is sampled from its slab: (file, x, y, size). `size` is the
# source window that becomes one 32px tile, so it sets the *scale* of the
# material in game — a 100px window on a checkerboard of 50px squares puts two
# squares in a tile, i.e. 16px squares on screen.
SLABS = {
    FLOOR: ("classroom_floor_slab.png", 40, 40, 120),
    # ⚠️ Wall and threshold are the **v2 re-paints** requested through
    # `tools/art_request.py` (§R1, §R2). The originals failed differently:
    #   * the first wall was an *elevation* with a dado rail and skirting painted
    #     across it, so it tiled into stripes — only the narrow band of plain
    #     block above the rail could be sampled at all (uniformity 2.28; the
    #     re-paint measures 1.18);
    #   * the first "threshold" was a door frame in perspective rather than a
    #     piece of floor, so dark flagstone stood in for it.
    # Both v2 sheets are letterboxed — the model centres a square swatch and pads
    # it with black — which is where the offsets come from. `art_request.py
    # --check --material` prints the content box if they need re-deriving.
    WALL:  ("wall_v2.png", 470, 250, 512),
    # Planks fill x 380..1160, y 190..630, above the brass edging strip. The
    # window is small on purpose: the planks are ~64px wide on the sheet, so a
    # 380px window crushed six of them into one tile and the wood read as
    # masonry. 200px puts about three planks in a tile.
    DOOR:  ("threshold_v2.png", 450, 280, 200),
    CORR:  ("corridor_floor_slab.png", 22, 20, 100),     # exactly two checkers
    STONE: ("basement_flagstone_slab.png", 40, 40, 130),
}
# ⚠️ The **v2 re-paint** (§R3). The first attempt came back as straight
# horizontal planks while the classroom floor these scatter through is
# herringbone parquet — three patches of a *different floor* rather than damage
# to this one. These are the same herringbone, which was the point of re-asking.
# The windows sit deliberately off-centre: each swatch has its damage centred,
# and a centred feature sampled into a 32px tile becomes a stamp repeated across
# the whole room.
# No decal is blitted over these any more. The variants used to be faked — clean
# parquet with a damage decal stamped on — and when the painted ones arrived the
# stamping was still running, so a swatch that already had a water stain got a
# second, code-drawn puddle on top of it.
VARIANT_SAMPLE = {
    FLOOR_CRACK: ("floor_variants_v2.png",  110, 330, 320),   # split, lifted boards
    FLOOR_STAIN: ("floor_variants_v2.png",  580, 330, 320),   # water-damaged bloom
    FLOOR_ROT:   ("floor_variants_v2.png", 1050, 330, 320),   # mould along the seams
}

DECAL_SHEET = "floor_damage_decals_sheet.png"
DECAL_CELLS = 8
DECAL_SCALE = 0.82        # fraction of the tile a decal covers, so it isn't clipped

DOOR_SHEET = "school_doors_sheet.png"
DOOR_CELLS = 3
DOOR_SIZE = (64, 32)      # matches the 2x1 tile doorway punched by gen_map

# sprite name -> (source file, target height, brighten gamma)
# The gamma is not optional. These were painted lit for a big canvas, and §1's
# one exception to "environment dark" is that anything you can pick up or use
# must stay legible — the iron key in particular went straight to unreadable
# against the HUD's dark panel at 15px.
ITEMS = {
    "item_book.png":   ("book_neutral.png", 17, 1.25),
    "item_key.png":    ("key_neutral.png", 15, 1.75),
    "item_potion.png": ("health_potion.png", 18, 1.2),
}
DOOR_GAMMA = 1.5          # same rule: a door is an interactable, not scenery

SEAM_FEATHER = 0.14       # of the sample size, cross-faded to make the wrap match

# Tone correction applied after the downscale: (brightness, saturation).
# The slabs were painted to look good big and lit, the same reason
# `spritelib.brighten` exists for the characters — except here it runs the other
# way. In game the cinderblock came out *brighter than the floor it borders*,
# which inverts §1's rule: the environment is background, and a wall that glows
# pulls the eye off the monster standing in front of it. It was olive-green too,
# so the saturation comes down with it. Nothing else needed touching.
TONE = {
    WALL: (0.62, 0.5),
    # The v2 floor variants were painted brighter than the base parquet they
    # scatter through — the cracked one at mean luma 56 against the floor's 38,
    # which at a 9% sprinkle reads as pale patches rather than as wear. Matched
    # by eye to the floor rather than by formula; the other two were close
    # enough already to leave alone.
    FLOOR_CRACK: (0.70, 0.85),
}


# ── seamless tiling ──────────────────────────────────────────────────────---
def _alpha_ramp(w, h, feather, horizontal):
    """A mask that is opaque at one edge and fades to nothing `feather` px in."""
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(feather):
        a = int(255 * (1.0 - i / feather))
        if horizontal:
            pygame.draw.line(mask, (255, 255, 255, a), (i, 0), (i, h - 1))
        else:
            pygame.draw.line(mask, (255, 255, 255, a), (0, i), (w - 1, i))
    return mask


def make_seamless(surf, feather):
    """Return the top-left size-`n` square of `surf`, wrapped to tile exactly.

    `surf` must be (n + feather) on a side: the extra strip is what *would* come
    after the tile's right/bottom edge, cross-faded back over its left/top edge
    so the two ends meet. Cheap, and invisible once the tile is 32px.
    """
    n = surf.get_width() - feather
    out = pygame.Surface((n, n), pygame.SRCALPHA)
    out.blit(surf, (0, 0), (0, 0, n, n))
    for horizontal in (True, False):
        # the run that follows the far edge, moved to the near edge
        w, h = (feather, n) if horizontal else (n, feather)
        strip = pygame.Surface((w, h), pygame.SRCALPHA)
        strip.blit(out, (0, 0), (n, 0, w, h) if horizontal else (0, n, w, h))
        # ...only that lives on `surf`, which still has the overhang
        strip.fill((0, 0, 0, 0))
        strip.blit(surf, (0, 0), (n, 0, w, h) if horizontal else (0, n, w, h))
        strip.blit(_alpha_ramp(w, h, feather, horizontal), (0, 0),
                   special_flags=pygame.BLEND_RGBA_MULT)
        out.blit(strip, (0, 0))
    return out


def _sample(file_name, x, y, size, feather):
    """One (size + feather) window of a slab, as a seamless `size` square."""
    slab = pygame.image.load(source(file_name)).convert_alpha()
    win = pygame.Surface((size + feather, size + feather), pygame.SRCALPHA)
    win.blit(slab, (0, 0), (x, y, size + feather, size + feather))
    return make_seamless(win, feather)


def material_tile(file_name, x, y, size):
    feather = max(4, int(size * SEAM_FEATHER))
    return pygame.transform.smoothscale(
        _sample(file_name, x, y, size, feather), (TILE, TILE))


def tone(surf, brightness, saturation):
    """Darken and desaturate in place — a tile is small enough to do per-pixel."""
    w, h = surf.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, a = surf.get_at((x, y))
            grey = 0.299 * r + 0.587 * g + 0.114 * b
            surf.set_at((x, y), tuple(
                min(255, max(0, int((grey + (c - grey) * saturation) * brightness)))
                for c in (r, g, b)) + (a,))
    return surf


# ── decals ───────────────────────────────────────────────────────────────---
def key_decal(surf, cut=20, soft=46):
    """Lift a decal off its black cell: fill away the surround, then soften.

    Neither strategy in `spritelib` fits a decal. A plain fill leaves the outer
    fringe fully opaque, so a soft-edged stain gains a hard rim; a plain
    luminance ramp erases the decal, because a *dark water stain painted on
    black* is barely above the background it has to be separated from. So: fill
    the connected black surround away, then ramp alpha over the remaining dark
    fringe only. A dark stain ends up semi-transparent, which is the correct
    result — it should darken the floor it sits on, not replace it.
    """
    key_by_fill(surf, cut)
    w, h = surf.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, a = surf.get_at((x, y))
            if not a:
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < soft:
                surf.set_at((x, y), (r, g, b, int(255 * lum / soft)))
    return surf


def decal(index, size):
    sheet = pygame.image.load(source(DECAL_SHEET)).convert_alpha()
    cell_w = sheet.get_width() // DECAL_CELLS
    cell = pygame.Surface((cell_w, sheet.get_height()), pygame.SRCALPHA)
    cell.blit(sheet, (0, 0), (index * cell_w, 0, cell_w, sheet.get_height()))
    key_decal(cell)
    rect = cell.get_bounding_rect()
    trimmed = pygame.Surface(rect.size, pygame.SRCALPHA)
    trimmed.blit(cell, (0, 0), rect)
    return pygame.transform.smoothscale(trimmed, (size, size))


# ── the tileset ──────────────────────────────────────────────────────────---
def _flat(gid):
    tile = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    tile.fill(FALLBACK[gid])
    pygame.draw.rect(tile, tuple(max(0, c - 8) for c in FALLBACK[gid]),
                     (0, 0, TILE, TILE), 1)
    return tile


def build_tileset():
    """Write the tileset strip. Returns (width, height, used_source_art)."""
    gids = sorted(TILE_NAMES)
    strip = pygame.Surface((TILE * len(gids), TILE), pygame.SRCALPHA)
    painted = True
    for i, gid in enumerate(gids):
        try:
            tile = material_tile(*(VARIANT_SAMPLE.get(gid) or SLABS[gid]))
            if gid in TONE:
                tone(tile, *TONE[gid])
        except FileNotFoundError:
            painted = False
            tile = _flat(gid)
        strip.blit(tile, (i * TILE, 0))
    os.makedirs(os.path.dirname(TILESET_PNG), exist_ok=True)
    pygame.image.save(strip, TILESET_PNG)
    return strip.get_width(), strip.get_height(), painted


# ── sprites cut off the prop sheets ──────────────────────────────────────---
def _cell(sheet_name, index, count):
    sheet = pygame.image.load(source(sheet_name)).convert_alpha()
    cw = sheet.get_width() // count
    cell = pygame.Surface((cw, sheet.get_height()), pygame.SRCALPHA)
    cell.blit(sheet, (0, 0), (index * cw, 0, cw, sheet.get_height()))
    return cell


def _keyed_crop(surf, cut=26):
    key_by_fill(surf, cut)
    rect = surf.get_bounding_rect()
    if not rect.width or not rect.height:
        raise ValueError("crop keyed away to nothing — luma cut too high?")
    out = pygame.Surface(rect.size, pygame.SRCALPHA)
    out.blit(surf, (0, 0), rect)
    return out


def extract_doors():
    """Closed and open door leaves, squashed to the 2x1 tile doorway.

    The third cell on the sheet is an empty frame; the game draws the open door
    as a dark threshold with the leaf swung aside, so it is not used.
    """
    for name, index in (("door_closed.png", 0), ("door_open.png", 1)):
        img = _keyed_crop(_cell(DOOR_SHEET, index, DOOR_CELLS))
        out = pygame.transform.smoothscale(img, DOOR_SIZE)
        brighten(out, DOOR_GAMMA)
        pygame.image.save(out, os.path.join(SPRITES, name))


def extract_items():
    """Book, key and potion at pickup size.

    These stay **bright** — §1's rule is that anything you can pick up or be
    killed by has to read against a dark floor, which is the one place the
    dark-and-desaturated rule is deliberately broken.
    """
    for name, (src_name, target_h, gamma) in ITEMS.items():
        img = _keyed_crop(pygame.image.load(source(src_name)).convert_alpha())
        scale = target_h / img.get_height()
        out = pygame.transform.smoothscale(
            img, (max(1, round(img.get_width() * scale)), target_h))
        brighten(out, gamma)
        pygame.image.save(out, os.path.join(SPRITES, name))


# ── preview ──────────────────────────────────────────────────────────────---
def write_previews():
    """A 3x3 repeat of every tile — the only honest test of a seam."""
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    strip = pygame.image.load(TILESET_PNG).convert_alpha()
    gids = sorted(TILE_NAMES)
    sheet = pygame.Surface((TILE * 3 * len(gids) + 8 * len(gids), TILE * 3),
                           pygame.SRCALPHA)
    for i, gid in enumerate(gids):
        tile = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        tile.blit(strip, (0, 0), ((gid - 1) * TILE, 0, TILE, TILE))
        ox = i * (TILE * 3 + 8)
        for ty in range(3):
            for tx in range(3):
                sheet.blit(tile, (ox + tx * TILE, ty * TILE))
    path = os.path.join(PREVIEW_DIR, "tiles_3x3.png")
    pygame.image.save(pygame.transform.scale(
        sheet, (sheet.get_width() * 2, sheet.get_height() * 2)), path)
    return path


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(SPRITES, exist_ok=True)
    w, h, painted = build_tileset()
    print(f"wrote {TILESET_PNG} ({w}x{h}, {len(TILE_NAMES)} tiles)"
          + ("" if painted else "  ⚠️  SOURCE ART MISSING — flat colours"))
    if painted:
        extract_doors()
        extract_items()
        print(f"wrote door + item sprites into {SPRITES}")
    if "--preview" in sys.argv:
        print(f"wrote {write_previews()}")


if __name__ == "__main__":
    main()
