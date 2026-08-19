"""Generate the player knight sprite as pixel art -> assets/sprites/knight.png.

Front-facing little knight: plumed helmet, steel armor, a shield on the left arm
and a sword on the right. Drawn a touch larger than the 24x32 hitbox; the player
blits it centered/feet-aligned over the hitbox.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/gen_player_sprite.py
"""
import os
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "sprites", "knight.png")
W, H = 28, 36

STEEL   = (158, 168, 188)
STEEL_D = (96, 106, 128)
STEEL_L = (205, 214, 230)
ARMOR   = (120, 140, 190)
ARMOR_D = (80, 96, 140)
SHIELD  = (70, 110, 200)
SHIELD_L = (120, 160, 235)
CROSS   = (232, 236, 246)
PLUME   = (208, 60, 72)
GOLD    = (224, 190, 96)
BLADE   = (212, 218, 230)
BLADE_D = (150, 158, 175)
BOOT    = (52, 52, 66)
DARK    = (26, 28, 38)


def rect(s, color, x, y, w, h):
    pygame.draw.rect(s, color, (x, y, w, h))


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    s = pygame.Surface((W, H), pygame.SRCALPHA)

    # ── sword (behind, right side) ──────────────────────────────────────---
    rect(s, BLADE, 23, 7, 3, 18)          # blade
    rect(s, BLADE_D, 25, 7, 1, 18)        # blade shade
    rect(s, STEEL_L, 23, 6, 3, 1)         # tip glint
    rect(s, GOLD, 21, 22, 7, 2)           # crossguard
    rect(s, GOLD, 23, 24, 3, 4)           # grip
    rect(s, GOLD, 22, 28, 5, 2)           # pommel

    # ── plume (behind helmet top) ───────────────────────────────────────---
    rect(s, PLUME, 12, 1, 5, 6)
    rect(s, (170, 44, 56), 12, 1, 2, 6)

    # ── legs + boots ────────────────────────────────────────────────────---
    rect(s, STEEL_D, 9, 27, 4, 6)         # left greave
    rect(s, STEEL_D, 15, 27, 4, 6)        # right greave
    rect(s, BOOT, 8, 33, 5, 3)
    rect(s, BOOT, 15, 33, 5, 3)

    # ── torso armor ─────────────────────────────────────────────────────---
    rect(s, ARMOR, 8, 15, 12, 13)
    rect(s, ARMOR_D, 8, 15, 12, 2)        # collar shade
    rect(s, STEEL_L, 13, 17, 2, 9)        # central ridge highlight
    rect(s, GOLD, 8, 24, 12, 2)           # belt
    # pauldrons
    rect(s, STEEL, 6, 14, 5, 4)
    rect(s, STEEL, 17, 14, 5, 4)
    rect(s, STEEL_D, 6, 17, 5, 1)
    rect(s, STEEL_D, 17, 17, 5, 1)

    # ── helmet ──────────────────────────────────────────────────────────---
    rect(s, STEEL, 9, 4, 10, 11)
    rect(s, STEEL_L, 9, 4, 10, 2)         # top highlight
    rect(s, STEEL_D, 9, 13, 10, 2)        # jaw shade
    rect(s, DARK, 10, 9, 8, 2)            # visor slit
    rect(s, STEEL_D, 13, 6, 2, 3)         # nose guard

    # ── shield (front, left arm) ────────────────────────────────────────---
    rect(s, SHIELD, 3, 16, 8, 11)
    rect(s, SHIELD, 4, 27, 6, 2)          # rounded bottom
    rect(s, SHIELD_L, 3, 16, 8, 2)        # top rim light
    rect(s, CROSS, 6, 18, 2, 8)           # cross vertical
    rect(s, CROSS, 4, 20, 6, 2)           # cross horizontal
    pygame.draw.rect(s, DARK, (3, 16, 8, 12), 1)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(s, OUT)
    print(f"wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
