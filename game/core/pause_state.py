"""PauseState — overlay drawn over the frozen game. Esc/Enter resume, Q -> menu."""
import pygame

import settings
from game.core.state import State

W, H = settings.INTERNAL_RES


class PauseState(State):
    draw_below = True

    def enter(self):
        self.font_big = self.game.assets.font(None, 36)
        self.font = self.game.assets.font(None, 16)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_p):
            self.game.pop()                         # resume
        elif event.key == pygame.K_q:
            from game.core.menu_state import MenuState
            self.game.switch(MenuState(self.game))

    def update(self, dt, inp):
        pass

    def draw(self, surface):
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((10, 10, 18, 170))
        surface.blit(dim, (0, 0))
        title = self.font_big.render("PAUSED", True, (235, 235, 245))
        surface.blit(title, ((W - title.get_width()) // 2, H // 2 - 30))
        tip = self.font.render("Esc: resume     Q: main menu", True, (200, 200, 215))
        surface.blit(tip, ((W - tip.get_width()) // 2, H // 2 + 10))
