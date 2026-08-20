"""Shared fixtures. Everything here runs headless and touches no user data.

Two things every test in this suite depends on:

* **Headless SDL.** The drivers are set before pygame is imported anywhere, and
  a 1x1 display is opened once per session because `convert_alpha()` and font
  rendering both need one. Without the display, asset loading raises.
* **No writes outside the sandbox.** `systems.scores` normally writes to the
  player's real Application Support directory, so its path is redirected to a
  tmp file for the whole session. A test that saves a score must never land in
  the actual leaderboard.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame                                                    # noqa: E402
import pytest                                                    # noqa: E402

import settings                                                  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _sdl():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def _isolated_scores(tmp_path, monkeypatch):
    """Point the leaderboard at a throwaway file for every test."""
    from game.systems import scores
    monkeypatch.setattr(scores, "SCORES_PATH", str(tmp_path / "scores.json"))
    return scores


@pytest.fixture
def game():
    """A real Game with its window/audio/asset stack, minus the main loop."""
    from game.core.game import Game
    g = Game()
    yield g
    while g.state_stack:
        g.pop()


@pytest.fixture
def make_play(game):
    """Build a PlayState for a chosen warrior, entered and ready to step."""
    from game.core.play_state import PlayState

    def _make(warrior="wallad", clear_monsters=False):
        game.warrior = warrior
        ps = PlayState(game)
        game.push(ps)
        if clear_monsters:
            ps.monsters.clear()
        return ps
    return _make


@pytest.fixture
def play(make_play):
    return make_play()


@pytest.fixture
def surface():
    return pygame.Surface(settings.INTERNAL_RES)


@pytest.fixture
def inp():
    """A neutral InputState — no movement, no edges."""
    from game.core.input import InputState
    return InputState()


@pytest.fixture
def step():
    """Advance a state by whole simulation steps, drawing each frame.

    Drawing matters: a good few defects here are draw-time only (a bad rect, a
    surface built from a stale size), and a test that only updates never sees
    them.
    """
    def _step(state, frames=1, inp=None, surface=None, until=None):
        from game.core.input import InputState
        inp = inp or InputState()
        for i in range(frames):
            state.update(settings.FIXED_DT, inp)
            if surface is not None:
                state.draw(surface)
            if until is not None and until():
                return i + 1
        return frames
    return _step
