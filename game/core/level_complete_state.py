"""LevelCompleteState — the two-beat "LEVEL ONE" / "COMPLETED" celebration.

Shown the moment the last book is home, between the level and the boss duel.
The beat structure is the whole point: the level name lands first, holds for a
second so it registers, and only then does COMPLETED slam in with the sting.
Both banners arrive with a short overshoot-and-settle so they punch rather than
fade in.

It draws over the frozen game rather than replacing it, so you can still see the
classroom you just finished.
"""
import math

import pygame

import settings
from game.core.state import State

W, H = settings.INTERNAL_RES

NAME_AT = 0.15          # seconds before "LEVEL ONE" drops in
DONE_AT = 1.15          # ...and a beat later, "COMPLETED"
POP_TIME = 0.32         # how long a banner takes to overshoot and settle
CAN_SKIP_AT = 1.9       # ignore the key that finished the level, then accept


class LevelCompleteState(State):
    draw_below = True

    def __init__(self, game, elapsed, charges=None):
        super().__init__(game)
        self.elapsed = elapsed
        # ⚠️ Carried through to the duel, not reset. Zina is *three bites a
        # level*, and the duel is the end of the same level — refilling her here
        # would mean the cheapest way to enter the boss fight at full strength
        # was to not use her at all in the school.
        self.charges = charges

    def enter(self):
        self.t = 0.0
        self.done_played = False
        self.name_img = self.game.assets.image("ui/level_one.png")
        self.done_img = self.game.assets.image("ui/level_completed.png")
        self.font = self.game.assets.font(None, 15)

    # ── flow ─────────────────────────────────────────────────────────────--
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.t >= CAN_SKIP_AT:
            self._advance()

    def update(self, dt, inp):
        self.t += dt
        if not self.done_played and self.t >= DONE_AT:
            self.done_played = True
            self.game.audio.play("level_done")
        if self.t >= CAN_SKIP_AT and (inp.interact or inp.attack or inp.confirm):
            self._advance()

    def _advance(self):
        # The sting is 7.2s and this screen can be skipped from 1.9s, so without
        # this it plays on under the next screen and collides with whatever is
        # there — two loud noises at once, neither landing.
        self.game.audio.stop("level_done")
        from game.core.play_state import PlayState
        self.game.pop()
        # ⚠️ The level is not the end of the run any more: clearing it opens the
        # duel (§9), and the **clock carries over** so the leaderboard still
        # measures the whole thing rather than restarting at the boss.
        self.game.switch(PlayState(self.game, duel=True, elapsed=self.elapsed,
                                   charges=self.charges))

    # ── draw ─────────────────────────────────────────────────────────────--
    def draw(self, surface):
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((8, 4, 10, min(210, int(self.t * 420))))
        surface.blit(dim, (0, 0))

        self._banner(surface, self.name_img, NAME_AT, H // 2 - 96)
        self._banner(surface, self.done_img, DONE_AT, H // 2 - 12)

        if self.t >= CAN_SKIP_AT:
            tip = self.font.render("Press Space or E to continue", True, (200, 190, 200))
            surface.blit(tip, ((W - tip.get_width()) // 2, H - 22))

    def _banner(self, surface, img, at, cy):
        """Drop in with an overshoot, then settle — a fade alone reads as limp."""
        age = self.t - at
        if age < 0:
            return
        if age < POP_TIME:
            p = age / POP_TIME
            scale = 1.0 + 0.35 * math.cos(p * math.pi / 2) * (1 - p)
            alpha = int(255 * min(1.0, p * 2.5))
        else:
            scale, alpha = 1.0, 255
        w = max(1, int(img.get_width() * scale))
        h = max(1, int(img.get_height() * scale))
        shown = pygame.transform.smoothscale(img, (w, h)) if scale != 1.0 else img.copy()
        shown.set_alpha(alpha)
        surface.blit(shown, ((W - w) // 2, cy - h // 2))
