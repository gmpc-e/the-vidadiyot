"""Ambience: the small moving things that make a room feel inhabited (§P4).

A failing fluorescent tube, a dripping pipe, cobwebs in the corners. All of it is
**non-solid decoration** and none of it touches the simulation.

Two reasons this is not part of `world/decor.py`:

- **It moves.** `decor` bakes a room's furniture into one Surface at load and
  blits it whole, which is what keeps furnishing free per frame. A flickering
  lamp cannot be baked, so it needs a live list.
- **It goes everywhere.** `decor` furnishes *classrooms*; the corridor and the
  entrance have never had anything in them at all, and a bare corridor is what
  the roadmap calls the thing holding the look back. Ambience is placed from a
  room rect and does not care what kind of room it is.

⚠️ **Everything hangs against the top wall.** These are ceiling and high-wall
fittings, and the draw order puts them *under* the actors — so anywhere a player
can stand, a lamp would be walked over. Against the top wall of a room there is
no walkable floor to be wrong about.
"""
import random

import pygame

from game.core.assets import load

# (frame, seconds) — a flicker is not a smooth cycle. A fluorescent tube on its
# way out sits lit for a while, stutters briefly, and now and then flares much
# too bright. Cycling 0-1-2-3 evenly instead reads as a disco light.
LAMP_PATTERN = ((0, 2.4), (1, 0.06), (0, 0.55), (2, 0.05), (1, 0.09),
                (0, 3.1), (3, 0.09), (0, 1.8), (2, 0.04), (0, 2.2))
# The drop forms slowly and falls fast, so the pause carries the timing.
DRIP_PATTERN = ((0, 1.7), (1, 0.20), (2, 0.14), (3, 0.34))

LAMP_EVERY = 150          # px of room width between ceiling lamps
WALL_INSET = 3            # px below the top edge that the fittings hang at
DRIP_CHANCE = 0.5         # per room


class _Animated:
    """One placed prop: a frame list, a pattern, and a phase of its own.

    ⚠️ The phase offset is the point. Without it every lamp in the level
    stutters on the same frame and the effect reads as the *screen* glitching
    rather than as several tired light fittings.
    """

    def __init__(self, frames, pattern, pos, phase):
        self.frames = frames
        self.pattern = pattern
        self.pos = pos
        self.period = sum(d for _, d in pattern)
        self.t = phase % self.period

    def update(self, dt):
        self.t = (self.t + dt) % self.period

    @property
    def image(self):
        run = 0.0
        for index, duration in self.pattern:
            run += duration
            if self.t < run:
                return self.frames[min(index, len(self.frames) - 1)]
        return self.frames[0]

    def draw(self, surface, camera):
        img = self.image
        surface.blit(img, (self.pos[0] - round(camera.offset.x),
                           self.pos[1] - round(camera.offset.y)))


class _Static(_Animated):
    """A cobweb. Same placement, no animation — one frame, forever."""

    def __init__(self, frame, pos):
        super().__init__([frame], ((0, 1.0),), pos, 0.0)


def _frames(prefix, count):
    got = [load(f"props/{prefix}_{i}.png") for i in range(count)]
    return [f for f in got if f is not None]


def build(regions, seed=0):
    """Place ambience across every room rect. Returns a list of props.

    Missing art yields an empty list rather than an error: `assets/props/` is
    regenerated from source outside the repo, so a fresh checkout has to render.
    """
    rng = random.Random(seed)
    lamps = _frames("lamp", 4)
    drips = _frames("drip", 4)
    webs = _frames("cobweb", 5)
    out = []
    for rect in regions:
        if lamps:
            span = max(1, rect.width // LAMP_EVERY)
            step = rect.width / (span + 1)
            for i in range(span):
                x = rect.x + step * (i + 1) - lamps[0].get_width() / 2
                out.append(_Animated(lamps, LAMP_PATTERN,
                                     (int(x), rect.y + WALL_INSET),
                                     rng.uniform(0, 12)))
        if webs and rect.width > 120:
            web = rng.choice(webs)
            out.append(_Static(web, (rect.x + 2, rect.y + WALL_INSET)))
            other = rng.choice(webs)
            out.append(_Static(pygame.transform.flip(other, True, False),
                               (rect.right - other.get_width() - 2,
                                rect.y + WALL_INSET)))
        if drips and rect.width > 200 and rng.random() < DRIP_CHANCE:
            x = rng.randint(rect.x + 60, max(rect.x + 61, rect.right - 100))
            out.append(_Animated(drips, DRIP_PATTERN, (x, rect.y + WALL_INSET),
                                 rng.uniform(0, 3)))
    return out
