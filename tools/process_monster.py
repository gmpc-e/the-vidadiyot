"""Turn the raw monster photo into a game sprite: scale down + drop white bg.

The source is a 1254x1254 creature on a near-white background. We scale it to a
small sprite and make near-white pixels transparent so it sits cleanly on the
dark school floor. Run once:

    SDL_VIDEODRIVER=dummy ./venv/bin/python tools/process_monster.py
"""
import os
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "/Users/elkes/downloads/snhir-haktantana.jpeg"
OUT = os.path.join(ROOT, "assets", "sprites", "monster.png")
TARGET = 48                      # sprite is 48x48 px
WHITE_CUTOFF = 224               # pixels brighter than this become transparent


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))          # convert_alpha needs a display
    img = pygame.image.load(SRC).convert_alpha()
    img = pygame.transform.smoothscale(img, (TARGET, TARGET))

    out = pygame.Surface((TARGET, TARGET), pygame.SRCALPHA)
    for y in range(TARGET):
        for x in range(TARGET):
            r, g, b, a = img.get_at((x, y))
            if r >= WHITE_CUTOFF and g >= WHITE_CUTOFF and b >= WHITE_CUTOFF:
                out.set_at((x, y), (0, 0, 0, 0))          # transparent bg
            else:
                out.set_at((x, y), (r, g, b, 255))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(out, OUT)
    print(f"wrote {OUT} ({TARGET}x{TARGET})")


if __name__ == "__main__":
    main()
