"""Input intents and the edge-latching contract in the main loop.

The latching is the important part: presses arrive on render frames but only
sim steps act on them, and the two run at different rates.
"""
import pygame

import settings
from game.core.input import InputState


def _replay(frame_times, press_frame, field="interact"):
    """Replay Game.run's timing and count how often a press is delivered."""
    acc, delivered, pending = 0.0, 0, InputState()
    for i, ft in enumerate(frame_times):
        acc = min(acc + ft, 0.25)
        frame = InputState()
        setattr(frame, field, i == press_frame)
        pending.latch_edges_from(frame)
        while acc >= settings.FIXED_DT:
            if getattr(frame.with_edges_of(pending), field):
                delivered += 1
            pending.clear_edges()
            acc -= settings.FIXED_DT
    return delivered


def test_a_fresh_state_has_no_intents():
    s = InputState()
    assert s.move == pygame.Vector2(0, 0)
    assert not any(getattr(s, f) for f in InputState.EDGE_FIELDS)
    assert not s.sprint


def test_every_edge_field_exists_on_the_state():
    s = InputState()
    for field in InputState.EDGE_FIELDS:
        assert hasattr(s, field), f"{field} is declared an edge but has no slot"


def test_latching_keeps_an_edge_until_a_step_takes_it():
    pending, frame = InputState(), InputState()
    frame.interact = True
    pending.latch_edges_from(frame)
    assert pending.interact
    pending.clear_edges()
    assert not pending.interact


def test_latching_never_clears_an_edge_that_is_already_waiting():
    pending = InputState()
    pending.interact = True
    pending.latch_edges_from(InputState())        # a frame with nothing pressed
    assert pending.interact, "a quiet frame must not swallow a waiting press"


def test_with_edges_of_keeps_this_frames_movement():
    frame = InputState()
    frame.move = pygame.Vector2(1, 0)
    frame.sprint = True
    pending = InputState()
    pending.attack = True
    merged = frame.with_edges_of(pending)
    assert merged.move == pygame.Vector2(1, 0) and merged.sprint
    assert merged.attack and not merged.interact


def test_a_press_is_delivered_exactly_once_at_120fps():
    """The original bug: half of all presses died on frames that ran no step."""
    frames = [1 / 120] * 40
    assert all(_replay(frames, i) == 1 for i in range(30))


def test_a_press_is_delivered_exactly_once_when_frames_starve_the_sim():
    frames = [0.004] * 60                     # 250fps render, 60Hz sim
    assert all(_replay(frames, i) == 1 for i in range(50))


def test_a_stalled_frame_does_not_repeat_one_press():
    frames = [1 / 120] * 5 + [0.05] + [1 / 120] * 5
    assert _replay(frames, 5) == 1


def test_every_edge_field_survives_the_loop():
    frames = [1 / 120] * 20
    for field in InputState.EDGE_FIELDS:
        assert _replay(frames, 4, field) == 1, f"{field} was dropped"


def test_a_slow_frame_still_delivers_its_press():
    """One 200ms hitch: the press lands, once, despite many steps running."""
    assert _replay([0.2, 1 / 60, 1 / 60], 0) == 1
