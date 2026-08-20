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


def flatten_color(surf, rgb, alpha=1.0):
    """Repaint every visible pixel a single colour, keeping the alpha shape.

    ⚠️ **For thin bright line art, the colour does not survive a big downscale
    and the alpha does.** A cobweb is 1px strands of pale silk on black; scaled
    from 200px to 30px, `smoothscale` averages each strand with the black around
    it and the result is a dark smudge at luma 12-17 — which is what the first
    extraction shipped. The *shape* is intact in the alpha channel the whole
    time, so the fix is to throw the averaged colour away and paint the mask a
    constant instead.

    Only use this where the subject genuinely is one colour. A lamp or a pipe has
    real shading and this would flatten it into a silhouette.

    ⚠️ `alpha` scales the mask, and it matters. The same downscale that dulls the
    colour *spreads* each strand across its neighbours, so the mask comes out
    broad and fairly opaque — repainted at full strength a web stops looking like
    strands and becomes a solid pale sheet, the brightest thing on a screen whose
    whole rule is "environment dark, actors bright".
    """
    out = surf.copy()
    w, h = out.get_size()
    for x in range(w):
        for y in range(h):
            a = out.get_at((x, y))[3]
            if a:
                out.set_at((x, y), (*rgb, min(255, int(a * alpha))))
    return out


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


# ── animation strips (Phase 2) ────────────────────────────────────────────
# A strip is one horizontal row of N frames on black, delivered by §A of
# `docs/ART_PROMPTS_PHASE2.md`. Cutting one is *not* the same job as cutting N
# separate props, and the difference is the whole reason this lives here rather
# than being N calls to `extract_pose`:
#
# ⚠️ **One scale for the whole strip, and one baseline.** Fitting each frame to
# its own height is the obvious implementation and it is wrong in a way that is
# invisible until the thing moves: a frame where the character raises its arms
# is *taller*, so normalising per frame shrinks the body on exactly the frame
# that should look biggest, and the sprite pulses as it plays. The strip is
# measured as a whole, scaled once, and every frame is pinned to the same
# bottom edge.
STRIP_GUTTER = 20        # px of black columns that separate two frames
STRIP_MIN_W = 24         # narrower than this is speckle, not a frame


def strip_columns(sheet, gutter=STRIP_GUTTER, luma_cut=24, min_width=STRIP_MIN_W):
    """(left, right) of each frame in a horizontal strip, left to right."""
    w, h = sheet.get_size()
    lit = [any(_luma(sheet.get_at((x, y))) > luma_cut for y in range(0, h, 2))
           for x in range(w)]
    out, run, empty = [], None, 0
    for x in range(w):
        if lit[x]:
            run, empty = (x if run is None else run), 0
        elif run is not None:
            empty += 1
            if empty >= gutter:
                out.append((run, x - empty))
                run = None
    if run is not None:
        out.append((run, w - 1))
    return [c for c in out if c[1] - c[0] >= min_width]


def strip_rows(sheet, gutter=6, luma_cut=24, min_height=40):
    """(top, bottom) of each band of content — for a sheet laid out as a grid.

    Hand-made sheets arrive as a grid of poses rather than as one strip per
    file, which is a *better* way to commission art (one request, one consistent
    character) and only costs a row scan here.

    ⚠️ `gutter` is small on purpose. Roni's sheet separates two rows by **7px** —
    a flaring cape below and flying hair above eat the gap — and at the original
    12px the two rows merged into one 634px band holding six figures. Splitting a
    figure in half is the opposite risk, and it is loud: the frame-count
    assertion in `slice_strip` catches it immediately.
    """
    w, h = sheet.get_size()
    # ⚠️ A row counts as empty when it is *nearly* empty, not perfectly empty.
    # On Roni's sheet a single stray lit pixel sat in the 7px gap between two
    # rows, and an `any()` test bridged them into one 634px band holding six
    # figures. One pixel is a speck of cape; two is content.
    lit = [sum(1 for x in range(0, w, 3)
               if _luma(sheet.get_at((x, y))) > luma_cut) > 2
           for y in range(h)]
    out, run, empty = [], None, 0
    for y in range(h):
        if lit[y]:
            run, empty = (y if run is None else run), 0
        elif run is not None:
            empty += 1
            if empty >= gutter:
                out.append((run, y - empty))
                run = None
    if run is not None:
        out.append((run, h - 1))
    return [r for r in out if r[1] - r[0] >= min_height]


def slice_strip(sheet, target_h, expect=None, luma_cut=24, mode=MODE_FILL,
                gutter=STRIP_GUTTER, band=None, cols=None, cells=None):
    """Cut a delivered strip into game-ready frames.

    `target_h` is the height of the **tallest** frame after scaling, so a
    wind-up that reaches overhead is what sets the scale and the standing frames
    come out correspondingly shorter — which is the truth about the pose, not a
    defect. Frames are returned bottom-aligned on a common canvas, so blitting
    them at one position needs no per-frame offset.
    """
    if band is not None:
        y0, y1 = band
        row = pygame.Surface((sheet.get_width(), y1 - y0), pygame.SRCALPHA)
        row.blit(sheet, (0, 0), (0, y0, sheet.get_width(), y1 - y0))
        sheet = row
    if cells:
        # ⚠️ **Even division, for sheets not drawn to the gutter rule.** The
        # trapped-warrior sheets trail web strands *between* frames, so the
        # figures are joined and gutter detection reads a whole row as one item.
        # When the frames are evenly spaced, splitting the lit span into N is
        # exact enough — a clipped strand costs nothing, a merged row costs the
        # sheet. Never use this on art that *does* have gutters: it will slice
        # through a subject that happens to sit off-centre in its cell.
        lit = [x for x in range(sheet.get_width())
               if any(_luma(sheet.get_at((x, y))) > luma_cut
                      for y in range(0, sheet.get_height(), 3))]
        if not lit:
            raise SystemExit("nothing lit in this band")
        step = (lit[-1] - lit[0] + 1) / cells
        found = [(int(lit[0] + i * step), int(lit[0] + (i + 1) * step) - 1)
                 for i in range(cells)]
    else:
        found = strip_columns(sheet, gutter=gutter, luma_cut=luma_cut)
    # A hand-made row often carries more than one animation — walk in the first
    # three cells, something else in the rest. `cols` takes a slice of it.
    if cols is not None:
        lo, hi = cols
        if hi > len(found):
            raise SystemExit(f"row has {len(found)} cells, asked for {lo}:{hi} "
                             f"(at {found})")
        found = found[lo:hi]
    cols = found
    if expect is not None and len(cols) != expect:
        raise SystemExit(
            f"strip has {len(cols)} frames, expected {expect} (at {cols}).\n"
            f"  Fewer means two frames are touching — the sheet needs wider "
            f"black gutters, which is §A's 'nothing touching' clause. More means "
            f"a frame broke into pieces. Re-roll the sheet; widening `gutter` "
            f"here only hides it.")

    # ⚠️ Frames are kept in **their own cell's coordinates**, not re-centred on
    # their content. A swing frame is much wider than a standing one because the
    # blade sticks out to one side; centring each trimmed frame puts the *body*
    # in a different place every frame, so the character slides sideways as it
    # attacks. The cells are evenly spaced and the body sits at the same place in
    # each — which is what registration means — so preserving the offset within
    # the cell keeps the body still and lets the sword extend where it likes.
    cell_w = max(x1 - x0 for x0, x1 in cols)
    cut = []
    for x0, x1 in cols:
        cell = pygame.Surface((cell_w, sheet.get_height()), pygame.SRCALPHA)
        cell.blit(sheet, (0, 0), (x0, 0, x1 - x0, sheet.get_height()))
        if mode == MODE_RAMP:
            key_by_ramp(cell, luma_cut, feather=0)
        else:
            key_by_fill(cell, luma_cut)
        rect = cell.get_bounding_rect()
        if not rect.width or not rect.height:
            raise SystemExit(f"strip frame at x={x0} keyed away to nothing")
        cut.append((cell, rect))

    # Crop every cell to the *union* of their content boxes, so each frame keeps
    # its horizontal offset and they still share one canvas.
    union = cut[0][1].unionall([r for _, r in cut[1:]])
    scale = target_h / union.height
    out = []
    for cell, _ in cut:
        piece = pygame.Surface(union.size, pygame.SRCALPHA)
        piece.blit(cell, (0, 0), union)
        out.append(pygame.transform.smoothscale(
            piece, (max(1, round(union.width * scale)), target_h)))
    return out
