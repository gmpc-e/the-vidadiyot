"""DefeatState — a big YOU LOST!!! banner when the player's health runs out.

Shows the leaderboard (no name entry — you didn't finish). Enter (or the
interact/attack keys) replays, Esc goes back to the menu. Draws over the frozen
game.

Enter is handled as a raw event rather than as an intent: `Input` maps no intent
to Return, so the on-screen "Enter: try again" prompt was previously a dead key
and only E/Space worked.
"""
import math
import pygame

import settings
from game.core.state import State
from game.ui.leaderboard import draw_board
from game.systems import scores

W, H = settings.INTERNAL_RES


class DefeatState(State):
    draw_below = True

    def enter(self):
        self.t = 0.0
        self.font_big = self.game.assets.font(None, 44)
        self.font_mid = self.game.assets.font(None, 22)
        self.font = self.game.assets.font(None, 16)

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
        elif inp.interact or inp.attack:
            self._retry()

    def draw(self, surface):
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((30, 6, 8, 190))
        surface.blit(dim, (0, 0))

        self._draw_banner(surface)
        draw_board(surface, self.font, self.font_mid, scores.top(8), W // 2, H // 2 + 24)
        tip = self.font.render("Enter: try again    Esc: main menu", True, (220, 200, 205))
        surface.blit(tip, ((W - tip.get_width()) // 2, H - 22))

    def _draw_banner(self, surface):
        shake = math.sin(self.t * 22.0) * 2.0 if self.t < 0.6 else 0.0
        text = self.font_big.render("YOU LOST !!!", True, (255, 235, 235))
        tw, th = text.get_size()
        cx, cy = W // 2 + shake, H // 2 - 42
        band = pygame.Rect(0, 0, tw + 70, th + 22); band.center = (cx, cy)
        pygame.draw.rect(surface, (120, 20, 24), band)
        pygame.draw.rect(surface, (230, 90, 90), band, 3)
        surface.blit(text, (cx - tw // 2, cy - th // 2))
