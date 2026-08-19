"""Short-lived visual effects: sparkle bursts and a rising book (roadmap §6).

World-space, purely cosmetic, and owned by PlayState — nothing here touches the
simulation. Everything is drawn with primitives (no art assets), so effects can
take a room's color and read as "that room accepted its book".
"""
import math
import random

import pygame

from game.ui.icons import draw_book

SPARKLE_COUNT   = 26
SPARKLE_LIFE    = (0.30, 0.55)   # seconds, randomized per particle
SPARKLE_SPEED   = (40, 115)      # px/sec, outward
SPARKLE_FADE    = 0.45           # fraction of life spent fading (rest is full bright)
SPARKLE_GRAVITY = 130            # px/sec^2, so the burst arcs and settles
BOOK_RISE       = 30             # px the returned book floats up
BOOK_LIFT       = 18             # px above the return point it starts, clear of the knight
BOOK_LIFE       = 0.7            # seconds it stays visible


class _Sparkle:
    """One outward-flung, gravity-pulled dot that fades as it dies."""

    def __init__(self, pos, color):
        ang = random.uniform(0, math.tau)
        speed = random.uniform(*SPARKLE_SPEED)
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(math.cos(ang), math.sin(ang)) * speed
        self.life = self.max_life = random.uniform(*SPARKLE_LIFE)
        self.size = random.choice((2, 2, 3, 3, 4))   # 1px reads as noise at 640x360
        # half the burst is the room's color, half is a warm white — the mix
        # keeps it legible against every room tint.
        self.color = color if random.random() < 0.5 else (255, 244, 210)

    @property
    def dead(self):
        return self.life <= 0

    def update(self, dt):
        self.life -= dt
        self.vel.y += SPARKLE_GRAVITY * dt
        self.pos += self.vel * dt

    def draw(self, surface, camera):
        t = max(0.0, self.life / self.max_life)
        p = camera.world_to_screen(self.pos)
        # Fade by darkening toward the scene rather than per-pixel alpha: one
        # rect blit per particle, no temp surfaces. Hold full brightness for
        # most of the life and dim only at the end — a linear fade spends its
        # whole span looking like dark specks of dirt on a dim floor.
        bright = min(1.0, t / SPARKLE_FADE)
        col = tuple(int(c * bright) for c in self.color)
        size = max(1, int(self.size * (0.6 + 0.4 * t)))
        surface.fill(col, (int(p.x), int(p.y), size, size))


class _RisingBook:
    """The returned book, drawn floating up and fading out at the return spot."""

    def __init__(self, pos, color):
        self.pos = pygame.Vector2(pos)
        self.color = color
        self.life = BOOK_LIFE

    @property
    def dead(self):
        return self.life <= 0

    def update(self, dt):
        self.life -= dt

    def draw(self, surface, camera):
        t = max(0.0, self.life / BOOK_LIFE)
        rise = BOOK_LIFT + BOOK_RISE * (1.0 - t)
        p = camera.world_to_screen(self.pos) - pygame.Vector2(0, rise)
        rect = pygame.Rect(0, 0, 13, 11)
        rect.center = (int(p.x), int(p.y))
        # draw into a scratch surface so the whole icon can fade as one
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_book(layer, layer.get_rect(), self.color)
        layer.set_alpha(int(255 * min(1.0, t * 2.5)))   # hold, then fade out
        surface.blit(layer, rect.topleft)


class Effects:
    """A flat pool of live effects. Update once, draw once, forget."""

    def __init__(self):
        self.items = []

    def book_returned(self, pos, color):
        """The §6 payoff burst: sparkles + the book floating to its shelf."""
        self.items.extend(_Sparkle(pos, color) for _ in range(SPARKLE_COUNT))
        self.items.append(_RisingBook(pos, color))

    def update(self, dt):
        for e in self.items:
            e.update(dt)
        self.items = [e for e in self.items if not e.dead]

    def draw(self, surface, camera):
        for e in self.items:
            e.draw(surface, camera)
