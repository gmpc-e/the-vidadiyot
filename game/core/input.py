"""Input -> intent mapping. Keyboard/gamepad translate to abstract intents
("move", "interact", "sprint", "power") so gameplay code never references raw
keycodes.
"""
import pygame


class InputState:
    """Snapshot of intents for one frame.

    Edge intents (a *press*, not a hold) need care: the render loop polls every
    frame, but the simulation steps on a fixed timestep, so a frame that runs no
    sim step would otherwise swallow the press outright — and a frame that runs
    two would fire it twice. `Game.run` latches edges into a pending state and
    hands them to exactly one step; see `latch_edges_from` / `with_edges_of`.
    """

    EDGE_FIELDS = ("interact", "attack", "pause", "mute", "power", "confirm")

    def __init__(self):
        self.move = pygame.Vector2(0, 0)   # normalized direction, magnitude 0..1
        self.sprint = False
        self.interact = False              # edge: True only on the press frame
        self.attack = False                # edge
        self.confirm = False               # edge: Enter, for menus only
        self.pause = False                 # edge
        self.mute = False                  # edge
        self.power = False                 # edge: the warrior's active power (Z)


    # ── edge latching (see the class docstring) ──────────────────────────--
    def latch_edges_from(self, other):
        """Remember any edge that fired in `other`, until a sim step takes it."""
        for field in self.EDGE_FIELDS:
            if getattr(other, field):
                setattr(self, field, True)

    def clear_edges(self):
        for field in self.EDGE_FIELDS:
            setattr(self, field, False)

    def with_edges_of(self, pending):
        """This frame's continuous intents, plus whichever edges are pending."""
        merged = InputState()
        merged.move = self.move
        merged.sprint = self.sprint
        for field in self.EDGE_FIELDS:
            setattr(merged, field, getattr(pending, field))
        return merged


class Input:
    def __init__(self):
        self._prev_keys = pygame.key.get_pressed()

    def poll(self):
        """Build the per-frame InputState. Call once per frame before update."""
        keys = pygame.key.get_pressed()
        state = InputState()

        x = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        x -= keys[pygame.K_a] or keys[pygame.K_LEFT]
        y = keys[pygame.K_s] or keys[pygame.K_DOWN]
        y -= keys[pygame.K_w] or keys[pygame.K_UP]
        move = pygame.Vector2(x, y)
        if move.length_squared() > 0:
            move = move.normalize()
        state.move = move

        state.sprint = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        state.interact = self._pressed(keys, pygame.K_e)
        state.attack = self._pressed(keys, pygame.K_SPACE)
        # ⚠️ Enter is a *menu* confirm, not an attack. The end screens say
        # "Enter: play again" and only Space actually worked; rather than fix
        # the label, both now do. It is deliberately not folded into `attack` —
        # binding Enter to the sword would let a player swing from the menu key.
        state.confirm = self._pressed(keys, pygame.K_RETURN) or \
            self._pressed(keys, pygame.K_KP_ENTER)
        state.pause = self._pressed(keys, pygame.K_ESCAPE)
        state.mute = self._pressed(keys, pygame.K_m)
        state.power = self._pressed(keys, pygame.K_z)

        self._prev_keys = keys
        return state

    def _pressed(self, keys, key):
        """True only on the frame the key transitions up->down."""
        return keys[key] and not self._prev_keys[key]
