"""The warrior roster and Roni's Zina power."""
import pygame
import pytest

import settings
from game.core.camera import Camera
from game.core.input import InputState
from game.entities import warriors
from game.entities.monster import Monster
from game.entities.player import Player
from game.entities.zina import Zina


@pytest.fixture
def camera():
    return Camera(settings.INTERNAL_RES)


# ── the roster as data ────────────────────────────────────────────────────
REQUIRED = {"id", "name", "title", "blurb", "sprites", "portrait", "card",
            "speed", "max_health", "reach", "weapon", "damage", "power",
            "power_name", "power_help"}


@pytest.mark.parametrize("w", warriors.WARRIORS, ids=lambda w: w["id"])
def test_every_warrior_is_fully_specified(w):
    assert REQUIRED <= set(w), f"missing {REQUIRED - set(w)}"
    assert set(w["card"]) == {"HP", "ATK", "DEF", "SPD"}
    assert w["speed"] > 0 and w["max_health"] > 0 and w["reach"] > 0
    assert isinstance(w["blurb"], list) and w["blurb"]


@pytest.mark.parametrize("w", warriors.WARRIORS, ids=lambda w: w["id"])
def test_every_warrior_has_the_art_it_claims(w):
    """Catches a roster entry added before its sprites were extracted."""
    import os
    from game.core.assets import ASSETS
    for state in ("idle", "walk", "attack", "hurt"):
        path = os.path.join(ASSETS, "sprites", f"{w['sprites']}_{state}.png")
        assert os.path.exists(path), path
    assert os.path.exists(os.path.join(ASSETS, "sprites", f"{w['portrait']}.png"))


def test_warrior_ids_are_unique():
    ids = [w["id"] for w in warriors.WARRIORS]
    assert len(ids) == len(set(ids))


def test_the_default_warrior_exists():
    assert warriors.DEFAULT_ID in warriors.BY_ID


def test_an_unknown_id_falls_back_to_the_default():
    assert warriors.get("nobody")["id"] == warriors.DEFAULT_ID


def test_the_card_and_the_real_numbers_agree_in_spirit():
    """The cards are flavour and the play stats are real, so they can drift.

    They must at least rank the warriors the same way, or the select screen
    tells the player the opposite of what they will feel.
    """
    by_card = sorted(warriors.WARRIORS, key=lambda w: w["card"]["SPD"])
    by_real = sorted(warriors.WARRIORS, key=lambda w: w["speed"])
    assert [w["id"] for w in by_card] == [w["id"] for w in by_real]


def test_the_knight_trades_speed_and_range_for_power_and_health():
    wallad, roni = warriors.get("wallad"), warriors.get("roni")
    assert wallad["damage"] > roni["damage"], "the sword must hit harder"
    assert wallad["max_health"] > roni["max_health"]
    assert roni["speed"] > wallad["speed"]
    assert roni["reach"] > wallad["reach"], "she fights at range"


@pytest.mark.parametrize("w", warriors.WARRIORS, ids=lambda w: w["id"])
def test_every_warrior_declares_a_weapon_that_deals_damage(w):
    assert w["weapon"] in ("melee", "knife")
    assert w["damage"] > 0


def test_only_roni_carries_a_power():
    assert warriors.get("roni")["power"] == "zina"
    assert warriors.get("wallad")["power"] is None


# ── Zina ──────────────────────────────────────────────────────────────────
@pytest.fixture
def pair():
    owner = Player(100, 100, warriors.get("roni"))
    target = Monster(220, 100, hits=3)
    return owner, target


def _run(z, limit=2000):
    steps = 0
    while not z.done and steps < limit:
        z.update(settings.FIXED_DT)
        steps += 1
    return steps


def test_zina_runs_out_bites_and_comes_home(pair):
    owner, target = pair
    z = Zina(owner, target)
    steps = _run(z)
    assert z.done and z.killed is target
    assert z.pos.distance_to(owner.pos) <= 20
    assert steps < 2000, "she must actually return, not orbit forever"


def test_the_round_trip_is_slow_enough_to_watch(pair):
    owner, target = pair
    seconds = _run(Zina(owner, target)) * settings.FIXED_DT
    assert 0.8 < seconds < 6.0, f"trip took {seconds:.2f}s"


def test_she_barks_on_the_way_out_and_back_but_not_mid_bite(pair):
    owner, target = pair
    z = Zina(owner, target)
    barks, bites, bark_while_biting = 0, 0, 0
    for _ in range(2000):
        if z.done:
            break
        z.update(settings.FIXED_DT)
        if z.sound_request == "zina_bark":
            barks += 1
            if z.state == Zina.BITE:
                bark_while_biting += 1
        elif z.sound_request == "zina_bite":
            bites += 1
        z.sound_request = None
    # Was ">= 2 barks", written when the bark was a synthesized 0.3s yap that
    # wanted repeating. The delivered sound is 1.85s of *sequence*, so one play
    # covers her whole run-in and retriggering it stacked copies of itself.
    assert barks >= 1, "she should announce herself"
    assert bites == 1, "exactly one bite sound per trip"
    assert bark_while_biting == 0, "no barking with her mouth full"


def test_the_bite_sound_fires_on_the_frame_she_latches_on(pair):
    owner, target = pair
    z = Zina(owner, target)
    for _ in range(2000):
        z.update(settings.FIXED_DT)
        if z.state == Zina.BITE:
            assert z.killed is target
            return
    pytest.fail("she never bit")


def test_she_chases_a_target_that_keeps_moving(pair):
    owner, target = pair
    z = Zina(owner, target)
    for _ in range(2000):
        if z.state != Zina.OUT:
            break
        target.pos.x += 1.2                     # the monster flees
        z.update(settings.FIXED_DT)
    assert z.state in (Zina.BITE, Zina.BACK), "she must run it down, not miss"


def test_she_comes_straight_home_if_the_target_dies_first(pair):
    owner, target = pair
    z = Zina(owner, target)
    z.update(settings.FIXED_DT)
    target.dead = True
    _run(z)
    assert z.done and z.killed is None, "nothing was bitten, so nothing was killed"


def test_she_rides_the_monster_while_latched_on(pair):
    owner, target = pair
    z = Zina(owner, target)
    for _ in range(2000):
        z.update(settings.FIXED_DT)
        if z.state == Zina.BITE:
            target.pos.x += 40
            z.update(settings.FIXED_DT)
            assert z.pos.distance_to(target.pos) < 1
            return
    pytest.fail("she never bit")


def test_zina_draws_in_every_state(pair, surface, camera):
    owner, target = pair
    z = Zina(owner, target, sprite=pygame.Surface((12, 10), pygame.SRCALPHA))
    for _ in range(400):
        if z.done:
            break
        z.update(settings.FIXED_DT)
        z.draw(surface, camera)


def test_zina_draws_without_a_sprite(pair, surface, camera):
    owner, target = pair
    Zina(owner, target).draw(surface, camera)


def test_a_zina_kill_leaves_a_splash_that_fades(make_play, surface, step):
    """§19. It is one sprite and a timer — the general effects pool that used to
    exist was deleted with the burst it served, and this is one caller again."""
    play = make_play("roni")
    victim = play.monsters[0]
    play.player.pos.update(victim.pos.x - 30, victim.pos.y)
    play.player.power_charges = 1
    play._use_power()
    for _ in range(240):
        play.update(settings.FIXED_DT, InputState())
        if play.splashes:
            break
    assert play.splashes, "no splash where the bite landed"
    where = play.splashes[0].pos
    assert where.distance_to(victim.pos) < 40
    step(play, 60, surface=surface)
    assert play.splashes == [], "it never faded"


def test_the_drawn_bite_star_is_only_a_fallback(make_play, surface):
    """⚠️ It drew on every bite, and once the painted splash landed it was a
    white spoked star over a red burst — which reads as a glitch, not a kill."""
    play = make_play("roni")
    assert play.bite_sprite is not None, "the art is installed"
    play.player.power_charges = 1
    play._use_power()
    assert play.zina.painted_bite, "the drawn star is still switched on"
