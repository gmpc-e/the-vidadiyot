"""Roni's Royal Blade — the in-flight throwing knife.

Taken from the sheet's THROW ANIMATION panel rather than the hero render: that
frame is already drawn side-on with motion streaks, which is exactly how it
reads flying across a room. It points right; the game flips it to face left.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_knife.py
"""
import os
import pygame

from spritelib import load_source, MODE_FILL, extract_pose

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "throwing-knive-roni.png"
OUT = os.path.join(ROOT, "assets", "sprites", "roni_knife.png")
CROP = (848, 792, 268, 86)        # the blade itself, clear of the motion streaks
TARGET_H = 11                     # it is a knife, not a sword
LUMA_CUT = 30
SOLID = 100


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    sheet = load_source(SRC)
    img = extract_pose(sheet, CROP, TARGET_H, mode=MODE_FILL,
                       luma_cut=LUMA_CUT, gamma=1.3, solid=SOLID)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(img, OUT)
    print(f"wrote {OUT} ({img.get_width()}x{img.get_height()})")


if __name__ == "__main__":
    main()
