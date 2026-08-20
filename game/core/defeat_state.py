"""DefeatState — the painted YOU LOST!! scene when the player's health runs out.

Shows the leaderboard (no name entry — you didn't finish). Enter, E or Space
replays, Esc goes back to the menu.

**It owns the whole frame**, for the same reason the victory screen does: it used
to draw the paused level underneath through a red wash, so the run's HUD — health
bar, hotbar, a running clock — sat behind the banner announcing the run was over.

⚠️ **The scene is painted, the *motion* is not.** `ui/defeat_scene.png` is one
still image; what moves is a slow push-in on it and a shudder as it lands, both
done by blitting the same surface at different scales. A still image on a screen
you sit and read is the difference between a game over and a wallpaper — but it
is scaled **once per frame from one source**, never resampled in a chain.
"""
import math
import pygame

import settings
from game.core.assets import load
from game.core.state import State
from game.ui.leaderboard import draw_board
from game.systems import scores

W, H = settings.INTERNAL_RES


# How far in the scene starts, and how long it takes to settle. A push-in this
# small is barely a move — which is the point: it should feel like the room
# closing in, not like a slideshow transition.
ZOOM_FROM = 1.14
ZOOM_TIME = 2.6
SHUDDER_TIME = 0.55       # seconds of impact shake as it arrives

# The panel the leaderboard sits on. The scene is busy everywhere, so the text
# needs its own ground or it is unreadable over the blood.
SCRIM = pygame.Rect(64, 176, 640 - 128, 172)
SCRIM_ALPHA = 214


class DefeatState(State):
    draw_below = False        # it used to show the dead run's HUD underneath

    def enter(self):
        self.game.audio.play_music("defeat")   # falls through to whatever is playing until a defeat track exists
        self.t = 0.0
        self.font_big = self.game.assets.font(None, 44)
        self.font_mid = self.game.assets.font(None, 22)
        self.font = self.game.assets.font(None, 16)
        self.scene = load("ui/defeat_scene.png")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self._retry()

    def _retry(self):
        from game.core.play_state import PlayState
        self.game.switch(PlayState(self.game))

    def update(self, dt, inp):
        self.t += dt
        if inp.pause:
            from game.core.menu_state import MenuState
            self.game.switch(MenuState(self.game))
        elif inp.interact or inp.attack or inp.confirm:
            self._retry()

    def draw(self, surface):
        surface.fill((14, 3, 5))
        if self.scene:
            self._draw_scene(surface)
        else:
            self._draw_banner(surface)      # no art installed: the old text
        panel = pygame.Surface(SCRIM.size, pygame.SRCALPHA)
        panel.fill((10, 2, 4, SCRIM_ALPHA))
        surface.blit(panel, SCRIM.topleft)
        pygame.draw.rect(surface, (104, 30, 34), SCRIM, 1)

        draw_board(surface, self.font, self.font_mid, scores.top(6),
                   W // 2, SCRIM.y + 14)
        tip = self.font.render("Enter: try again    Esc: main menu", True, (220, 200, 205))
        surface.blit(tip, ((W - tip.get_width()) // 2, SCRIM.bottom - 18))

    def _draw_scene(self, surface):
        """The push-in. Eased so it decelerates into place rather than stopping."""
        t = min(1.0, self.t / ZOOM_TIME)
        zoom = ZOOM_FROM + (1.0 - ZOOM_FROM) * (1 - (1 - t) ** 3)
        w, h = int(W * zoom), int(H * zoom)
        shake = 0
        if self.t < SHUDDER_TIME:
            fade = 1.0 - self.t / SHUDDER_TIME
            shake = int(math.sin(self.t * 46.0) * 3.0 * fade)
        img = self.scene if zoom == 1.0 else pygame.transform.smoothscale(self.scene, (w, h))
        surface.blit(img, ((W - w) // 2 + shake, (H - h) // 2))

    def _draw_banner(self, surface):
        shake = math.sin(self.t * 22.0) * 2.0 if self.t < 0.6 else 0.0
        text = self.font_big.render("YOU LOST !!!", True, (255, 235, 235))
        tw, th = text.get_size()
        cx, cy = W // 2 + shake, H // 2 - 42
        band = pygame.Rect(0, 0, tw + 70, th + 22); band.center = (cx, cy)
        pygame.draw.rect(surface, (120, 20, 24), band)
        pygame.draw.rect(surface, (230, 90, 90), band, 3)
        surface.blit(text, (cx - tw // 2, cy - th // 2))
