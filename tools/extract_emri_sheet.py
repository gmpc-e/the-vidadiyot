"""Cut Emri's character sheets — walks, cast and hurt.

Sources, both under `~/Downloads/the-vidadiyot/monsters/emre/`:

- `emri-movement-and-frames-v2.png` — front walk, side walk, **back walk**, cast
- `emri-movement-and-frames-hurt-v3.png` — a better side run, and the **hurt**

⚠️ **Both are needed.** v3 is not a superset: it has the hurt row and a stronger
side run, v2 has the front and back walks. Same trap Little Snir's pair set.

⚠️ **Bands are written down, not found.** v2's side and back rows are separated
by **5px** — a flaring mane below and hair above eat the gap — so a row scan
merges them into one 431px band holding six figures. This is the third sheet to
do that; the numbers below were measured once.

Emri is the boss and is cut **taller than the other monsters** (`TALL`), matching
`settings.EMRI_SIZE`.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_emri_sheet.py
"""
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritelib import slice_strip                                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, "assets", "sprites")
SRC = os.path.expanduser("~/Downloads/the-vidadiyot/monsters/emre")

TALL = 74                # taller than the 54px monsters — it is the boss

SHEETS = {
    "emri-movement-and-frames-v2.png": [
        ("emri_walk",      (20, 270), False),    # toward the camera
        ("emri_walk_up",   (497, 712), False),   # away — the row nothing else has
        ("emri_cast",      (717, 937), False),   # orb, wrapped, thrown
    ],
    "emri-movement-and-frames-hurt-v3.png": [
        ("emri_walk_side", (52, 345), False),    # a better run than v2's
        ("emri_hurt",      (424, 725), False),   # struck, doubled over, up again
    ],
}


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(SPRITES, exist_ok=True)
    for name, rows in SHEETS.items():
        path = os.path.join(SRC, name)
        if not os.path.exists(path):
            raise SystemExit(f"no sheet at {path}")
        sheet = pygame.image.load(path).convert_alpha()
        for prefix, band, flip in rows:
            frames = slice_strip(sheet, TALL, expect=3, band=band, luma_cut=20)
            for i, f in enumerate(frames):
                if flip:
                    f = pygame.transform.flip(f, True, False)
                out = os.path.join(SPRITES, f"{prefix}_{i}.png")
                pygame.image.save(f, out)
                print(f"  wrote {os.path.relpath(out, ROOT)} "
                      f"({f.get_width()}x{f.get_height()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
