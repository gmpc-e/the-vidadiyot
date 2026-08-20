"""Cut Little Snir's character sheets — walk, web wind-up, hurt, front and side.

Source: `~/Downloads/the-vidadiyot/monsters/little-snir/little_snir_sheet_v{2,3}.png`.

⚠️ **Both sheets are needed and neither is a superset.** v2 is entirely
front-facing and v3 entirely side-facing (profile, facing *left*), each with the
same three rows. Little Terror's v3 happened to contain her v2; Snir's do not, so
picking "the newer one" would have thrown away her front views.

⚠️ **v3 faces left and the game's convention is right.** Every directional sprite
is painted facing screen-right and mirrored for leftward movement — a left-facing
row would disagree with the mirror on every frame, so it is flipped on the way in.

Neither sheet carries a back-facing walk, so she turns toward the camera and
sideways but never away. Same gap Little Terror had.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_snir_sheet.py
"""
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritelib import slice_strip                                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, "assets", "sprites")
SRC = os.path.expanduser("~/Downloads/the-vidadiyot/monsters/little-snir")

TALL = 54                # the height every monster is cut to

# sheet -> [(output prefix, band, flip?)]. Bands are the rows `strip_rows`
# finds; they are written down so a re-export a few pixels off is a loud
# failure rather than a silently different crop.
SHEETS = {
    "little_snir_sheet_v2.png": [        # front-facing
        ("snir_walk", (60, 354), False),
        ("snir_cast", (406, 699), False),
        ("snir_hurt", (745, 1038), False),
    ],
    "little_snir_sheet_v3.png": [        # side-facing, drawn facing left
        ("snir_walk_side", (37, 274), True),
        ("snir_cast_side", (314, 551), True),
        ("snir_hurt_side", (566, 811), True),
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
            frames = slice_strip(sheet, TALL, expect=3, band=band, luma_cut=22)
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
