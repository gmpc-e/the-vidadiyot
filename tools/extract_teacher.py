"""Extract the teacher monsters from their character sheets (roadmap §2.12).

Source: `~/Downloads/the-vidadiyot/monsters/teacher_*_sheet*.png` — one sheet per
teacher, holding four full-length poses in a row (MAIN / IDLE / WALK / ATTACK)
plus, on the female sheet only, the shared flying-book projectile.

**The poses are found, not typed.** `extract_terror.py` and friends carry
hand-measured crops (`CROP = (497, 472, 216, 256)`), which is fine for a sheet
that arrives once and never again — and these sheets are generated through
`art_request.py`, so a re-roll lands the figures somewhere else every time.

**Why not `extract_props.columns()`, which does exactly this for the props.**
Column detection assumes every item owns a vertical slice of the sheet, and on a
character sheet that is false: the ATTACK pose throws both arms overhead and the
projectile sits in the gap under one of them, so the two share a range of x and
no black gutter separates them. Scanned by column they merge into one item.
Connected components do not care about the interleaving — the figure and the
book are simply not touching — so blobs are labelled and then classified by
height: a **pose spans most of the band**, and anything shorter is the extra
item. That also picks up the loose torn pages as part of the projectile without
naming them.

The pose count is asserted. A merged pair or a phantom blob is then a loud
failure rather than the WALK pose quietly saved as the game sprite.

**Scale is set once, across all four poses.** Each pose must not be normalised to
its own height: ATTACK reaches both arms overhead, so fitting it to 54px like
the others would shrink the *body* by a third and the monster would visibly
shrink whenever it cast. One scale factor is derived from the MAIN pose and
applied to all of them.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_teacher.py [--sheet]
"""
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritelib import brighten, key_by_fill                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, "assets", "sprites")
SRC_DIR = os.path.expanduser("~/Downloads/the-vidadiyot/monsters")

LUMA_CUT = 20              # the teachers are painted dark; key tight or lose the coat

# The in-game monster sprite is measured by height — 54px is what Little Terror
# and Little Snir already stand at, and a new monster that does not match them
# reads as being a different distance away.
TARGET_H = 54
# ...but the MENU art is the MAIN pose at portrait size, matching `make_menu_art`.
MENU_H = 268

# Painted characters arrive darker than the brief asks for — §R8 spends a
# paragraph on it and the delivery still came back at roughly wall brightness.
# The invariant is "environment dark, actors bright", so the lift happens here
# rather than by re-rolling the sheet until the model complies.
LIFT = 1.35

# pose index -> what it becomes. WALK and ATTACK are cut but not yet used: the
# monster draws one static sprite (`Monster.draw`), so they are here waiting for
# the Phase 2 animation work rather than being thrown away and re-cut later.
POSES = ("main", "idle", "walk", "attack")

# Which pose becomes `<name>.png`, the sprite the game actually draws. MAIN, not
# IDLE — §R8 defines MAIN as "the clearest full view of the design", and the
# male sheet proved why that matters: the model drew his IDLE pose with his eyes
# shut and **no glasses at all**, and the broken glasses are the one feature that
# survives being shrunk to 54px. A pose the model treats as a variation is the
# wrong place to take the canonical sprite from.
GAME_POSE = "main"

SHEETS = {
    # name       sheet file                poses  extra item in the corner?
    "teacher_f": ("teacher_f_sheet_v3.png", 4, True),
    # §R9 tells the model not to paint a projectile on the male sheet — they
    # throw the same book — and it painted one anyway. `False` here means the
    # blob is simply not written out, rather than overwriting `tome.png` with a
    # second, differently-lit version of the same object.
    "teacher_m": ("teacher_m_sheet.png",    4, False),
}


def _band(sheet):
    """The vertical extent of the figure row — everything lit on the sheet."""
    w, h = sheet.get_size()
    rows = [y for y in range(0, h, 2)
            if any(_lit(sheet.get_at((x, y))) for x in range(0, w, 4))]
    if not rows:
        raise SystemExit("sheet is empty")
    return rows[0], rows[-1] + 1


def _lit(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] > LUMA_CUT


# Components are labelled on a stride-2 mask: a 1536x1024 sheet is 786k pixels
# and a Python flood fill over all of them is slow enough to notice, while every
# blob here is hundreds of pixels across. Halving both axes costs nothing real.
STRIDE = 2
POSE_MIN_BAND = 0.5      # a blob this tall (as a share of the band) is a pose
BLOB_MIN_PX = 40         # in mask cells: below this it is speckle, not art


def _blobs(sheet):
    """Bounding boxes of the separate lit shapes on the sheet, left to right."""
    w, h = sheet.get_size()
    mw, mh = w // STRIDE, h // STRIDE
    mask = [[_lit(sheet.get_at((x * STRIDE, y * STRIDE)))
             for y in range(mh)] for x in range(mw)]
    boxes = []
    for sx in range(mw):
        for sy in range(mh):
            if not mask[sx][sy]:
                continue
            stack, cells = [(sx, sy)], []
            mask[sx][sy] = False
            while stack:
                cx, cy = stack.pop()
                cells.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < mw and 0 <= ny < mh and mask[nx][ny]:
                        mask[nx][ny] = False
                        stack.append((nx, ny))
            if len(cells) < BLOB_MIN_PX:
                continue
            xs = [c[0] for c in cells]
            ys = [c[1] for c in cells]
            boxes.append((min(xs) * STRIDE, min(ys) * STRIDE,
                          (max(xs) + 1) * STRIDE, (max(ys) + 1) * STRIDE))
    return sorted(boxes)


def _union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _cut(sheet, box):
    """Key one shape off the black sheet and trim it to its own content."""
    x0, y0, x1, y1 = box
    surf = pygame.Surface((x1 - x0, y1 - y0), pygame.SRCALPHA)
    surf.blit(sheet, (0, 0), (x0, y0, x1 - x0, y1 - y0))
    key_by_fill(surf, LUMA_CUT)
    rect = surf.get_bounding_rect()
    if not rect.width or not rect.height:
        raise SystemExit(f"pose at {box} keyed away to nothing")
    out = pygame.Surface(rect.size, pygame.SRCALPHA)
    out.blit(surf, (0, 0), rect)
    return out


def _scaled(surf, scale):
    return pygame.transform.smoothscale(
        surf, (max(1, round(surf.get_width() * scale)),
               max(1, round(surf.get_height() * scale))))


def extract(name, sheet_file, n_poses, has_extra):
    path = os.path.join(SRC_DIR, sheet_file)
    if not os.path.exists(path):
        raise SystemExit(f"no sheet at {path} — run tools/art_request.py first")
    sheet = pygame.image.load(path).convert_alpha()
    band_y0, band_y1 = _band(sheet)
    band_h = band_y1 - band_y0

    blobs = _blobs(sheet)
    pose_boxes = [b for b in blobs if b[3] - b[1] >= band_h * POSE_MIN_BAND]
    others = [b for b in blobs if b not in pose_boxes]

    if len(pose_boxes) != n_poses:
        raise SystemExit(
            f"{sheet_file}: found {len(pose_boxes)} full-height figures, expected "
            f"{n_poses}\n  at {pose_boxes}\n"
            f"  fewer means two poses are touching and merged into one blob; more "
            f"means a pose broke apart. Either way the sheet is the thing to "
            f"re-roll — §R8 asks for wide black gutters and one common ground "
            f"line for exactly this reason.")

    # Anything left that is not tucked inside a figure's own column is the extra
    # item and its debris — the flying book plus the torn pages trailing it.
    def inside_a_pose(b):
        return any(p[0] <= b[0] and b[2] <= p[2] for p in pose_boxes)

    extras = [b for b in others if not inside_a_pose(b)]

    poses = [_cut(sheet, b) for b in pose_boxes]
    # One scale for every pose, taken from MAIN — see the module docstring.
    scale = TARGET_H / poses[0].get_height()
    written = []

    for label, surf in zip(POSES, poses):
        img = brighten(_scaled(surf, scale), LIFT)
        out = os.path.join(SPRITES, f"{name}.png" if label == GAME_POSE
                           else f"{name}_{label}.png")
        pygame.image.save(img, out)
        written.append(out)

    menu = brighten(_scaled(poses[0], MENU_H / poses[0].get_height()), LIFT)
    out = os.path.join(SPRITES, f"{name}_menu.png")
    pygame.image.save(menu, out)
    written.append(out)

    if has_extra:
        if not extras:
            raise SystemExit(f"{sheet_file}: no projectile found beside the poses")
        tome = _cut(sheet, _union(extras))
        # The projectile is sized against the fireball it replaces, not against
        # the sheet: `settings.TOME_SIZE` is the collision box either way.
        img = brighten(_scaled(tome, 22 / tome.get_height()), LIFT)
        out = os.path.join(SPRITES, "tome.png")
        pygame.image.save(img, out)
        written.append(out)

    return written


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(SPRITES, exist_ok=True)
    for name, (sheet_file, n, extra) in SHEETS.items():
        for path in extract(name, sheet_file, n, extra):
            img = pygame.image.load(path)
            print(f"  wrote {os.path.relpath(path, ROOT)} "
                  f"({img.get_width()}x{img.get_height()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
