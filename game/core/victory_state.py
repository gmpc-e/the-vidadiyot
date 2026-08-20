"""VictoryState — the payoff + name entry + leaderboard.

Flow: the painted VICTORY! banner and the fanfare, then a name prompt, then the
top-players board. Enter advances / replays, Esc quits.

**No confetti and no balloons.** They were here first and they were wrong: this
is a horror-lite game about an abandoned school at night, and a birthday-party
particle system on top of a blood-drenched painted banner made the ending read
as a different game. Dust and embers replaced them and were still read as
confetti — the same drifting coloured specks, dressed differently. What rises
now is **skulls**: small, dark, sparse, and unmistakably not a celebration.

⚠️ **This screen owns the whole frame.** It used to draw the paused level
underneath, so the run's HUD — health bar, hotbar, book counter, a running
clock — sat behind the VICTORY banner, and the level's own camera shake was
still decaying under it. That is the "flaky, jiggling background": not a bug in
this file, but the fact that this file was never a screen, only an overlay.
`draw_below` is off and the background is painted here.

⚠️ **The banner is never rescaled *per frame*.** It used to "breathe" by
smoothscaling to a fractional size each frame, which resampled a 253px image on
a 640x360 surface that is then integer-scaled x2 — so the one painted asset on
the screen was also the blurriest thing on it. It is scaled **once, in
`enter()`**, to fill the frame, and does not move after that.
"""
import math
import random
import pygame

import settings
from game.core.state import State
from game.ui.hud import format_time
from game.ui.leaderboard import draw_board
from game.systems import scores

W, H = settings.INTERNAL_RES

# The banner is painted at 253x150 and the screen is 640x360 — a wider frame than
# the art, so filling it is driven by **width**, and the result is taller than the
# screen. That is deliberate: the banner is anchored to the top and its lower
# drips run off the bottom, which is what "fill the screen" has to mean for art
# of this shape. Scaled once at `enter()`, never per frame.
#
# ⚠️ The text then unavoidably sits **on** the banner, so it gets `SCRIM` behind
# it. Sizing the banner to clear the text instead was the first attempt and it
# put us back at roughly the original 253px — no larger than what we started
# with, which was the complaint.
BANNER_FILL = 0.94         # of the screen *width*
BANNER_TOP = -6            # a few px of bleed so the crown is not floating

# The dark panel the name entry and the leaderboard are drawn on. Sized for the
# **longer** of the two phases — a full board of 8 rows plus its title and the
# "new personal best" line — so the panel does not resize between them.
# ⚠️ **The two phases want different panels, and one rect could not serve both.**
# Name entry holds four short lines and should sit *low*, so the banner — the one
# painted asset on the screen, and the reason the screen exists — reads over it.
# The board holds a title, six rows and a prompt, so it needs height, and pushing
# it down far enough to clear the banner left the last row on the "play again"
# line. Sizing each for its own contents is what fixes both.
SCRIM_NAME = pygame.Rect(52, 214, 640 - 104, 128)
SCRIM_BOARD = pygame.Rect(52, 150, 640 - 104, 200)
SCRIM = SCRIM_BOARD          # the larger of the two, for anything measuring it
SCRIM_ALPHA = 232          # near-opaque: the banner's letters sit right behind it

# Rising skulls. Sparse and desaturated on purpose: at 640x360 a skull is about
# six pixels, and the read has to come from the *shape* — two eye sockets and a
# jaw notch — rather than from colour, which is why they are all bone-white and
# none of them are bright.
BONE = [(206, 200, 186), (176, 170, 158), (146, 141, 132)]
SKULL_COUNT = 22
MAX_NAME = 12


class VictoryState(State):
    draw_below = False        # see the docstring: the level's HUD showed through

    def __init__(self, game, elapsed):
        super().__init__(game)
        self.elapsed = elapsed

    def enter(self):
        self.game.audio.play_music("victory")   # falls through to whatever is playing until a victory track exists
        self.t = 0.0
        self.phase = "name"            # name -> board
        self.name = ""
        self.error = ""
        self.outcome = ""          # set once a run is recorded (new best, etc.)
        self.font_big = self.game.assets.font(None, 44)
        self.font_mid = self.game.assets.font(None, 22)
        self.font = self.game.assets.font(None, 16)
        self.banner = self._fit(self.game.assets.image("ui/victory_banner.png"))
        self.skulls = [self._new_skull(scatter=True) for _ in range(SKULL_COUNT)]
        self.game.audio.play_fanfare()

    @staticmethod
    def _fit(img):
        """Scale the banner to fill the frame — **once**, never per frame."""
        scale = W * BANNER_FILL / img.get_width()
        return pygame.transform.smoothscale(
            img, (int(img.get_width() * scale), int(img.get_height() * scale)))

    # ── particles ────────────────────────────────────────────────────────--
    def _new_skull(self, scatter=False):
        """One small skull drifting upward. `scatter` seeds the first screenful.

        Without it every one starts below the frame and the screen is empty for
        the first two seconds — exactly the beat the fanfare is playing over.
        """
        return {
            "x": random.uniform(0, W),
            "y": random.uniform(0, H) if scatter else H + random.uniform(0, 40),
            "rise": random.uniform(6, 19),          # px/sec, slow: they float
            "sway": random.uniform(3, 11),
            "phase": random.uniform(0, math.tau),
            "big": random.random() < 0.35,          # 7px across rather than 5
            "color": random.choice(BONE),
            "alpha": random.randint(55, 135),
        }

    # ── input ────────────────────────────────────────────────────────────--
    def handle_event(self, event):
        if self.phase != "name" or event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_RETURN:
            self._submit_name()
        elif event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
            self.error = ""
        elif event.unicode and event.unicode.isprintable() and len(self.name) < MAX_NAME:
            if event.unicode.strip() or (self.name and event.unicode == " "):
                self.name += event.unicode
                self.error = ""

    def _submit_name(self):
        """Record the run. A returning player keeps whichever time is better."""
        name = self.name.strip()
        if not name:
            self.error = "Enter a name"
            return
        result = scores.add(name, self.elapsed)
        if result == scores.INVALID:
            self.error = "Enter a name"
            return
        if result == scores.SLOWER:
            # Not an error: the run counted, it just didn't beat their record.
            self.outcome = f"Your best still stands: {format_time(scores.best_time(name))}"
        elif result == scores.IMPROVED:
            self.outcome = "NEW PERSONAL BEST!"
        else:
            self.outcome = ""
        self.phase = "board"

    # ── loop ─────────────────────────────────────────────────────────────--
    def update(self, dt, inp):
        self.t += dt
        for sk in self.skulls:
            sk["y"] -= sk["rise"] * dt
            if sk["y"] < -10:
                sk.update(self._new_skull())

        if inp.pause:
            from game.core.menu_state import MenuState
            self.game.switch(MenuState(self.game))
        elif self.phase == "board" and (inp.interact or inp.attack or inp.confirm):
            from game.core.play_state import PlayState
            self.game.switch(PlayState(self.game))

    # ── draw ─────────────────────────────────────────────────────────────--
    def draw(self, surface):
        # Opaque, not a wash: nothing is drawn under this screen any more.
        surface.fill((8, 7, 12))
        self._draw_skulls(surface)
        self._draw_ribbon(surface)
        self._draw_scrim(surface)

        if self.phase == "name":
            self._draw_name_entry(surface)
        else:
            # Six: what `SCRIM_BOARD` is sized to hold alongside the title, the
            # "NEW PERSONAL BEST" line and the prompt. The full board lives on
            # the menu's own leaderboard screen, which has the whole frame.
            draw_board(surface, self.font, self.font_mid, scores.top(6),
                       W // 2, self.scrim.y + 34, highlight=self.name)
            if self.outcome:
                note = self.font.render(self.outcome, True, (250, 225, 150))
                surface.blit(note, ((W - note.get_width()) // 2, self.scrim.y + 12))
            tip = self.font.render("Enter: play again    Esc: main menu", True, (200, 200, 215))
            surface.blit(tip, ((W - tip.get_width()) // 2, self.scrim.bottom - 18))

    @property
    def scrim(self):
        return SCRIM_NAME if self.phase == "name" else SCRIM_BOARD

    def _draw_scrim(self, surface):
        """The panel the text sits on, so it stays readable over the banner."""
        box = self.scrim
        panel = pygame.Surface(box.size, pygame.SRCALPHA)
        panel.fill((6, 5, 9, SCRIM_ALPHA))
        surface.blit(panel, box.topleft)
        pygame.draw.rect(surface, (92, 74, 46), box, 1)

    def _draw_name_entry(self, surface):
        y = self.scrim.y + 18
        tm = self.font.render(f"Time  {format_time(self.elapsed)}", True, (245, 245, 250))
        surface.blit(tm, ((W - tm.get_width()) // 2, y))
        prompt = self.font.render("Enter your name:", True, (220, 220, 230))
        surface.blit(prompt, ((W - prompt.get_width()) // 2, y + 22))
        caret = "_" if int(self.t * 2) % 2 == 0 else " "
        box = self.font_mid.render(self.name + caret, True, (255, 255, 255))
        bw = max(160, box.get_width() + 20)
        rect = pygame.Rect(0, 0, bw, box.get_height() + 8); rect.center = (W // 2, y + 56)
        pygame.draw.rect(surface, (0, 0, 0, 180), rect)
        pygame.draw.rect(surface, (255, 220, 120), rect, 1)
        surface.blit(box, (rect.centerx - box.get_width() // 2, rect.centery - box.get_height() // 2))
        if self.error:
            err = self.font.render(self.error, True, (250, 120, 120))
            surface.blit(err, ((W - err.get_width()) // 2, rect.bottom + 6))

    def _draw_skulls(self, surface):
        layer = pygame.Surface((W, H), pygame.SRCALPHA)
        for sk in self.skulls:
            x = int(sk["x"] + math.sin(self.t * 0.7 + sk["phase"]) * sk["sway"])
            self._skull(layer, x, int(sk["y"]), (*sk["color"], sk["alpha"]),
                        big=sk["big"])
        surface.blit(layer, (0, 0))

    @staticmethod
    def _skull(surface, x, y, rgba, big=False):
        """A 5x6 (or 7x8) skull, drawn as rectangles.

        Deliberately not a font glyph or a circle: at this size a skull is
        legible only if the two sockets and the jaw notch are placed on exact
        pixels, and any smoothing turns it into a blob.
        """
        w, h = (7, 8) if big else (5, 6)
        eye = 2 if big else 1
        cranium = h - (3 if big else 2)
        surface.fill(rgba, (x, y, w, cranium))                 # dome
        surface.fill(rgba, (x + 1, y + cranium, w - 2, h - cranium))   # jaw
        hole = (0, 0, 0, 0)
        surface.fill(hole, (x + 1, y + cranium - eye - 1, eye, eye))   # left eye
        surface.fill(hole, (x + w - 1 - eye, y + cranium - eye - 1, eye, eye))
        surface.fill(hole, (x + w // 2, y + h - 1, 1, 1))              # jaw notch

    def _draw_ribbon(self, surface):
        """The painted banner, scaled once in `enter()` and static thereafter.

        See the module docstring: rescaling it per frame was what made the one
        painted asset on this screen the softest thing on it, and pulsing its
        alpha on top of a live level was half of the "jiggling".
        """
        surface.blit(self.banner, ((W - self.banner.get_width()) // 2, BANNER_TOP))
