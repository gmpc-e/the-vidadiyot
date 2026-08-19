"""Extract Elad the Knight's animation poses from his sheet.

The sheet holds MAIN / IDLE / WALK / three ATTACKs / HURT / VICTORY. The player
only needs four states, and the attack crops deliberately stop short of the
goblin and blood splatter beside the knight — the game draws its own slash arc
(`Player._draw_swing`), so the painted arc is not wanted here.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_knight.py
"""
import os
import pygame

from spritelib import load_source, MODE_FILL, extract_pose

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "elad-the-knight.png"
OUT_DIR = os.path.join(ROOT, "assets", "sprites")
TARGET_H = 48                     # a touch shorter than the 54px monsters
# A high cut chews straight through his dark armor: the fill follows the shadows
# inward, downscaling smears the holes, and he renders as a ghost (only ~9% of
# his pixels stayed opaque). Low cut + solidify keeps him a solid figure.
LUMA_CUT = 16
SOLID    = 110                    # snap alpha on/off after scaling
GAMMA    = 1.7                    # dark armor at 48px needs the shadows lifted

# Crops start *below* each pose's painted label ribbon: the ribbon is bright, so
# the background fill keeps it, and it is wide enough to beat the figure for
# "largest blob" — which silently yields a 387px-wide banner instead of a knight.
PORTRAIT = (48, 70, 392, 580)     # the big MAIN pose, for the warrior-select page
PORTRAIT_H = 200

POSES = {                         # name -> (x, y, w, h) on the sheet
    "knight_idle":   (615, 62, 215, 300),
    "knight_walk":   (1075, 62, 275, 300),
    "knight_attack": (575, 404, 165, 188),   # SLASH, stopping at his feet so
                                             # the painted arc stays out (the
                                             # game draws its own slash)
    "knight_hurt":   (900, 714, 220, 256),
}


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    sheet = load_source(SRC)
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, crop in POSES.items():
        img = extract_pose(sheet, crop, TARGET_H, mode=MODE_FILL,
                           luma_cut=LUMA_CUT, gamma=GAMMA, solid=SOLID)
        path = os.path.join(OUT_DIR, name + ".png")
        pygame.image.save(img, path)
        print(f"wrote {path} ({img.get_width()}x{img.get_height()})")

    # The select screen used to upscale the 48px game sprite, which looked like
    # mush. Give it its own crop off the full-size art instead.
    portrait = extract_pose(sheet, PORTRAIT, PORTRAIT_H, mode=MODE_FILL,
                            luma_cut=LUMA_CUT, gamma=1.35, solid=SOLID)
    path = os.path.join(OUT_DIR, "knight_portrait.png")
    pygame.image.save(portrait, path)
    print(f"wrote {path} ({portrait.get_width()}x{portrait.get_height()})")


if __name__ == "__main__":
    main()
