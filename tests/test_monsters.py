"""Monster, Caster, and Emri the blink boss."""
import random

import pygame
import pytest

import settings
from game.core.camera import Camera
from game.entities.monster import (Blinker, Caster, Monster, Teacher, make_emri,
                                   make_fire_caster, make_teacher,
                                   make_web_caster)
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


class _OneWall:
    """A collider with a single solid tile, for shoving a monster into it."""
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def solid_rects(self, box):
        return [self.rect] if pygame.Rect(box).colliderect(self.rect) else []


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


def test_a_hit_records_a_shove_away_from_the_blow():
    """The shove is recorded, not applied: `take_hit` has no collider, and an
    unresolved 26px teleport is how a struck monster ended up in the next room."""
    m = Monster(100, 0, hits=5)
    m.take_hit((0, 0))
    assert m.knockback.x > 0
    assert m.pos.x == 100, "nothing moves until update() can resolve it"


def test_a_shove_cannot_push_a_monster_through_a_wall(monkeypatch):
    """The reported bug: hit a monster in classroom A, it appears in classroom B.

    Knockback is 26px against 32px tiles, so an unresolved shove cleared most of
    a wall in one blow.
    """
    wall = pygame.Rect(140, -80, 32, 240)
    m = Monster(100, 0, hits=5)
    monkeypatch.setattr(settings, "MONSTER_SPEED", 0)   # isolate the shove
    m.speed = 0
    m.take_hit((0, 0))                                  # shoved toward the wall
    m.update(settings.FIXED_DT, Player(-400, 0), _OneWall(wall))
    assert not m.hitbox.colliderect(wall), "the shove went through the wall"
    assert m.pos.x > 100, "but it still moved"


def test_a_thrown_weapon_shoves_along_its_own_heading():
    """A knife lands *inside* its target, so "away from the blow" is rounding
    error — which made the monster hop somewhere random on every knife hit."""
    m = Monster(100, 100, hits=5)
    m.take_hit((100.4, 100.2), 0.85, direction=(1, 0))
    assert m.knockback.x > 0 and m.knockback.y == 0


def test_a_blow_landing_dead_centre_does_not_shove_at_random():
    m = Monster(100, 100, hits=5)
    m.take_hit((100.4, 100.2), 0.85)
    assert m.knockback.length() == 0, "a direction from noise is worse than none"


def test_a_hit_from_exactly_on_top_does_not_crash_on_a_zero_vector():
    m = Monster(50, 50, hits=3)
    m.take_hit((50, 50))
    assert m.health == 2
    assert m.knockback.length() == 0


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


def _wind_and_cast(c, hero, steps=200):
    """Run a caster until it actually throws, through its wind-up."""
    for _ in range(steps):
        c.update(settings.FIXED_DT, hero, _Open())
        if c.cast_request is not None:
            return True
    return False


def test_a_caster_asks_to_cast_when_the_player_is_in_range(hero):
    c = make_fire_caster(hero.pos.x + settings.CASTER_KEEP_MIN + 10, hero.pos.y)
    c.cast_cd = 0
    assert _wind_and_cast(c, hero), "it never threw"
    assert c.cast_request.length() == pytest.approx(1.0), "requests are directions"


# ── the wind-up (the tell that makes a ranged fight fair) ─────────────────
def test_a_caster_charges_before_it_throws_rather_than_firing_instantly(hero):
    """⚠️ It used to fire on the frame its cooldown expired: the shot simply
    existed, and being hit was a question of where you happened to be standing."""
    c = make_fire_caster(hero.pos.x + settings.CASTER_KEEP_MIN + 10, hero.pos.y)
    c.cast_cd = 0
    c.update(settings.FIXED_DT, hero, _Open())
    assert c.cast_request is None, "it threw with no warning at all"
    assert c.winding > 0 and c.cast_started, "no charge started either"
    assert 0.0 <= c.charge < 0.2, "the charge should start at the beginning"


def test_a_charging_caster_stops_moving(hero):
    """Standing still is the readable half of the tell."""
    c = make_fire_caster(hero.pos.x + settings.CASTER_KEEP_MIN + 20, hero.pos.y)
    c.cast_cd = 0
    c.update(settings.FIXED_DT, hero, _Open())
    where = pygame.Vector2(c.pos)
    for _ in range(int(c.wind_up / settings.FIXED_DT) - 2):
        c.update(settings.FIXED_DT, hero, _Open())
    assert c.pos.distance_to(where) < 1.0, "it kept moving while charging"


def test_the_aim_locks_when_the_charge_starts_so_dodging_works(hero):
    """⚠️ Tracking the player through the wind-up would make the tell purely
    decorative — there would be nothing the warning let you do."""
    c = make_fire_caster(hero.pos.x, hero.pos.y - 150)
    c.cast_cd = 0
    c.update(settings.FIXED_DT, hero, _Open())
    aimed = pygame.Vector2(c.wind_aim)
    # sideways, but not so far it leaves aggro — losing sight is a *different*
    # rule, and this test is about the aim, not the cancel
    hero.pos.x += 80
    assert _wind_and_cast(c, hero)
    assert c.cast_request.distance_to(aimed) < 0.01, "it tracked me anyway"


def test_breaking_line_of_sight_cancels_the_charge(hero):
    """A wind-up you can hide from is one worth answering."""
    c = make_fire_caster(hero.pos.x + 100, hero.pos.y)
    c.cast_cd = 0
    c.update(settings.FIXED_DT, hero, _Open())
    assert c.winding > 0
    for _ in range(10):
        c.update(settings.FIXED_DT, hero, _Blind())
    assert c.winding == 0 and c.cast_request is None, "it threw through a wall"


def test_the_charge_reads_zero_to_one_for_whatever_draws_it(hero):
    c = make_fire_caster(hero.pos.x + 100, hero.pos.y)
    assert c.charge is None, "not charging"
    c.cast_cd = 0
    seen = []
    for _ in range(200):
        c.update(settings.FIXED_DT, hero, _Open())
        if c.charge is not None:
            seen.append(c.charge)
        if c.cast_request is not None:
            break
    assert seen and 0 <= min(seen) and max(seen) < 1.0
    assert seen == sorted(seen), "the charge must run forwards"


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


def test_emri_drifts_only_while_it_is_visible(hero):
    """⚠️ It used to be nailed to the floor between blinks, which reads as a prop
    for the 1.3s it stands there telegraphing. It circles now — but only while
    visible, and slowly enough that the telegraph is still a window to swing
    into rather than a chase."""
    # ⚠️ Blink spots are random, and a blink into a corner leaves nowhere to
    # drift. Seeded for the same reason the teacher's wander test is: a
    # behaviour test driven by `random` either pins the seed or asserts on
    # something that cannot vary.
    random.seed(20260821)
    e = make_emri(400, 400)
    hidden_moves = visible_moves = 0
    for _ in range(900):
        before = pygame.Vector2(e.pos)
        e.update(settings.FIXED_DT, hero, _Open())
        moved = before.distance_to(e.pos) > 0.01
        if e.state == e.HIDDEN:
            hidden_moves += moved
        elif e.state in (e.APPEAR, e.STRIKE):
            visible_moves += moved
    assert visible_moves > 20, "it stood perfectly still the whole time it was up"
    assert hidden_moves == 0, "it drifted while it was supposed to be gone"


def test_a_dormant_emri_is_gone_entirely(hero):
    """A phase break is the boss *leaving* — not standing there invulnerable."""
    e = make_emri(400, 400)
    e.dormant = True
    where = pygame.Vector2(e.pos)
    for _ in range(300):
        e.update(settings.FIXED_DT, hero, _Open())
    assert e.state == e.HIDDEN and not e.targetable
    assert e.cast_request is None, "it attacked while it was supposed to be away"
    assert e.pos == where
    e.dormant = False
    for _ in range(600):
        e.update(settings.FIXED_DT, hero, _Open())
        if e.targetable:
            break
    assert e.targetable, "it never came back"


def test_emri_is_bigger_than_an_ordinary_monster():
    """A boss the size of a classroom monster reads as one whatever it does."""
    e = make_emri(0, 0)
    assert e.hitbox.width > settings.MONSTER_SIZE[0]


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


# ── the teachers ─────────────────────────────────────────────────────────--
class _Blind:
    """Sight is blocked everywhere, but nothing obstructs movement.

    `_can_see` walks the line of sight probing with **2x2** rects, while
    `move_and_collide` asks the same collider about the monster's 44x44 hitbox.
    To test "cannot see the player" without also walling the monster in, the two
    have to disagree — so anything tiny enough to be a sight probe hits a wall,
    and anything hitbox-sized passes freely.
    """
    @staticmethod
    def solid_rects(box):
        r = pygame.Rect(box)
        return [pygame.Rect(r)] if max(r.w, r.h) <= 4 else []


def test_a_teacher_wanders_its_room_instead_of_walking_at_the_player(monkeypatch):
    """A `Caster` closes in from any distance, which is right in a corridor and
    wrong in a classroom — it crosses the floor before the player is through the
    door. Out of sight, a teacher patrols its post instead.

    ⚠️ The radius is pinned rather than read from `settings`. The sibling test
    below patches `TEACHER_WANDER` to 0 to hold a teacher still, and at 0 the
    wander target *is* the home position — so `d.length()` is exactly 0, the
    monster never moves, and this test fails with a mystifying `0.0 > 4` if the
    two ever share a value. Pinning it makes the pair order-independent."""
    monkeypatch.setattr(settings, "TEACHER_WANDER", 96)
    # ⚠️ Wandering is random, so this asserts on a *sampled* outcome and was
    # intermittently failing at roughly one run in six. Seeding makes the
    # sequence the same every time: a behaviour test driven by `random` either
    # pins the seed or asserts on something that cannot vary, and this one wants
    # to check real accumulated movement.
    random.seed(20260820)
    hero = Player(900, 900)                     # far away and unseen
    t = make_teacher(300, 300)
    start = pygame.Vector2(t.pos)
    moved_away, drifted = 0.0, 0.0
    for _ in range(600):
        t.update(settings.FIXED_DT, hero, _Open())
        drifted = max(drifted, t.home.distance_to(t.pos))
        moved_away = max(moved_away, start.distance_to(t.pos))
    assert moved_away > 4, "it should not stand perfectly still"
    assert drifted <= settings.TEACHER_WANDER + 40, "it left its classroom"
    assert t.pos.distance_to(hero.pos) > 300, "it beelined at the player"


def test_a_teacher_that_can_see_the_player_fights_like_a_caster():
    hero = Player(420, 300)
    t = make_teacher(300, 300)
    for _ in range(240):
        t.update(settings.FIXED_DT, hero, _Open())
        if t.cast_request is not None:
            break
    assert t.cast_request is not None, "it never threw a book"
    assert t.cast_kind == "tome"
    assert t.chasing


def test_a_teacher_out_of_sight_does_not_re_growl_every_frame(monkeypatch):
    """`newly_chasing` drives the scare sound. Leaving last frame's value in
    place while wandering means a growl per frame.

    Wandering is pinned off so the only thing keeping the player unseen is the
    blocked line of sight. Left free, the teacher eventually drifts within
    `MONSTER_SIGHT_STEP` of the player, at which point the sight walk takes zero
    samples and reports a clear view — true enough at 12px, and flaky here."""
    monkeypatch.setattr(settings, "TEACHER_WANDER", 0)
    hero = Player(400, 300)                     # inside aggro, sight blocked
    t = make_teacher(300, 300)
    t.chasing = True
    t.newly_chasing = True
    for _ in range(30):
        t.update(settings.FIXED_DT, hero, _Blind())
        assert not t.newly_chasing
        assert not t.chasing


def test_a_teacher_is_a_caster_and_draws(hero, surface, camera):
    t = make_teacher(300, 300, female=False)
    assert isinstance(t, (Teacher, Caster))
    assert t.name == "Schoolmaster"
    t.sprite = pygame.Surface((20, 54), pygame.SRCALPHA)
    for _ in range(200):
        t.update(settings.FIXED_DT, hero, _Open())
        t.draw(surface, camera)


def test_a_monster_with_a_walk_pose_alternates_and_one_without_does_not():
    """Monsters use the player's animator now. Most ship one pose and must go on
    behaving exactly as they did — a single sprite, forever."""
    walking = make_teacher(0, 0)
    walking.set_frames(idle=pygame.Surface((8, 20), pygame.SRCALPHA),
                       walk=pygame.Surface((8, 20), pygame.SRCALPHA))
    walking.vel = pygame.Vector2(30, 0)
    assert walking.anim_state == "walk"
    seen = {id(walking.frame_for("walk", t * 0.05)) for t in range(20)}
    assert len(seen) == 2, "the synthesized gait never alternated"

    still = make_fire_caster(0, 0, sprite=pygame.Surface((8, 20), pygame.SRCALPHA))
    still.vel = pygame.Vector2(30, 0)
    assert still.frame_for(still.anim_state, 0.3) is still.sprite


def test_a_monster_with_no_art_at_all_still_draws(surface, camera, hero):
    """`_pose` returns None for missing art and `set_frames` drops it."""
    m = make_teacher(100, 100)
    m.set_frames(idle=None, walk=None)
    m.draw(surface, camera)


def test_a_caster_shoots_at_its_stated_range_not_at_its_aggro_range(hero):
    """⚠️ `MONSTER_AGGRO` is 190 and a fire caster's range is 250. Gating the
    cast on `chasing` — which includes the aggro distance — quietly capped every
    caster at 190 and made `CASTER_CAST_RANGE` a number that did nothing."""
    far = settings.CASTER_CAST_RANGE - 10
    assert far > settings.MONSTER_AGGRO, "this test would prove nothing otherwise"
    c = make_fire_caster(hero.pos.x + far, hero.pos.y)
    c.cast_cd = 0
    assert _wind_and_cast(c, hero), "it never fired from its own stated range"


def test_a_caster_will_not_fire_through_a_wall(hero):
    """The line of sight is the half of the old `chasing` check worth keeping."""
    c = make_fire_caster(hero.pos.x + 120, hero.pos.y)
    c.cast_cd = 0
    for _ in range(200):
        c.update(settings.FIXED_DT, hero, _Blind())
    assert c.cast_request is None and c.winding == 0
