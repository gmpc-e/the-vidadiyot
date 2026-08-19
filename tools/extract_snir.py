"""Extract 'Little Snir' IDLE pose from her sheet -> snir.png.

Same border flood-fill approach as extract_terror.py (dark bg + dark hair, so a
brightness threshold would fail). Crop the IDLE pose, drop connected background,
auto-trim, scale.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/extract_snir.py
"""
import os
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "/Users/elkes/Downloads/little_snir_monster_modes.png"
OUT = os.path.join(ROOT, "assets", "sprites", "snir.png")

CROP = (724, 74, 244, 436)      # IDLE pose (x, y, w, h)
BG_TOL = 40
TARGET_H = 54


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
    stack = [(px, 0) for px in range(w)] + [(px, h - 1) for px in range(w)]
    stack += [(0, py) for py in range(h)] + [(w - 1, py) for py in range(h)]
    seen = [[False] * h for _ in range(w)]
    while stack:
        px, py = stack.pop()
        if px < 0 or py < 0 or px >= w or py >= h or seen[px][py]:
            continue
        seen[px][py] = True
        if color_dist(surf.get_at((px, py)), bg) <= BG_TOL:
            surf.set_at((px, py), (0, 0, 0, 0))
            stack.extend([(px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)])

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
