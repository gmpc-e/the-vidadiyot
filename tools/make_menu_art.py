"""Bigger character crops for the title screen.

The menu used to scale the 48-58px *game* sprites up to 72px, which is an
upscale of already-downscaled art — the result reads as mush. These come off the
original sheets at menu size instead, so the menu downscales from high
resolution rather than upscaling from low.

The warriors get menu crops too, rather than reusing their select-screen
portraits: those are painted *scenes* keyed off black, which is invisible on the
select page but shows as a grey box against the menu's grid. The animation cells
sit on flat black and cut out cleanly.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/make_menu_art.py
"""
import os
import pygame

from spritelib import load_source, MODE_FILL, MODE_RAMP, extract_pose

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "sprites")
MENU_H = 104

# name -> (source, crop, mode, luma cut, brightness gamma, feather)
FIGURES = {
    "elad_menu":   ("elad-the-knight.png", (615, 62, 215, 300),
                    MODE_FILL, 16, 1.7, 0),
    "roni_menu":   ("roni-the-warrior-princess.png", (1092, 80, 62, 90),
                    MODE_FILL, 20, 1.35, 0),
    "snir_menu":   ("little_snir_monster_modes.png", (700, 60, 290, 470),
                    MODE_FILL, 26, 1.15, 0),
    "terror_menu": ("maya-tirosh-monsters.png", (486, 466, 238, 268),
                    MODE_FILL, 40, 1.15, 0),
    # Emri is drawn as shadow and smoke; a fill would leave a floating head
    "emri_menu":   ("emre-monster.png", (690, 95, 225, 320),
                    MODE_RAMP, 52, 1.35, 18),
}


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, (src, crop, mode, cut, gamma, feather) in FIGURES.items():
        sheet = load_source(src)
        img = extract_pose(sheet, crop, MENU_H, mode=mode, luma_cut=cut,
                           gamma=gamma, feather=feather,
                           solid=100 if mode == MODE_FILL else None)
        path = os.path.join(OUT_DIR, name + ".png")
        pygame.image.save(img, path)
        print(f"wrote {path} ({img.get_width()}x{img.get_height()})")


if __name__ == "__main__":
    main()
