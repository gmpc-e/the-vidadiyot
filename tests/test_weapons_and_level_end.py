"""Thrown knives, per-warrior damage, and the level-complete sequence."""
import pygame
import pytest

import settings
from game.core.camera import Camera
from game.core.input import InputState
from game.core.level_complete_state import LevelCompleteState
from game.entities import warriors
from game.entities.knife import Knife
from game.entities.monster import Monster
from game.entities.player import Player
from game.systems import audio


def _press(**edges):
    i = InputState()
    for k, v in edges.items():
        setattr(i, k, v)
    return i


@pytest.fixture
def camera():
    return Camera(settings.INTERNAL_RES)


# ── the Knife projectile ──────────────────────────────────────────────────
def test_a_knife_flies_along_its_aim():
    k = Knife(0, 0, (1, 0), 1)
    k.update(0.1)
    assert k.pos.x > 0 and k.pos.y == 0


def test_a_knife_drops_out_of_the_air_at_the_end_of_its_range():
    k = Knife(0, 0, (1, 0), 1)
    while not k.dead:
        k.update(settings.FIXED_DT)
    assert k.travelled >= settings.KNIFE_RANGE


def test_a_knife_damages_a_monster_and_is_spent_on_the_hit():
    m = Monster(0, 0, hits=3)
    k = Knife(0, 0, (1, 0), 0.85)
    assert k.on_hit(m) is False
    assert m.health == pytest.approx(2.15) and k.dead, "one blade, one hit"


def test_a_knife_reports_the_kill_it_lands():
    m = Monster(0, 0, hits=1)
    assert Knife(0, 0, (1, 0), 1).on_hit(m) is True


def test_a_knife_with_no_aim_still_flies():
    k = Knife(0, 0, (0, 0), 1)
    assert k.vel.length() == pytest.approx(settings.KNIFE_SPEED)


def test_a_knife_draws_with_and_without_its_sprite(surface, camera):
    for sprite in (None, pygame.Surface((20, 6), pygame.SRCALPHA)):
        k = Knife(100, 100, (1, -1), 1, sprite=sprite)
        for _ in range(6):
            k.update(settings.FIXED_DT)
        k.draw(surface, camera)


# ── who carries what ──────────────────────────────────────────────────────
def test_only_the_thrower_reports_throwing():
    assert Player(0, 0, warriors.get("roni")).throws
    assert not Player(0, 0, warriors.get("elad")).throws


@pytest.mark.parametrize("wid", [w["id"] for w in warriors.WARRIORS])
def test_every_weapon_is_paced(wid):
    """An unpaced weapon is worth whatever the player's mashing speed happens to
    be. Melee had no cooldown, which made the knight 2x-to-20x the princess
    depending only on how fast the key was hit."""
    p = Player(0, 0, warriors.get(wid))
    assert p.can_attack()
    p.start_swing()
    assert not p.can_attack(), f"{wid} can attack again immediately"


@pytest.mark.parametrize("wid", [w["id"] for w in warriors.WARRIORS])
def test_the_cooldown_expires(wid, inp):
    p = Player(0, 0, warriors.get(wid))
    p.start_swing()
    for _ in range(int(p.cooldown / settings.FIXED_DT) + 2):
        p.update(settings.FIXED_DT, inp)
    assert p.can_attack()


def test_mashing_cannot_beat_a_warriors_own_cadence(make_play, step, surface):
    """Holding the key must give the same throughput as pressing it perfectly —
    otherwise the better masher wins, not the better choice."""
    rates = {}
    for wid in ("elad", "roni"):
        p = make_play(wid, clear_monsters=True)
        target = Monster(p.player.pos.x + 30, p.player.pos.y, hits=400)
        target.update = lambda dt, pl, c: None
        home = pygame.Vector2(target.pos)
        p.monsters = [target]
        p.player.facing = 1
        seconds = 3.0
        for _ in range(int(seconds / settings.FIXED_DT)):
            target.pos.update(home)               # pin out knockback
            step(p, 1, inp=_press(attack=True), surface=surface)
        rates[wid] = (400 - target.health) / seconds
    for wid, dps in rates.items():
        cap = warriors.get(wid)["damage"] / warriors.get(wid)["cooldown"]
        assert dps <= cap + 0.5, f"{wid} exceeded its own cadence: {dps:.2f} > {cap:.2f}"


# ── in play ───────────────────────────────────────────────────────────────
def test_the_knight_takes_two_pips_a_swing(make_play, step):
    p = make_play("elad", clear_monsters=True)
    m = Monster(p.player.pos.x + 20, p.player.pos.y, hits=5)
    p.monsters = [m]
    step(p, 1, inp=_press(attack=True))
    assert m.health == 3, "ATK 32 should land two pips"


def test_a_swing_that_kills_mid_way_does_not_keep_hitting(make_play, step):
    """Two pips against a one-pip monster must not run past its death."""
    p = make_play("elad", clear_monsters=True)
    m = Monster(p.player.pos.x + 20, p.player.pos.y, hits=1)
    p.monsters = [m]
    step(p, 1, inp=_press(attack=True))
    assert m.dead and p.monsters == []


def test_roni_throws_instead_of_swinging(make_play, step):
    p = make_play("roni", clear_monsters=True)
    p.monsters = [Monster(p.player.pos.x + 120, p.player.pos.y, hits=5)]
    step(p, 1, inp=_press(attack=True))
    assert len(p.player_shots) == 1
    assert p.monsters[0].health == 5, "the blade has to travel first"


def test_a_thrown_knife_reaches_and_wounds_a_distant_monster(make_play, step, surface):
    p = make_play("roni", clear_monsters=True)
    m = Monster(p.player.pos.x + 130, p.player.pos.y, hits=5)
    p.monsters = [m]
    step(p, 1, inp=_press(attack=True))
    step(p, 90, surface=surface, until=lambda: m.health < 5)
    assert m.health == pytest.approx(5 - warriors.get("roni")["damage"])


def test_throwing_is_unlimited(make_play, step, surface):
    p = make_play("roni", clear_monsters=True)
    p.monsters = [Monster(p.player.pos.x + 200, p.player.pos.y, hits=99)]
    thrown = 0
    seconds = 3.0
    for _ in range(int(seconds / settings.FIXED_DT)):
        if p.player.can_attack():
            step(p, 1, inp=_press(attack=True), surface=surface)
            thrown += 1
        else:
            step(p, 1, surface=surface)
    expected = seconds / settings.KNIFE_COOLDOWN
    assert thrown >= expected - 1, f"{thrown} throws in {seconds}s"
    assert p.player.power_charges == settings.ZINA_CHARGES, "throwing is not a charge"


def test_a_knife_stops_at_a_wall(make_play, step, surface):
    p = make_play("roni", clear_monsters=True)
    wall = next(iter(p.tilemap.solid))
    p.player.pos.update(wall[0] * p.tilemap.tw - 30, wall[1] * p.tilemap.th + 16)
    p.player.facing = 1
    step(p, 1, inp=_press(attack=True))
    step(p, 60, surface=surface, until=lambda: not p.player_shots)
    assert p.player_shots == []


def test_a_knife_cannot_hit_a_hidden_emri(make_play, step, surface):
    p = make_play("roni", clear_monsters=True)
    p.wake_emri()
    emri = p.emri
    emri.pos.update(p.player.pos.x + 60, p.player.pos.y)
    for _ in range(300):
        if emri.state == emri.HIDDEN:
            break
        step(p, 1, surface=surface)
    emri.pos.update(p.player.pos.x + 60, p.player.pos.y)
    before = emri.health
    step(p, 1, inp=_press(attack=True))
    step(p, 40, surface=surface)
    assert emri.health == before, "it is not in the world to be hit"


def test_the_hint_names_the_right_verb_for_each_warrior(make_play):
    for wid, verb in (("elad", "Attack"), ("roni", "Throw at")):
        p = make_play(wid, clear_monsters=True)
        p.monsters = [Monster(p.player.pos.x + 20, p.player.pos.y, hits=3)]
        assert verb in p._compute_hint()


# ── level complete ────────────────────────────────────────────────────────
def test_finishing_the_level_opens_the_celebration(play, step):
    play.monsters.clear()
    for rid, room in play.classrooms.items():
        play.inventory.add("book", room["color"])
        play.player.pos.update(room["rect"].center)
        step(play, 1, inp=_press(interact=True))
        if play.won:
            break
    assert isinstance(play.game.state_stack[-1], LevelCompleteState)


def test_the_two_banners_arrive_in_order(game, surface):
    lc = LevelCompleteState(game, 42.0)
    game.push(lc)
    from game.core import level_complete_state as L
    assert L.NAME_AT < L.DONE_AT, "the level name lands first"
    assert L.DONE_AT - L.NAME_AT >= 0.8, "it needs a beat to register"
    for _ in range(200):
        lc.update(settings.FIXED_DT, InputState())
        lc.draw(surface)


def test_the_sting_plays_once_on_the_second_beat(game, surface):
    played = []
    game.audio.play = lambda name, volume=1.0: played.append(name)
    lc = LevelCompleteState(game, 42.0)
    game.push(lc)
    from game.core import level_complete_state as L
    for _ in range(int(L.DONE_AT / settings.FIXED_DT) - 2):
        lc.update(settings.FIXED_DT, InputState())
    assert played == [], "it must wait for COMPLETED"
    for _ in range(200):
        lc.update(settings.FIXED_DT, InputState())
    assert played == ["level_done"], "exactly one sting"


def test_the_celebration_cannot_be_skipped_by_the_keypress_that_won_it(game, surface):
    """The last book is returned with E; that same press must not blow straight
    through the banners the player has not seen yet."""
    from game.core import level_complete_state as L
    lc = LevelCompleteState(game, 42.0)
    game.push(lc)
    lc.update(settings.FIXED_DT, _press(interact=True))
    assert isinstance(game.state_stack[-1], LevelCompleteState)
    lc.t = L.CAN_SKIP_AT
    lc.update(settings.FIXED_DT, _press(interact=True))
    from game.core.victory_state import VictoryState
    assert isinstance(game.state_stack[-1], VictoryState)


def test_the_level_done_sting_is_registered_and_distinct():
    assert "level_done" in audio.SYNTHS
    rate = 2 * audio.SR
    sting = len(audio._synth_level_done()) / rate
    assert 1.0 < sting < 3.0, f"{sting:.2f}s"
    assert sting != len(audio._synth_fanfare()) / rate
