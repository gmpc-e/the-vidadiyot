"""Cut the Phase 2 animation strips into game-ready frames.

Source: `~/Downloads/the-vidadiyot/phase2/*.png`, one strip per file, delivered
by `tools/art_request.py` against `docs/ART_PROMPTS_PHASE2.md`. Each sheet is a
single horizontal row of three frames on black.

**Why three frames and not four.** §A of the pack explains it in full; the short
version is that the model reliably draws three well-separated, well-registered
figures and unreliably draws four. A walk plays them **ping-pong** (0-1-2-1) for
a four-beat cycle out of three drawings, which `Entity.PINGPONG` handles.

**Frames come back on a shared canvas.** `spritelib.slice_strip` scales the whole
strip by one factor and bottom-aligns every frame, so the game blits them all at
one position and the character stays put. Fitting each frame to its own height is
the obvious implementation and it makes the sprite pulse — see the note there.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_phase2.py [--sheet]
"""
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritelib import brighten, slice_strip, strip_rows                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, "assets", "sprites")
SRC_DIR = os.path.expanduser("~/Downloads/the-vidadiyot")

FRAMES = 3

# delivered file -> list of (output prefix, row index, target height, gamma)
#
# `row` picks one band out of a sheet laid out as a **grid**. Hand-made sheets
# arrive that way — one request, one consistent character, several animations —
# which is a better way to commission art than one strip per file, and costs
# only a row scan in `spritelib.strip_rows`.
#
# The height matches the character's **existing** idle pose, because these get
# intercut with it: a walk cycle two pixels taller than the idle makes the
# character jolt the moment it starts moving. `knight_idle.png` is 48 tall.
#
# ⚠️ Rows are indexed from the top and a sheet's *unused* rows are simply not
# listed. `elad-knight-sheet-v2` has a third row of lightning-sword poses that
# is deliberately skipped: Elad's `power` is None, so it is art for a mechanic
# the game does not have — and the beam bridges all three frames into one blob,
# so it could not be cut apart even if it were wanted.
# (prefix, row, target_h, gamma) or (prefix, row, target_h, gamma, (col_lo, col_hi))
# — a hand-made row often carries more than one animation, so a column slice
# picks the three cells that belong together.
STRIPS = {
    "champions/elad-the-knight/elad-knight-sheet-v2.png": [
        ("knight_attack", 1, 48, 1.0),
    ],
    # Elad's flinch. Row 3 is struck / braced / recovered — the first cell has
    # the impact, the other two are the recovery, which is a legitimate hurt
    # cycle even though only the first cell is obviously "hurt".
    "champions/elad-the-knight/elad-hurt-bottom-left.png": [
        ("knight_hurt", 2, 48, 1.0),
    ],
    # Roni's directional walks. ⚠️ Row 4 is row 2 facing the other way and is
    # deliberately skipped — `player.draw` mirrors the side view for leftward
    # movement, so a painted left-facing row would only ever disagree with it.
    "champions/roni-the-warrior-princess/roni-directional.png": [
        ("roni_walk_down", 0, 48, 1.0),
        ("roni_walk_side", 1, 48, 1.0),
        ("roni_walk_up",   2, 48, 1.0),
    ],
    # ⚠️ The directional walks come off **v3**, which was set aside as "better
    # sheet, worse fit" — a verdict made before directional facing came up. It
    # carries front, back and side walks, and a back view is the one thing that
    # cannot be derived from a front view by mirroring.
    #
    # The rows are drawn at different sizes on the sheet (side figures ~234px,
    # front ~193px, back ~176px). Normalising each to the same 48px output is
    # what keeps Elad the same height whichever way he walks — the sheet's own
    # inconsistency does not survive into the game.
    # Roni: walk / throw / hurt, three clean rows at 2, 2 and 9px baseline
    # spread. ⚠️ Row 3's middle frame is 30px shorter than its neighbours and
    # that is correct — it is the doubled-over stagger. Height is advisory for
    # exactly this reason; the baseline is what has to hold.
    # ⚠️ The trapped-warrior sheets need **even division**, not gutter detection:
    # their web strands trail *between* frames, so the figures are joined and a
    # gutter scan reads a whole row as one item. `cells` splits the lit span into
    # N — exact enough when the frames are evenly spaced, and a clipped strand
    # costs nothing where a merged row costs the sheet.
    #
    # ⚠️ ...and they arrive **much darker than the idle they cut against** (mean
    # luma 31 and 52, against 74 and 88), which breaks the "actors stay bright"
    # rule the moment the player is caught. The gammas below were measured
    # against each warrior's own idle, not guessed.
    "champions/elad-the-knight/elad-web-captured.png": [
        ("knight_webbed", 1, 48, 1.55, None, 4),
    ],
    "champions/roni-the-warrior-princess/roni-trapped-web.png": [
        ("roni_webbed", 1, 48, 1.45, None, 5),
    ],
    "champions/roni-the-warrior-princess/roni-sheet-v2.png": [
        ("roni_walk", 0, 48, 1.0),
        ("roni_attack", 1, 48, 1.0),
        ("roni_hurt", 2, 48, 1.0),
    ],
    "champions/elad-the-knight/elad-knight-sheet-v3.png": [
        ("knight_walk_side", 0, 48, 1.0, (0, 3)),
        ("knight_walk_up",   2, 48, 1.0, (1, 4)),
        ("knight_walk_down", 3, 48, 1.0, (0, 3)),
    ],
}


def extract(sheet, prefix, row, target_h, gamma, cols=None, cells=None):
    bands = strip_rows(sheet)
    if row >= len(bands):
        raise SystemExit(f"{prefix}: asked for row {row}, the sheet has "
                         f"{len(bands)} ({bands})")
    frames = slice_strip(sheet, target_h, expect=cells or FRAMES,
                         band=bands[row], cols=cols, cells=cells)
    written = []
    for i, f in enumerate(frames):
        if gamma != 1.0:
            f = brighten(f, gamma)
        out = os.path.join(SPRITES, f"{prefix}_{i}.png")
        pygame.image.save(f, out)
        written.append(out)
    return written


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(SPRITES, exist_ok=True)
    for src, rows in STRIPS.items():
        full = os.path.join(SRC_DIR, src)
        if not os.path.exists(full):
            raise SystemExit(f"no sheet at {full}")
        sheet = pygame.image.load(full).convert_alpha()
        for prefix, row, h, gamma, *rest in rows:
            for path in extract(sheet, prefix, row, h, gamma,
                                cols=rest[0] if rest else None,
                                cells=rest[1] if len(rest) > 1 else None):
                img = pygame.image.load(path)
                print(f"  wrote {os.path.relpath(path, ROOT)} "
                      f"({img.get_width()}x{img.get_height()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
