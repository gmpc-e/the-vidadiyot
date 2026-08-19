"""Extract Roni the Warrior Princess and Zina her dog from the sheet.

The sheet's ANIMATIONS panel draws Roni and Zina *together* in every frame, with
Roni on the left of each cell and Zina on the right. The game needs them apart —
Roni is the player, Zina is a summon that flies out and comes back — so each crop
takes one half of a cell.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_roni.py
"""
import os
import pygame

from spritelib import load_source, MODE_FILL, extract_pose

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "roni-the-warrior-princess.png"
OUT_DIR = os.path.join(ROOT, "assets", "sprites")
LUMA_CUT = 20                     # animation cells sit on near-black
GAMMA = 1.35
SOLID = 110                       # snap alpha after scaling — no ghosting
# The hero art: Roni *and* Zina. Stops above the UI mock-ups lower on the sheet.
# Wide enough that the dog is actually visible — cropped to portrait shape she
# was the only one in frame, which rather undercuts a character whose whole
# power is the dog. The select screen scales it down to fit its art box.
PORTRAIT = (128, 235, 500, 410)
PORTRAIT_H = 200

# Cells are small and packed, so crops must clear both the row's label text above
# and the neighbouring frame to the right; extract_pose auto-trims, so erring
# generous *inside* those bounds is free.
POSES = {                         # name -> (crop, target height)
    "roni_idle":   ((1092, 80, 62, 90), 48),
    "roni_walk":   ((1082, 200, 72, 86), 48),
    "roni_attack": ((1226, 424, 78, 90), 48),
    "roni_hurt":   ((1376, 424, 78, 90), 48),   # the recoil frame of the attack row
    "zina":        ((1300, 94, 68, 78), 34),    # the dog, sent out on Z
}


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    sheet = load_source(SRC)
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, (crop, target_h) in POSES.items():
        img = extract_pose(sheet, crop, target_h, mode=MODE_FILL,
                           luma_cut=LUMA_CUT, gamma=GAMMA, solid=SOLID)
        path = os.path.join(OUT_DIR, name + ".png")
        pygame.image.save(img, path)
        print(f"wrote {path} ({img.get_width()}x{img.get_height()})")

    portrait = extract_pose(sheet, PORTRAIT, PORTRAIT_H, mode=MODE_FILL,
                            luma_cut=LUMA_CUT, gamma=1.2, solid=SOLID)
    path = os.path.join(OUT_DIR, "roni_portrait.png")
    pygame.image.save(portrait, path)
    print(f"wrote {path} ({portrait.get_width()}x{portrait.get_height()})")


if __name__ == "__main__":
    main()
