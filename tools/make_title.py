"""Turn the painted title artwork into menu-ready assets.

The source is a 1774x887 painting on black: the words "The Vidadiyot" over a
spiked mace-and-skull bar. Two things have to happen before it can sit on the
640x360 menu:

  * **Crop.** The painting carries a wide dead-black margin, and the lettering
    and the mace bar want different sizes on screen — the words are the hero,
    the bar is a thin divider. So they come out as two assets.
  * **Key out the black.** Blitting the raw art would stamp a hard black
    rectangle over the menu's grid. Instead alpha ramps with luminance, so the
    dark vignette dissolves into the background and only the paint survives.

Run once (regenerate if the artwork changes):

    SDL_VIDEODRIVER=dummy ./venv/bin/python tools/make_title.py
"""
import os

import pygame

from spritelib import load_source

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "The-Vidadiyot.png"
OUT_DIR = os.path.join(ROOT, "assets", "ui")

# Source crops, measured from the artwork's content profile (the painting sits
# inside a black margin: content spans x 118..1660, y 78..794).
# Kept loose on every side: the V's spike, the t's crossbar and the flourish on
# the T all overshoot the ink's bounding box, and clipping any of them shows.
LETTERS = (86, 40, 1600, 640)       # x, y, w, h — "The Vidadiyot" plus its drips
RULE    = (150, 648, 1470, 152)     # the spiked mace bar with the skull boss

# Target sizes on the 640x360 internal surface.
LETTERS_W = 460
RULE_W    = 310

# Alpha ramp: pixels darker than this fade out, so the art has no black box.
DARK_CUT  = 46
DARK_GAMMA = 0.85


def _keyed(surf):
    """Copy `surf` with near-black turned progressively transparent."""
    w, h = surf.get_size()
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            r, g, b = surf.get_at((x, y))[:3]
            luma = 0.299 * r + 0.587 * g + 0.114 * b
            a = 255 if luma >= DARK_CUT else int(255 * (luma / DARK_CUT) ** DARK_GAMMA)
            out.set_at((x, y), (r, g, b, a))
    return out


def _emit(name, crop, target_w):
    x, y, w, h = crop
    piece = pygame.Surface((w, h)).convert()
    piece.blit(load_source(SRC).convert(), (0, 0), crop)
    target_h = round(h * target_w / w)
    scaled = pygame.transform.smoothscale(piece, (target_w, target_h))
    out = _keyed(scaled)
    path = os.path.join(OUT_DIR, name)
    pygame.image.save(out, path)
    print(f"wrote {path} ({target_w}x{target_h})")


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))          # convert()/convert_alpha() need one
    os.makedirs(OUT_DIR, exist_ok=True)
    _emit("title.png", LETTERS, LETTERS_W)
    _emit("title_rule.png", RULE, RULE_W)


if __name__ == "__main__":
    main()
