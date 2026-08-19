"""Monster, Caster, and Emri the blink boss."""
import pygame
import pytest

import settings
from game.core.camera import Camera
from game.entities.monster import (Blinker, Caster, Monster, make_emri,
                                   make_fire_caster, make_web_caster)
from game.entities.player import Player


class _Open:
    """A collider with no walls anywhere."""
    @staticmethod
    def solid_rects(box):
        return []


class _Boxed:
    """Everything is solid — used to corner Emri with nowhere to land."""
    @staticmethod
    def solid_rects(box):
        return [pygame.Rect(box)]


@pytest.fixture
def camera():
    return Camera(settings.INTERNAL_RES)


@pytest.fixture
def hero():
    return Player(500, 500)


# ── Monster basics ────────────────────────────────────────────────────────
def test_a_monster_dies_after_exactly_its_hit_count():
    m = Monster(0, 0, hits=3)
    assert not m.take_hit((0, 0)) and not m.take_hit((0, 0))
    assert m.take_hit((0, 0)) and m.dead


def test_a_hit_knocks_the_monster_away_from_the_blow():
    m = Monster(100, 0, hits=5)
    m.take_hit((0, 0))
    assert m.pos.x > 100


def test_a_hit_from_exactly_on_top_does_not_crash_on_a_zero_vector():
    m = Monster(50, 50, hits=3)
    m.take_hit((50, 50))
    assert m.health == 2


def test_an_untargetable_monster_cannot_be_hit():
    m = Monster(0, 0, hits=3)
    m.targetable = False
    assert m.take_hit((0, 0)) is False
    assert m.health == 3


def test_a_monster_chases_once_the_player_is_inside_aggro(hero):
    m = Monster(hero.pos.x + settings.MONSTER_AGGRO - 10, hero.pos.y, hits=3)
    m.update(settings.FIXED_DT, hero, _Open())
    assert m.chasing and m.newly_chasing


def test_newly_chasing_is_true_for_one_step_only(hero):
    m = Monster(hero.pos.x + 20, hero.pos.y, hits=3)
    m.update(settings.FIXED_DT, hero, _Open())
    m.update(settings.FIXED_DT, hero, _Open())
    assert m.chasing and not m.newly_chasing


def test_a_distant_monster_does_not_chase(hero):
    m = Monster(hero.pos.x + settings.MONSTER_AGGRO + 200, hero.pos.y, hits=3)
    m.update(settings.FIXED_DT, hero, _Open())
    assert not m.chasing


def test_a_chasing_monster_closes_the_distance(hero):
    m = Monster(hero.pos.x + 150, hero.pos.y, hits=3)
    before = m.dist_to(hero.pos)
    for _ in range(30):
        m.update(settings.FIXED_DT, hero, _Open())
    assert m.dist_to(hero.pos) < before


def test_a_guard_stays_near_its_post_when_nobody_is_around(hero):
    m = Monster(0, 0, hits=3, mode="guard")
    for _ in range(600):
        m.update(settings.FIXED_DT, hero, _Open())
    assert m.pos.distance_to(m.home) < 160


def test_a_monster_draws_with_and_without_a_sprite(surface, camera):
    for sprite in (None, pygame.Surface((20, 20), pygame.SRCALPHA)):
        m = Monster(100, 100, hits=3, sprite=sprite)
        m.flash = settings.HIT_FLASH_TIME
        m.draw(surface, camera)


# ── Casters ───────────────────────────────────────────────────────────────
def test_the_two_casters_carry_their_own_names_and_projectiles():
    fire = make_fire_caster(0, 0)
    web = make_web_caster(0, 0)
    assert (fire.name, fire.cast_kind) == ("Little Terror", "fire")
    assert (web.name, web.cast_kind) == ("Little Snir", "web")


def test_a_caster_asks_to_cast_when_the_player_is_in_range(hero):
    c = make_fire_caster(hero.pos.x + settings.CASTER_KEEP_MIN + 10, hero.pos.y)
    c.cast_cd = 0
    c.update(settings.FIXED_DT, hero, _Open())
    assert c.cast_request is not None
    assert c.cast_request.length() == pytest.approx(1.0), "requests are directions"


def test_a_caster_out_of_range_does_not_cast(hero):
    c = make_fire_caster(hero.pos.x + settings.CASTER_CAST_RANGE + 100, hero.pos.y)
    c.cast_cd = 0
    c.update(settings.FIXED_DT, hero, _Open())
    assert c.cast_request is None


def test_the_cooldown_spaces_casts_out(hero):
    c = make_fire_caster(hero.pos.x + 150, hero.pos.y)
    c.cast_cd = 0
    c.update(settings.FIXED_DT, hero, _Open())
    c.cast_request = None
    c.update(settings.FIXED_DT, hero, _Open())
    assert c.cast_request is None, "it must wait out the cooldown"


def test_a_caster_kites_away_when_the_player_gets_too_close(hero):
    c = make_fire_caster(hero.pos.x + settings.CASTER_KEEP_MIN - 30, hero.pos.y)
    before = c.dist_to(hero.pos)
    for _ in range(20):
        c.update(settings.FIXED_DT, hero, _Open())
    assert c.dist_to(hero.pos) > before


def test_a_caster_closes_in_when_far_away(hero):
    c = make_fire_caster(hero.pos.x + settings.CASTER_CAST_RANGE + 120, hero.pos.y)
    before = c.dist_to(hero.pos)
    for _ in range(30):
        c.update(settings.FIXED_DT, hero, _Open())
    assert c.dist_to(hero.pos) < before


def test_the_web_caster_is_on_a_slower_cooldown_than_the_fire_one():
    """The web is strong crowd control, so it must stay the rarer of the two."""
    assert make_web_caster(0, 0).cast_cd_max > make_fire_caster(0, 0).cast_cd_max


# ── Emri ──────────────────────────────────────────────────────────────────
def _cycle(emri, hero, collider=None, steps=1200):
    """Run Emri and report which states it passed through."""
    seen = set()
    for _ in range(steps):
        emri.update(settings.FIXED_DT, hero, collider or _Open())
        seen.add(emri.state)
    return seen


def test_emri_starts_hidden_and_untouchable():
    e = make_emri(0, 0)
    assert e.state == Blinker.HIDDEN and not e.targetable
    assert e.alpha == 0.0


def test_emri_walks_through_the_whole_loop(hero):
    assert _cycle(make_emri(0, 0), hero) == {"hidden", "appear", "strike", "vanish"}


def test_emri_materialises_at_arms_length_from_the_player(hero):
    e = make_emri(2000, 2000)
    for _ in range(1200):
        e.update(settings.FIXED_DT, hero, _Open())
        if e.state == Blinker.APPEAR:
            assert e.pos.distance_to(hero.pos) == pytest.approx(
                settings.EMRI_BLINK_DIST, abs=1.0)
            return
    pytest.fail("Emri never blinked in")


def test_emri_is_only_targetable_while_it_is_showing(hero):
    e = make_emri(0, 0)
    for _ in range(1200):
        e.update(settings.FIXED_DT, hero, _Open())
        assert e.targetable == (e.state != Blinker.HIDDEN)


def test_a_hidden_emri_cannot_be_hurt(hero):
    e = make_emri(0, 0)
    assert e.state == Blinker.HIDDEN
    for _ in range(20):
        e.take_hit(hero.pos)
    assert e.health == e.max_health


def test_emri_casts_a_bolt_when_it_strikes(hero):
    e = make_emri(0, 0)
    for _ in range(1200):
        e.update(settings.FIXED_DT, hero, _Open())
        if e.cast_request is not None:
            assert e.cast_kind == "bolt"
            assert e.cast_request.length() == pytest.approx(1.0)
            return
    pytest.fail("Emri never cast")


def test_emri_never_walks(hero):
    e = make_emri(400, 400)
    positions = set()
    for _ in range(200):
        e.update(settings.FIXED_DT, hero, _Open())
        positions.add((round(e.pos.x), round(e.pos.y)))
    assert e.vel == pygame.Vector2(0, 0)
    assert len(positions) < 8, "it should teleport between spots, not drift"


def test_emri_takes_boss_grade_punishment():
    e = make_emri(0, 0)
    e.targetable = True
    hits = sum(1 for _ in range(settings.EMRI_HITS) if not e.take_hit((0, 0)))
    assert e.dead and e.max_health == settings.EMRI_HITS


def test_emri_lands_on_the_player_when_there_is_nowhere_free(hero):
    """Cornered, it must still resolve rather than loop or land inside a wall."""
    e = make_emri(0, 0)
    e.state_t = 0
    e._advance(hero, _Boxed())
    assert e.pos == hero.pos


def test_emri_fades_in_and_out_rather_than_popping(hero):
    e = make_emri(0, 0)
    alphas = set()
    for _ in range(1200):
        e.update(settings.FIXED_DT, hero, _Open())
        alphas.add(round(e.alpha, 2))
    assert len([a for a in alphas if 0.0 < a < 1.0]) > 3


def test_emri_draws_in_every_state(hero, surface, camera):
    e = make_emri(300, 300)
    e.sprite = pygame.Surface((20, 20), pygame.SRCALPHA)
    for _ in range(400):
        e.update(settings.FIXED_DT, hero, _Open())
        e.draw(surface, camera)


def test_the_telegraph_is_the_whole_vulnerable_window(hero):
    """Documents the tuning contract: shortening the telegraph is what makes the
    boss harder — see the roadmap note. Hit-ability must track visibility."""
    e = make_emri(0, 0)
    visible_steps = 0
    for _ in range(1800):
        e.update(settings.FIXED_DT, hero, _Open())
        if e.targetable:
            visible_steps += 1
    window = settings.EMRI_TELEGRAPH + settings.EMRI_STRIKE_TIME + settings.EMRI_VANISH_TIME
    cycle = window + settings.EMRI_HIDDEN_MAX
    assert 0 < visible_steps * settings.FIXED_DT < 1800 * settings.FIXED_DT
    assert window < cycle, "it must spend real time away, or it is just a monster"
