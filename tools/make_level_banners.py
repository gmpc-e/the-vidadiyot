"""Crop the two level-complete banners out of their painted sheets.

The level-complete sequence shows "LEVEL ONE" and then, a beat later,
"COMPLETED"; the victory screen gets its own painted banner. All of them key the
same way the title art does: alpha ramps with
luminance, which dissolves the vignette instead of stamping a black rectangle
over the frozen game behind them.

`level-one.png` is a whole mock-up screen, so only its slime lettering is taken —
the Vidadiyot logo and the scene below it are not wanted here.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/make_level_banners.py
"""
import os
import pygame

from spritelib import load_source, MODE_RAMP, extract_pose

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "ui")

BANNERS = {
    # name -> (source file, crop, target height, luma cut, alpha curve, gamma)
    # "LEVEL ONE" sits on a painted dungeon scene rather than on black, so it
    # needs a high cut and a steep curve to lift the lettering off its
    # background; "COMPLETED" is already on black and needs far less.
    "level_one": ("level-one.png", (118, 318, 1160, 300), 104, 104, 1.9, 1.0),
    "level_completed": ("completed-level.png", (60, 90, 1420, 820), 150, 62, 1.5, 1.0),
    # Its own painted plate on black, rather than a crop out of the full victory
    # mock-up — that screen's rewards panel and Replay/Next/Menu buttons describe
    # features the game does not have yet; see the roadmap.
    "victory_banner": ("victory.png", (70, 60, 1400, 830), 150, 50, 1.4, 1.0),
}
FEATHER = 8


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, (src, crop, height, cut, curve, gamma) in BANNERS.items():
        sheet = load_source(src)
        img = extract_pose(sheet, crop, height, mode=MODE_RAMP, luma_cut=cut,
                           feather=FEATHER, alpha_gamma=curve, gamma=gamma)
        path = os.path.join(OUT_DIR, name + ".png")
        pygame.image.save(img, path)
        print(f"wrote {path} ({img.get_width()}x{img.get_height()})")


if __name__ == "__main__":
    main()
