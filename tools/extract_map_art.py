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
from spritelib import key_by_fill, source                       # noqa: E402

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
    WALL:  ("wall_cinderblock_slab.png", 30, 25, 118),   # above the dado rail
    CORR:  ("corridor_floor_slab.png", 22, 20, 100),     # exactly two checkers
    STONE: ("basement_flagstone_slab.png", 40, 40, 130),
    DOOR:  ("basement_flagstone_slab.png", 200, 60, 70), # threshold = stone underfoot
}
# Second windows on the same parquet slab, so the variants are the same material
# with different grain rather than an obviously different floor.
VARIANT_SAMPLE = {
    FLOOR_CRACK: ("classroom_floor_slab.png", 190, 60, 120),
    FLOOR_STAIN: ("classroom_floor_slab.png", 60, 190, 120),
    FLOOR_ROT:   ("classroom_floor_slab.png", 200, 200, 120),
}
# ...each stamped with one decal off the damage sheet, by cell index.
VARIANT_DECAL = {FLOOR_CRACK: 0, FLOOR_STAIN: 4, FLOOR_ROT: 2}

DECAL_SHEET = "floor_damage_decals_sheet.png"
DECAL_CELLS = 8
DECAL_SCALE = 0.82        # fraction of the tile a decal covers, so it isn't clipped

DOOR_SHEET = "school_doors_sheet.png"
DOOR_CELLS = 3
DOOR_SIZE = (64, 32)      # matches the 2x1 tile doorway punched by gen_map

ITEMS = {                 # sprite name -> (source file, target height)
    "item_book.png":   ("book_neutral.png", 17),
    "item_key.png":    ("key_neutral.png", 15),
    "item_potion.png": ("health_potion.png", 18),
}

SEAM_FEATHER = 0.14       # of the sample size, cross-faded to make the wrap match


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


def variant_tile(gid):
    file_name, x, y, size = VARIANT_SAMPLE[gid]
    tile = material_tile(file_name, x, y, size)
    stamp = decal(VARIANT_DECAL[gid], int(TILE * DECAL_SCALE))
    off = (TILE - stamp.get_width()) // 2
    tile.blit(stamp, (off, off))
    return tile


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
            if gid in VARIANT_SAMPLE:
                tile = variant_tile(gid)
            else:
                tile = material_tile(*SLABS[gid])
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
        pygame.image.save(pygame.transform.smoothscale(img, DOOR_SIZE),
                          os.path.join(SPRITES, name))


def extract_items():
    """Book, key and potion at pickup size.

    These stay **bright** — §1's rule is that anything you can pick up or be
    killed by has to read against a dark floor, which is the one place the
    dark-and-desaturated rule is deliberately broken.
    """
    for name, (src_name, target_h) in ITEMS.items():
        img = _keyed_crop(pygame.image.load(source(src_name)).convert_alpha())
        scale = target_h / img.get_height()
        out = pygame.transform.smoothscale(
            img, (max(1, round(img.get_width() * scale)), target_h))
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
