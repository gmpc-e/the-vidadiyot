"""VictoryState — celebration + name entry + leaderboard.

Flow: the painted VICTORY! banner with confetti & balloons and the fanfare, then
a name prompt (unique names only), then the top-players leaderboard. Enter
advances / replays, Esc quits.
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
FESTIVE = [
    (240, 80, 90), (250, 200, 60), (90, 200, 120),
    (90, 160, 240), (200, 120, 220), (250, 140, 70),
]
MAX_NAME = 12


class VictoryState(State):
    draw_below = True

    def __init__(self, game, elapsed):
        super().__init__(game)
        self.elapsed = elapsed

    def enter(self):
        self.t = 0.0
        self.phase = "name"            # name -> board
        self.name = ""
        self.error = ""
        self.font_big = self.game.assets.font(None, 44)
        self.font_mid = self.game.assets.font(None, 22)
        self.font = self.game.assets.font(None, 16)
        self.banner = self.game.assets.image("ui/victory_banner.png")
        self.confetti = [self._new_confetto(burst=True) for _ in range(140)]
        self.balloons = [self._new_balloon(i) for i in range(9)]
        self.game.audio.play_fanfare()

    # ── particles ────────────────────────────────────────────────────────--
    def _new_confetto(self, burst=False):
        return {
            "x": random.uniform(0, W),
            "y": random.uniform(-40, H * 0.5) if burst else random.uniform(-H, 0),
            "vx": random.uniform(-30, 30), "vy": random.uniform(40, 120),
            "size": random.randint(3, 6), "color": random.choice(FESTIVE),
            "spin": random.uniform(-6, 6), "rot": random.uniform(0, math.tau),
        }

    def _new_balloon(self, i):
        return {
            "x": (i + 0.5) * (W / 9) + random.uniform(-10, 10),
            "y": H + random.uniform(0, H), "speed": random.uniform(18, 34),
            "phase": random.uniform(0, math.tau), "color": FESTIVE[i % len(FESTIVE)],
            "r": random.randint(12, 18),
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
        name = self.name.strip()
        if not name:
            self.error = "Enter a name"
            return
        if scores.name_taken(name):
            self.error = "Name already taken — pick another"
            return
        scores.add(name, self.elapsed)
        self.phase = "board"

    # ── loop ─────────────────────────────────────────────────────────────--
    def update(self, dt, inp):
        self.t += dt
        for c in self.confetti:
            c["x"] += c["vx"] * dt; c["y"] += c["vy"] * dt; c["rot"] += c["spin"] * dt
            if c["y"] > H + 10:
                c.update(self._new_confetto()); c["y"] = -10
        for b in self.balloons:
            b["y"] -= b["speed"] * dt
            if b["y"] < -40:
                b.update(self._new_balloon(0)); b["y"] = H + 30

        if inp.pause:
            from game.core.menu_state import MenuState
            self.game.switch(MenuState(self.game))
        elif self.phase == "board" and (inp.interact or inp.attack):
            from game.core.play_state import PlayState
            self.game.switch(PlayState(self.game))

    # ── draw ─────────────────────────────────────────────────────────────--
    def draw(self, surface):
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((10, 10, 20, 160))
        surface.blit(dim, (0, 0))
        for b in self.balloons:
            self._draw_balloon(surface, b)
        for c in self.confetti:
            s = c["size"]
            dx, dy = math.cos(c["rot"]) * s, math.sin(c["rot"]) * s
            pygame.draw.line(surface, c["color"], (c["x"] - dx, c["y"] - dy),
                             (c["x"] + dx, c["y"] + dy), 3)
        self._draw_ribbon(surface)

        if self.phase == "name":
            self._draw_name_entry(surface)
        else:
            draw_board(surface, self.font, self.font_mid, scores.top(8),
                       W // 2, H // 2 + 26, highlight=self.name)
            tip = self.font.render("Enter: play again    Esc: main menu", True, (200, 200, 215))
            surface.blit(tip, ((W - tip.get_width()) // 2, H - 22))

    def _draw_name_entry(self, surface):
        y = H // 2 + 26
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

    def _draw_balloon(self, surface, b):
        sway = math.sin(self.t * 1.5 + b["phase"]) * 8
        x, y = int(b["x"] + sway), int(b["y"])
        pygame.draw.line(surface, (180, 180, 190), (x, y + b["r"]), (x, y + b["r"] + 22), 1)
        pygame.draw.ellipse(surface, b["color"], (x - b["r"], y - b["r"], b["r"] * 2, int(b["r"] * 2.4)))
        pygame.draw.ellipse(surface, (255, 255, 255), (x - b["r"] // 2, y - b["r"], b["r"], b["r"]), 0)

    def _draw_ribbon(self, surface):
        """The painted banner, breathing gently so it doesn't sit dead still."""
        pulse = 1.0 + 0.03 * math.sin(self.t * 3.4)
        w = max(1, int(self.banner.get_width() * pulse))
        h = max(1, int(self.banner.get_height() * pulse))
        img = pygame.transform.smoothscale(self.banner, (w, h)) if pulse != 1.0 else self.banner
        surface.blit(img, ((W - w) // 2, H // 2 - 46 - h // 2))
