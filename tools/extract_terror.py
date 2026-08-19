"""Extract the 'Little Terror' IDLE pose from the monster sheet -> terror.png.

The sheet has a dark background AND the character wears dark tatters, so a simple
brightness threshold would eat the clothing. Instead we flood-fill from the crop
borders: only background pixels *connected to the edge* become transparent, so
interior dark clothing is kept. Then auto-trim and scale.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_terror.py
"""
import os
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "/Users/elkes/Downloads/maya-tirosh-monsters.png"
OUT = os.path.join(ROOT, "assets", "sprites", "terror.png")

CROP = (497, 472, 216, 256)      # IDLE pose (x, y, w, h)
BG_TOL = 42                      # color distance to treat a border pixel as bg
TARGET_H = 54                   # final sprite height in px


def color_dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    sheet = pygame.image.load(SRC).convert_alpha()

    x, y, w, h = CROP
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.blit(sheet, (0, 0), CROP)

    bg = surf.get_at((0, 0))
    # flood fill background from all border pixels
    stack = [(px, 0) for px in range(w)] + [(px, h - 1) for px in range(w)]
    stack += [(0, py) for py in range(h)] + [(w - 1, py) for py in range(h)]
    seen = [[False] * h for _ in range(w)]
    while stack:
        px, py = stack.pop()
        if px < 0 or py < 0 or px >= w or py >= h or seen[px][py]:
            continue
        seen[px][py] = True
        c = surf.get_at((px, py))
        if color_dist(c, bg) <= BG_TOL:
            surf.set_at((px, py), (0, 0, 0, 0))
            stack.extend([(px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)])

    # auto-trim to remaining content
    rect = surf.get_bounding_rect()
    trimmed = pygame.Surface(rect.size, pygame.SRCALPHA)
    trimmed.blit(surf, (0, 0), rect)

    scale = TARGET_H / trimmed.get_height()
    out = pygame.transform.smoothscale(
        trimmed, (max(1, round(trimmed.get_width() * scale)), TARGET_H))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(out, OUT)
    print(f"wrote {OUT} ({out.get_width()}x{out.get_height()})")


if __name__ == "__main__":
    main()
