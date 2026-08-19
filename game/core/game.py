"""Game: window, fixed-timestep main loop, and the state stack. See §3.3.

Renders to a small internal surface (640x360) then integer-scales it to the
window, giving crisp pixel art and cheap lighting later on.
"""
import pygame

import settings
from game.core.assets import AssetManager
from game.core.input import Input, InputState
from game.systems.eventbus import EventBus
from game.systems.audio import AudioSystem


class Game:
    def __init__(self):
        pygame.init()
        self.audio = AudioSystem()   # manages its own mixer init
        win_w = settings.INTERNAL_RES[0] * settings.WINDOW_SCALE
        win_h = settings.INTERNAL_RES[1] * settings.WINDOW_SCALE
        self.window = pygame.display.set_mode((win_w, win_h))
        pygame.display.set_caption(settings.CAPTION)
        self.render_surface = pygame.Surface(settings.INTERNAL_RES).convert()

        self.clock = pygame.time.Clock()
        self.assets = AssetManager()
        self.input = Input()
        self.bus = EventBus()

        self.state_stack = []
        self.running = True
        self.difficulty = "Normal"      # chosen in the menu; see systems/difficulty.py
        self.warrior = "elad"           # chosen in the menu; see entities/warriors.py

    # ── state stack ────────────────────────────────────────────────────────
    def push(self, state):
        self.state_stack.append(state)
        state.enter()

    def pop(self):
        if self.state_stack:
            self.state_stack.pop().exit()

    def switch(self, state):
        while self.state_stack:
            self.pop()
        self.push(state)

    # ── main loop ──────────────────────────────────────────────────────────
    def run(self):
        accumulator = 0.0
        # Presses land on render frames, but only sim steps act on them, and the
        # two run at different rates. Park each press here until a step takes it:
        # without this, a frame that ran no step ate the press (E felt broken
        # about half the time) and a frame that ran two fired it twice.
        pending = InputState()
        while self.running and self.state_stack:
            accumulator += self.clock.tick(settings.FPS_CAP) / 1000.0
            # avoid the "spiral of death" if a frame stalls badly
            accumulator = min(accumulator, 0.25)

            self._pump_events()
            inp = self.input.poll()
            pending.latch_edges_from(inp)

            while accumulator >= settings.FIXED_DT:
                if self.state_stack:
                    self.state_stack[-1].update(settings.FIXED_DT,
                                                inp.with_edges_of(pending))
                    pending.clear_edges()      # exactly one step per press
                accumulator -= settings.FIXED_DT

            self._draw()

        pygame.quit()

    def _pump_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.state_stack:
                self.state_stack[-1].handle_event(event)

    def _draw(self):
        # render bottom-up for states that let the one below show through
        first = len(self.state_stack) - 1
        while first > 0 and self.state_stack[first].draw_below:
            first -= 1
        for state in self.state_stack[first:]:
            state.draw(self.render_surface)

        pygame.transform.scale(self.render_surface, self.window.get_size(), self.window)
        pygame.display.flip()
