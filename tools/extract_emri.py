"""Extract Emri 'the disappearing monster' IDLE pose -> emri.png.

Emri has no legs on the sheet — the body trails off into smoke, which is exactly
right for a monster that blinks in and out, so the crop keeps that tail.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_emri.py
"""
import os
import pygame

from spritelib import load_source, MODE_RAMP, extract_pose

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "emre-monster.png"
OUT = os.path.join(ROOT, "assets", "sprites", "emri.png")
CROP = (690, 95, 225, 320)        # IDLE pose
TARGET_H = 58                     # slightly taller than the other two: it's a boss
LUMA_CUT = 52                     # he is shadow: a fill would leave a floating head
FEATHER = 20                      # dissolve the crop edge so the kept haze isn't a box
GAMMA   = 1.35                    # a gentler lift than the knight: he should stay murky


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    sheet = load_source(SRC)
    img = extract_pose(sheet, CROP, TARGET_H, mode=MODE_RAMP,
                       luma_cut=LUMA_CUT, feather=FEATHER, gamma=GAMMA)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(img, OUT)
    print(f"wrote {OUT} ({img.get_width()}x{img.get_height()})")


if __name__ == "__main__":
    main()
