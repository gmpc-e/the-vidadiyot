"""Game loop plumbing, the state stack, menus, HUD, camera, audio."""
import os

import pygame
import pytest

import settings
from game.core.camera import Camera
from game.core.game import Game
from game.core.input import InputState
from game.core.menu_state import (HowToState, LeaderboardState, MenuState,
                                  WarriorSelectState)
from game.core.pause_state import PauseState
from game.core.play_state import PlayState
from game.core.state import State
from game.entities import warriors
from game.systems import audio


def _key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


# ── state stack ───────────────────────────────────────────────────────────
def test_push_enters_and_pop_exits():
    seen = []

    class Probe(State):
        def enter(self): seen.append("enter")
        def exit(self): seen.append("exit")

    g = Game()
    g.push(Probe(g))
    g.pop()
    assert seen == ["enter", "exit"]


def test_switch_unwinds_the_whole_stack(game):
    game.push(MenuState(game))
    game.push(PauseState(game))
    game.switch(MenuState(game))
    assert len(game.state_stack) == 1


def test_popping_an_empty_stack_is_safe(game):
    while game.state_stack:
        game.pop()
    game.pop()


def test_the_game_starts_with_sane_defaults(game):
    assert game.difficulty in ("Easy", "Normal", "Hard")
    assert game.warrior in warriors.BY_ID
    assert game.running


# ── camera ────────────────────────────────────────────────────────────────
def test_the_camera_ignores_movement_inside_the_dead_zone():
    c = Camera((640, 360))
    c.snap_to((1000, 1000))
    before = pygame.Vector2(c.pos)
    c.update(0.1, (1000 + settings.CAMERA_DEADZONE[0] - 5, 1000))
    assert c.pos == before


def test_the_camera_follows_once_the_target_leaves_the_dead_zone():
    c = Camera((640, 360))
    c.snap_to((1000, 1000))
    c.update(0.1, (1000 + settings.CAMERA_DEADZONE[0] + 50, 1000))
    assert c.pos.x > 1000 - 320


def test_the_camera_clamps_to_the_world():
    c = Camera((640, 360))
    c.set_world_bounds(pygame.Rect(0, 0, 1000, 800))
    c.snap_to((0, 0))
    assert c.pos.x >= 0 and c.pos.y >= 0
    c.snap_to((10000, 10000))
    assert c.pos.x <= 1000 - 640 and c.pos.y <= 800 - 360


def test_shake_offsets_the_view_and_then_stops():
    c = Camera((640, 360))
    c.snap_to((500, 500))
    c.shake(8, 0.2)
    offsets = {tuple(c.offset) for _ in range(20)}
    assert len(offsets) > 1, "a shaking camera should jitter"
    c.update(0.5, (500, 500))
    steady = {tuple(c.offset) for _ in range(10)}
    assert len(steady) == 1, "the shake must settle"


def test_world_to_screen_subtracts_the_camera():
    c = Camera((640, 360))
    c.snap_to((320, 180))
    assert c.world_to_screen((320, 180)) == pygame.Vector2(320, 180)


# ── menu ──────────────────────────────────────────────────────────────────
def test_menu_selection_wraps_both_ways(game):
    from game.core import menu_state
    m = MenuState(game)
    game.push(m)
    last = len(menu_state.ITEMS) - 1
    m.sel = 0
    m.handle_event(_key(pygame.K_UP))
    assert m.sel == last
    m.handle_event(_key(pygame.K_DOWN))
    assert m.sel == 0


def test_q_and_escape_both_quit_from_the_title(game):
    for key in (pygame.K_q, pygame.K_ESCAPE):
        g = Game()
        m = MenuState(g)
        g.push(m)
        m.handle_event(_key(key))
        assert not g.running, f"{pygame.key.name(key)} should quit"


def test_left_and_right_only_change_difficulty_on_its_own_row(game):
    from game.core import menu_state
    m = MenuState(game)
    game.push(m)
    m.sel = menu_state.ITEMS.index("play")
    before = game.difficulty
    m.handle_event(_key(pygame.K_RIGHT))
    assert game.difficulty == before
    m.sel = menu_state.ITEMS.index("difficulty")
    m.handle_event(_key(pygame.K_RIGHT))
    assert game.difficulty != before


def test_the_warrior_row_switches_in_place_without_opening_the_page(game):
    """Most of the time you already know who you want; opening a page to press
    Right once and back out is three keys too many."""
    from game.core import menu_state
    m = MenuState(game)
    game.push(m)
    m.sel = menu_state.ITEMS.index("warrior")
    first = game.warrior
    m.handle_event(_key(pygame.K_RIGHT))
    assert game.warrior != first
    assert isinstance(game.state_stack[-1], MenuState), "it must not open a screen"
    m.handle_event(_key(pygame.K_LEFT))
    assert game.warrior == first, "and it must go back the other way"


def test_switching_warriors_wraps_around_the_roster(game):
    from game.core import menu_state
    m = MenuState(game)
    game.push(m)
    m.sel = menu_state.ITEMS.index("warrior")
    first = game.warrior
    for _ in range(len(warriors.WARRIORS)):
        m.handle_event(_key(pygame.K_RIGHT))
    assert game.warrior == first


def test_the_menu_shows_every_warrior_and_every_monster(game, surface):
    """The title screen is the cast list; a character added to the roster with
    no menu crop would only fail here, at draw time."""
    m = MenuState(game)
    game.push(m)
    for w in warriors.WARRIORS:
        assert game.assets.image(f"sprites/{w['id']}_menu.png").get_width() > 0
    for name in ("snir_menu", "terror_menu", "emri_menu"):
        assert game.assets.image(f"sprites/{name}.png").get_width() > 0
    for w in warriors.WARRIORS:
        game.warrior = w["id"]
        m.update(0.3, InputState())
        m.draw(surface)


def test_play_starts_a_run(game):
    from game.core import menu_state
    m = MenuState(game)
    game.push(m)
    m.sel = menu_state.ITEMS.index("play")
    m.handle_event(_key(pygame.K_RETURN))
    assert isinstance(game.state_stack[-1], PlayState)


@pytest.mark.parametrize("row,cls", [
    ("howto", HowToState), ("leaderboard", LeaderboardState),
    ("warrior", WarriorSelectState),
])
def test_each_row_opens_its_screen(game, row, cls):
    from game.core import menu_state
    m = MenuState(game)
    game.push(m)
    m.sel = menu_state.ITEMS.index(row)
    m.handle_event(_key(pygame.K_RETURN))
    assert isinstance(game.state_stack[-1], cls)


def test_the_title_block_never_collides_with_the_menu_or_the_tip(game, surface):
    """The six rows sit in ~135px between the art and the key tip; a nudge to any
    constant can silently overlap them, and that only shows up as a screenshot."""
    from game.core import menu_state as M
    m = MenuState(game)
    game.push(m)
    title = game.assets.image("ui/title.png")
    rule = game.assets.image("ui/title_rule.png")
    art_bottom = M.TITLE_Y + title.get_height() + M.RULE_GAP + rule.get_height()
    last_row = M.MENU_TOP + M.MENU_STEP * (len(M.ITEMS) - 1) + m.font.get_height()
    tip_y = settings.INTERNAL_RES[1] - 14
    assert art_bottom < M.MENU_TOP
    assert last_row + 4 <= tip_y
    assert tip_y + m.small.get_height() <= settings.INTERNAL_RES[1]


def test_every_menu_screen_draws(game, surface):
    m = MenuState(game)
    game.push(m)
    from game.core import menu_state
    for i in range(len(menu_state.ITEMS)):
        m.sel = i
        m.update(0.1, InputState())
        m.draw(surface)
    for cls in (HowToState, LeaderboardState, WarriorSelectState, PauseState):
        s = cls(game)
        game.push(s)
        s.update(0.1, InputState())
        s.draw(surface)
        game.pop()


# ── warrior select ────────────────────────────────────────────────────────
def test_the_select_screen_opens_on_the_current_warrior(game):
    game.warrior = "roni"
    s = WarriorSelectState(game)
    game.push(s)
    assert s.warrior["id"] == "roni"


def test_choosing_sticks_and_wraps(game):
    s = WarriorSelectState(game)
    game.push(s)
    for _ in range(len(warriors.WARRIORS)):
        s.handle_event(_key(pygame.K_RIGHT))
    assert s.i == 0, "it should wrap around"
    s.handle_event(_key(pygame.K_LEFT))
    s.handle_event(_key(pygame.K_RETURN))
    assert game.warrior == warriors.WARRIORS[-1]["id"]


def test_leaving_with_escape_still_confirms_the_shown_warrior(game):
    """The page always shows exactly one warrior, so backing out has to mean
    'take this one' — anything else leaves the screen lying to the player."""
    s = WarriorSelectState(game)
    game.push(s)
    s.handle_event(_key(pygame.K_RIGHT))
    shown = s.warrior["id"]
    s.handle_event(_key(pygame.K_ESCAPE))
    assert game.warrior == shown


def test_long_power_text_is_wrapped_not_clipped(game):
    s = WarriorSelectState(game)
    game.push(s)
    font = game.assets.font(None, 14)
    for w in warriors.WARRIORS:
        for line in s._wrap(w["power_help"], font, 388):
            assert font.size(line)[0] <= 388


# ── pause ─────────────────────────────────────────────────────────────────
def test_escape_resumes_and_q_returns_to_the_menu(game):
    game.push(PlayState(game))
    p = PauseState(game)
    game.push(p)
    p.handle_event(_key(pygame.K_ESCAPE))
    assert isinstance(game.state_stack[-1], PlayState)

    p2 = PauseState(game)
    game.push(p2)
    p2.handle_event(_key(pygame.K_q))
    assert isinstance(game.state_stack[-1], MenuState)


def test_pause_draws_the_game_underneath():
    assert PauseState.draw_below


# ── HUD ───────────────────────────────────────────────────────────────────
def test_the_hud_draws_for_both_warriors(make_play, surface):
    for wid in ("wallad", "roni"):
        p = make_play(wid)
        p.hud.draw(surface, p.player, p._counters(), "a hint", 61.5,
                   flashes={"book": 0.5})


def test_only_a_warrior_with_a_power_gets_charge_pips(make_play, surface):
    """Elad's row would be permanently empty, which reads as a bug."""
    calls = []
    for wid in ("wallad", "roni"):
        p = make_play(wid)
        orig = pygame.draw.rect
        try:
            pygame.draw.rect = lambda *a, **k: calls.append(wid) or orig(*a, **k)
            p.hud._draw_power(surface, p.player)
        finally:
            pygame.draw.rect = orig
    assert "roni" in calls and "wallad" not in calls


def test_the_timer_formats_as_minutes_and_seconds():
    from game.ui.hud import format_time
    assert format_time(0) == "0:00"
    assert format_time(61.9) == "1:01"
    assert format_time(600) == "10:00"


def test_the_hud_survives_a_dead_player(make_play, surface):
    p = make_play()
    p.player.health = 0
    p.hud.draw(surface, p.player, p._counters(), None, 0.0)


# ── audio ─────────────────────────────────────────────────────────────────
def test_every_registered_sound_resolves_to_something_audible(game):
    """Whether it comes from a file or the synth, every registered name plays."""
    for name in audio.SYNTHS:
        snd = game.audio._get_sfx(name)
        assert snd is not None and snd.get_length() > 0, name


def test_a_sound_with_only_a_file_still_plays(game, tmp_path, monkeypatch):
    """New effects arrive as a file with no synth ever written for them. Looking
    the name up in SYNTHS first is what made the delivered sword swing silent."""
    monkeypatch.setattr(audio, "SFX_DIR", str(tmp_path))
    game.audio._sfx.clear()
    assert game.audio._get_sfx("no_such_sound") is None, "and that is not fatal"
    game.audio.play("no_such_sound")            # must not raise
    import shutil
    real = os.path.join(audio.ASSETS, "sfx", "sword_swing.ogg")
    if os.path.exists(real):
        shutil.copy(real, tmp_path / "file_only.ogg")
        game.audio._sfx.clear()
        snd = game.audio._get_sfx("file_only")
        assert snd is not None and snd.get_length() > 0


def test_the_book_chime_is_shorter_than_the_victory_fanfare():
    """They mark different moments; if they blur, the payoff stops landing."""
    rate = 2 * audio.SR
    assert len(audio._synth_success()) / rate < len(audio._synth_fanfare()) / rate


def test_playing_an_unregistered_sound_is_ignored_not_fatal(game):
    game.audio.play("no_such_sound")


def test_muting_silences_playback(game):
    assert game.audio.toggle() is False
    game.audio.play("zina_bark")
    assert game.audio.toggle() is True


def test_sound_names_used_in_code_are_all_registered():
    """Catches a `play("typo")` that would otherwise just go quiet."""
    import re
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    used = set()
    for path in (root / "game").rglob("*.py"):
        used |= set(re.findall(r'audio\.play\(\s*"([a-z_]+)"', path.read_text()))
        used |= set(re.findall(r'sound_request\s*=\s*"([a-z_]+)"', path.read_text()))
        used |= set(re.findall(r'or\s+"([a-z_]+)"\s*$', path.read_text(), re.M))
    unknown = {n for n in used if n.startswith("zina_") or n in ("monster", "success")}
    assert unknown <= set(audio.SYNTHS), f"unregistered: {unknown - set(audio.SYNTHS)}"


def test_enter_works_wherever_the_screen_says_it_does(game, surface):
    """⚠️ Every end screen prints "Enter: play again" and only Space worked."""
    from game.core.input import InputState
    from game.core.victory_state import VictoryState
    from game.core.play_state import PlayState
    assert "confirm" in InputState.EDGE_FIELDS, "an un-latched edge gets dropped"
    v = VictoryState(game, 12.0)
    game.push(v)
    v.name = "Someone"
    v._submit_name()
    inp = InputState()
    inp.confirm = True
    v.update(settings.FIXED_DT, inp)
    assert isinstance(game.state_stack[-1], PlayState), "Enter did nothing"


def test_the_victory_panel_leaves_the_banner_visible(game):
    """It sat over the middle of the one painted asset on the screen.

    ⚠️ The *name-entry* panel is the one that has to sit low — it holds four
    short lines and the banner is what the player is looking at. The board panel
    is taller by necessity and is allowed to cover more."""
    from game.core.victory_state import VictoryState, SCRIM_NAME, SCRIM_BOARD
    v = VictoryState(game, 12.0)
    game.push(v)
    assert v.phase == "name" and v.scrim is SCRIM_NAME
    assert SCRIM_NAME.top > v.banner.get_height() * 0.45, "the panel covers VICTORY!"
    for box in (SCRIM_NAME, SCRIM_BOARD):
        assert box.bottom <= settings.INTERNAL_RES[1]
