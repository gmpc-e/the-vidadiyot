"""State base + a state stack driven by the Game loop.

The stack lets states layer: PlayState runs underneath PauseState, which can
draw the frozen game behind its menu. Only the top state updates by default.
"""


class State:
    def __init__(self, game):
        self.game = game

    # ── lifecycle ──────────────────────────────────────────────────────────
    def enter(self):
        """Called when this state becomes the top of the stack."""

    def exit(self):
        """Called when this state is popped."""

    # ── per-frame ──────────────────────────────────────────────────────────
    def handle_event(self, event):
        """Discrete pygame events (QUIT, window, etc.)."""

    def update(self, dt, inp):
        """Fixed-timestep update. `inp` is the frame's InputState."""

    def draw(self, surface):
        """Render onto the internal render surface."""

    # states that let the state below keep drawing (e.g. a pause overlay)
    draw_below = False
