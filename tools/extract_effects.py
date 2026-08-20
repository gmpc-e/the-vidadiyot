"""Cut the one-off effect art: Roni's knife, Snir's web, Zina's bite splash.

These are single sprites off three unrelated hand-made sheets, none of which
follows the strip conventions in `docs/ART_PROMPTS_PHASE2.md` — they are weapon
cards and option boards, laid out for a human to choose from. So the crops are
**measured and written down** rather than found; a card's layout is not something
a row scan can reason about.

⚠️ **Fine bright detail does not survive a big downscale.** A web strand, a blood
spatter and a knife's chasing are all a pixel or two wide in a 1536px painting,
and averaging them down to 30px blends them into the black behind them. Two of
the three are repainted from their alpha (`spritelib.flatten_color`) for exactly
that reason — the shape is intact in the mask long after the colour is gone. See
the cobweb note in `tools/extract_ambience.py`; this is the third time.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_effects.py
"""
import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritelib import flatten_color, key_by_fill, slice_strip          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, "assets", "sprites")
SRC = os.path.expanduser("~/Downloads/the-vidadiyot")

KNIFE_SHEET = "champions/roni-the-warrior-princess/throwing-knive-roni.png"
KNIFE_CROP = (50, 745, 560, 210)     # the "DETAIL VIEW" panel, below its caption
# ⚠️ Sized by **width**, not height. The old knife was 34px wide and the note was
# that it looked too big; this blade is longer and thinner, so matching heights
# would have made it *wider* than what it replaced.
KNIFE_W = 26

WEB_SHEET = "monsters/little-snir/web-affects.png"
WEB_BAND = (86, 258)                 # the first row of flight webs
WEB_H = 30

SPLASH_SHEET = "champions/roni-the-warrior-princess/zina_bite_splash.png"
SPLASH_CROP = (20, 840, 900, 120)    # the "IMPACT SPLASH OPTIONS" row
SPLASH_H = 26
SPLASH_PICK = 0                      # the radial burst: symmetrical, so it needs
                                     # no rotation, and it reads at 30px where
                                     # the directional spatters do not
BLOOD = (198, 44, 40)


def _load(rel):
    path = os.path.join(SRC, rel)
    if not os.path.exists(path):
        raise SystemExit(f"no sheet at {path}")
    return pygame.image.load(path).convert_alpha()


def _knife():
    sheet = _load(KNIFE_SHEET)
    x, y, w, h = KNIFE_CROP
    cell = pygame.Surface((w, h), pygame.SRCALPHA)
    cell.blit(sheet, (0, 0), KNIFE_CROP)
    key_by_fill(cell, 34)            # the card has a dark vignette, not flat black
    rect = cell.get_bounding_rect()
    trimmed = pygame.Surface(rect.size, pygame.SRCALPHA)
    trimmed.blit(cell, (0, 0), rect)
    # ⚠️ the detail view points LEFT; everything in the game is aimed
    # screen-right and mirrored or rotated from there
    trimmed = pygame.transform.flip(trimmed, True, False)
    scale = KNIFE_W / trimmed.get_width()
    return pygame.transform.smoothscale(
        trimmed, (KNIFE_W, max(1, round(trimmed.get_height() * scale))))


def _web():
    frames = slice_strip(_load(WEB_SHEET), WEB_H, band=WEB_BAND, cells=4,
                         luma_cut=20)
    # head on the left with the trail streaming right means it is flying LEFT
    return pygame.transform.flip(frames[0], True, False)


def _splash():
    sheet = _load(SPLASH_SHEET)
    x, y, w, h = SPLASH_CROP
    row = pygame.Surface((w, h), pygame.SRCALPHA)
    row.blit(sheet, (0, 0), SPLASH_CROP)
    frames = slice_strip(row, SPLASH_H, cells=6, luma_cut=22)
    return flatten_color(frames[SPLASH_PICK], BLOOD, 0.95)


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    for name, make in (("roni_knife", _knife),
                       ("web_ball", _web),
                       ("bite_splash", _splash)):
        img = make()
        path = os.path.join(SPRITES, f"{name}.png")
        pygame.image.save(img, path)
        print(f"  wrote {os.path.relpath(path, ROOT)} "
              f"({img.get_width()}x{img.get_height()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
