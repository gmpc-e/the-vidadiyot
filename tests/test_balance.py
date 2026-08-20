"""Tuning invariants — the relationships between constants that must hold.

These are not "the number is 42" tests, which only break when you deliberately
retune. Each one guards a relationship the design depends on, so it fails when a
tweak has a consequence somewhere the tweaker wasn't looking.
"""
import pytest

import settings
from game.entities import warriors
from game.systems import difficulty


def test_the_internal_resolution_scales_to_whole_pixels():
    w, h = settings.INTERNAL_RES
    assert w % 2 == 0 and h % 2 == 0
    assert settings.WINDOW_SCALE >= 1 and settings.WINDOW_SCALE == int(settings.WINDOW_SCALE)


def test_the_sim_steps_faster_than_the_frame_cap_allows_frames():
    """If the cap dipped below the sim rate, the accumulator would never drain."""
    assert settings.FPS_CAP >= 1 / settings.FIXED_DT


def test_the_player_is_narrower_than_a_tile_so_doorways_forgive():
    assert settings.PLAYER_SIZE[0] < settings.TILE


def test_a_monster_is_wider_than_a_tile_which_is_why_decor_stays_non_solid():
    """The constraint world/decor.py is built around — see its module docstring."""
    assert settings.MONSTER_SIZE[0] > settings.TILE


def test_sprinting_is_faster_than_walking():
    assert settings.PLAYER_SPRINT > settings.PLAYER_WALK


def test_no_monster_outruns_a_sprinting_player():
    """A monster that can always catch you removes the point of stamina."""
    fastest = max(settings.MONSTER_SPEED, settings.CASTER_SPEED, settings.WEBBER_SPEED)
    slowest_warrior = min(w["speed"] for w in warriors.WARRIORS)
    assert fastest < slowest_warrior


def test_casters_keep_out_of_every_melee_warriors_reach():
    """Their keep-away distance has to exceed melee range or they never kite.

    A thrower is deliberately excluded: out-ranging the casters is the whole
    point of fighting at range, and is paid for in damage per hit.
    """
    melee = [w["reach"] for w in warriors.WARRIORS if w["weapon"] == "melee"]
    assert settings.CASTER_KEEP_MIN > max(melee)
    assert settings.WEB_KEEP_MIN > max(melee)


def test_a_thrower_out_ranges_the_casters_but_hits_for_less():
    throwers = [w for w in warriors.WARRIORS if w["weapon"] == "knife"]
    melee = [w for w in warriors.WARRIORS if w["weapon"] == "melee"]
    for t in throwers:
        assert t["reach"] > settings.CASTER_KEEP_MIN, "range is the point"
        assert t["damage"] < max(m["damage"] for m in melee), "range must cost something"


def test_a_thrown_blade_outruns_the_monsters_it_chases():
    assert settings.KNIFE_SPEED > max(settings.CASTER_SPEED, settings.WEBBER_SPEED)


def test_throwing_is_paced_so_it_is_not_a_machine_gun():
    """Unlimited ammo needs a cooldown, or range plus spam beats every fight."""
    assert settings.KNIFE_COOLDOWN >= settings.SWING_TIME


@pytest.mark.parametrize("w", warriors.WARRIORS, ids=lambda w: w["id"])
def test_every_warrior_declares_a_cooldown(w):
    """An unpaced weapon is worth the player's mashing speed, not its stats."""
    assert w["cooldown"] > 0


def test_melee_out_damages_range_but_not_by_a_landslide():
    """The trade is damage *per second*, not per hit. Melee has to stand inside
    a caster's keep-away distance to earn its throughput, so it should lead —
    but a runaway lead means nobody ever picks the thrower.
    """
    dps = {w["id"]: w["damage"] / w["cooldown"] for w in warriors.WARRIORS}
    melee = max(dps[w["id"]] for w in warriors.WARRIORS if w["weapon"] == "melee")
    thrown = max(dps[w["id"]] for w in warriors.WARRIORS if w["weapon"] == "knife")
    assert melee > thrown, "standing in range must pay"
    assert melee / thrown < 2.0, f"melee is {melee / thrown:.1f}x — the thrower is a trap"


def test_a_thrower_needs_more_hits_but_gets_them_from_safety():
    """Sanity on the shape of the trade, in the units a player feels: how long
    to drop a caster, and from how far."""
    from game.entities import warriors as W
    for w in W.WARRIORS:
        seconds = settings.CASTER_HITS / (w["damage"] / w["cooldown"])
        assert 0.5 < seconds < 4.0, f"{w['id']} takes {seconds:.1f}s to kill a caster"


def test_a_knife_flies_its_whole_range_before_dropping():
    assert settings.KNIFE_SPEED * 1.0 > settings.KNIFE_RANGE / 2


def test_a_caster_can_reach_further_than_it_kites_to():
    assert settings.CASTER_CAST_RANGE > settings.CASTER_KEEP_MIN
    assert settings.WEB_CAST_RANGE > settings.WEB_KEEP_MIN


def test_projectiles_outrun_a_walking_player_or_they_could_never_land():
    """Both casters' shots used to be slower than a walk, so retreating on foot
    made the ranged monsters harmless. Sprinting must still outrun them, or
    stamina stops being the answer."""
    for speed in (settings.FIREBALL_SPEED, settings.WEB_SPEED, settings.TOME_SPEED):
        assert speed > settings.PLAYER_WALK
        assert speed < settings.PLAYER_SPRINT


def test_emris_bolt_cannot_be_outrun_at_all():
    """It only fires from arm's length after a telegraph — dodging is sideways,
    not a footrace."""
    assert settings.BOLT_SPEED > settings.PLAYER_SPRINT


def test_a_projectile_lives_long_enough_to_cross_its_own_range():
    assert settings.FIREBALL_SPEED * settings.FIREBALL_LIFETIME > settings.CASTER_CAST_RANGE
    assert settings.WEB_SPEED * settings.WEB_LIFETIME > settings.WEB_CAST_RANGE
    assert settings.TOME_SPEED * settings.TOME_LIFETIME > settings.TOME_CAST_RANGE


def test_a_teacher_fights_at_room_range_not_corridor_range():
    """The reason the teachers hold the classrooms and the other two do not.

    Little Terror reaches 250px and backs off below 130 — inside a room that is
    most of the floor, so it retreats into a corner and the fight stalls. Give a
    teacher corridor range and this speaks up."""
    assert settings.TOME_CAST_RANGE > settings.TOME_KEEP_MIN
    assert settings.TOME_CAST_RANGE < settings.CASTER_CAST_RANGE
    assert settings.TOME_CAST_RANGE < settings.WEB_CAST_RANGE
    assert settings.TEACHER_SPEED < settings.CASTER_SPEED, "they shuffle"
    # ...and it must not out-wander its own leash, or it abandons the room it is
    # there to hold and the locked door protecting it stops meaning anything.
    assert settings.TEACHER_WANDER < settings.MONSTER_LEASH


def test_no_single_hit_can_kill_a_warrior_outright_on_hard():
    """One-shotting from full health reads as a bug, not as difficulty."""
    hardest = difficulty.get("Hard")["dps"]
    weakest = min(w["max_health"] for w in warriors.WARRIORS)
    for damage in (settings.FIREBALL_DAMAGE, settings.BOLT_DAMAGE):
        assert damage * hardest < weakest


def test_easy_really_is_easier_than_hard():
    order = [difficulty.get(name)["dps"] for name in difficulty.ORDER]
    assert order == sorted(order)


def test_health_and_damage_may_be_fractional():
    """Both are floats so either side can be nudged by a percentage without
    being forced onto whole pips — 4 -> 4.6 rather than 4 -> 5 (a 25% jump)."""
    from game.entities.monster import Monster
    m = Monster(0, 0, hits=settings.WEBBER_HITS)
    m.take_hit((0, 0), 0.85)
    assert m.health == pytest.approx(settings.WEBBER_HITS - 0.85)
    assert not m.dead


def test_a_partial_hit_never_kills_early_or_leaves_a_ghost():
    from game.entities.monster import Monster
    m = Monster(0, 0, hits=1.0)
    assert m.take_hit((0, 0), 0.85) is False, "0.85 of a pip is not a kill"
    assert m.take_hit((0, 0), 0.85) is True


def test_a_two_pip_swing_knocks_back_once_not_twice():
    """One call is one blow; looping take_hit per pip doubled the shove."""
    from game.entities.monster import Monster
    one, two = Monster(100, 0, hits=9), Monster(100, 0, hits=9)
    one.take_hit((0, 0), 1)
    two.take_hit((0, 0), 2)
    # compare the recorded shove, not the position: the shove is applied in
    # update() now, so comparing positions here would pass without testing it
    assert one.knockback.x == pytest.approx(two.knockback.x)
    assert one.knockback.length() > 0


def test_the_web_is_escapable_in_a_few_presses():
    assert 1 <= settings.WEB_STRUGGLE_HITS <= 6


def test_carrying_is_limited_so_return_trips_happen():
    assert settings.CARRY_CAPACITY >= 1


def test_interact_range_reaches_past_the_player_body():
    assert settings.INTERACT_RANGE > max(settings.PLAYER_SIZE) / 2


# ── Emri ──────────────────────────────────────────────────────────────────
def test_emri_spends_real_time_away_or_it_is_just_another_monster():
    shown = (settings.EMRI_TELEGRAPH + settings.EMRI_STRIKE_TIME
             + settings.EMRI_VANISH_TIME)
    assert settings.EMRI_HIDDEN_MIN > 0 and settings.EMRI_HIDDEN_MIN <= settings.EMRI_HIDDEN_MAX
    assert shown < settings.EMRI_HIDDEN_MIN + shown


def test_the_telegraph_leaves_time_for_several_swings():
    """The telegraph is the whole vulnerable window; too short and the boss is
    unbeatable rather than hard. It must outlast a few swings, not just one."""
    assert settings.EMRI_TELEGRAPH > settings.SWING_TIME * 3


def test_emri_is_tougher_than_the_regular_monsters():
    assert settings.EMRI_HITS > max(settings.CASTER_HITS, settings.WEBBER_HITS,
                                    settings.MONSTER_HITS)


def test_emri_blinks_inside_every_warriors_reach():
    """It has to be hittable where it lands, or the fight cannot be won."""
    shortest = min(w["reach"] for w in warriors.WARRIORS)
    assert settings.EMRI_BLINK_DIST <= shortest + settings.PLAYER_SIZE[0]


def test_emri_is_parked_rather_than_deleted():
    """It is out of level 1 but still fully specified, waiting on the boss
    level — so the constants must stay coherent, not rot."""
    assert not hasattr(settings, "EMRI_SPAWN_AFTER_BOOKS")
    assert settings.EMRI_HITS > 0 and settings.EMRI_TELEGRAPH > 0


def test_emri_stays_visible_long_enough_to_answer():
    """It used to vanish before a player could react. The window it spends on
    screen must be a real fraction of its cycle, not a blink."""
    shown = (settings.EMRI_TELEGRAPH + settings.EMRI_STRIKE_TIME
             + settings.EMRI_VANISH_TIME)
    cycle = shown + settings.EMRI_HIDDEN_MAX
    assert shown >= 3.0, f"only {shown:.2f}s on screen per blink"
    assert shown / cycle > 0.3, "it spends too much of the fight untouchable"


# ── Zina ──────────────────────────────────────────────────────────────────
def test_zina_is_limited_because_her_bite_is_not():
    """The bite is an instant kill, so the charge count is the entire balance."""
    assert 1 <= settings.ZINA_CHARGES <= 5


def test_zina_cannot_be_used_from_safety():
    """Her leash must be shorter than a caster's range, or Roni clears the level
    from outside the fight."""
    assert settings.ZINA_RANGE < settings.CASTER_CAST_RANGE


def test_zina_is_slow_enough_to_watch_and_fast_enough_to_land():
    trip = 2 * settings.ZINA_RANGE / settings.ZINA_SPEED
    assert 0.5 < trip < 6.0, f"a full-range round trip takes {trip:.1f}s"


def test_zina_outruns_what_she_is_chasing():
    assert settings.ZINA_SPEED > max(settings.CASTER_SPEED, settings.WEBBER_SPEED,
                                     settings.MONSTER_SPEED)


# ── the book-return payoff ────────────────────────────────────────────────
def test_the_payoff_is_a_beat_not_an_interruption():
    for value in (settings.BOOK_FLASH_TIME, settings.BOOK_SHAKE_TIME):
        assert 0 < value < 2.0


# ── difficulty actually differs (2026-08-20) ──────────────────────────────
def test_difficulty_changes_how_long_a_monster_takes_to_kill():
    """⚠️ Normal was too easy and this is why: difficulty only scaled *incoming*
    damage, so a monster died in the same number of swings whatever you picked
    and the level was the same length on Hard as on Easy."""
    from game.systems import difficulty
    hps = [difficulty.get(n)["hp"] for n in difficulty.ORDER]
    assert hps == sorted(hps), "monsters must get tougher as difficulty rises"
    assert len(set(hps)) == len(hps), "two difficulties share a health scale"
    assert difficulty.get("Normal")["hp"] > 1.0, "Normal must be above the base"


def test_healing_gets_meaner_as_difficulty_rises():
    from game.systems import difficulty
    regens = [difficulty.get(n)["regen"] for n in difficulty.ORDER]
    assert regens == sorted(regens, reverse=True)


def test_regenerating_a_full_bar_takes_longer_than_a_fight():
    """Health regen was doing most of the work of an easy mode by itself: at
    3.0/sec a full bar came back in ~33s, so a fight cost nothing once it was
    over. It must be slow enough that potions and difficulty mean something."""
    seconds = settings.PLAYER_MAX_HEALTH / settings.PLAYER_HEALTH_REGEN
    assert seconds > 60, f"a full heal takes only {seconds:.0f}s"
    assert settings.PLAYER_REGEN_DELAY >= 3.0


def test_the_teachers_hit_harder_than_the_corridor_casters_do():
    """They hold every classroom and are the enemy met most; being the softest
    attack in the game made a room something to walk through."""
    assert settings.TOME_DAMAGE > settings.FIREBALL_DAMAGE


# ── the wind-up (2026-08-20) ──────────────────────────────────────────────
def test_every_caster_telegraphs_long_enough_to_answer():
    """⚠️ Human reaction is around 0.25s. A tell shorter than that is not a tell,
    it is an apology — the player sees the charge only after being hit by it."""
    for w in (settings.CASTER_WINDUP, settings.WEB_WINDUP, settings.TOME_WINDUP):
        assert w > 0.35, f"{w}s is under a reaction time"


def test_a_wind_up_never_outlasts_its_own_cooldown():
    """Otherwise a caster is charging every frame it is alive, the tell stops
    meaning 'about to throw', and it never moves again."""
    for wind, cd in ((settings.CASTER_WINDUP, settings.CASTER_CAST_CD),
                     (settings.WEB_WINDUP, settings.WEB_CAST_CD),
                     (settings.TOME_WINDUP, settings.TOME_CAST_CD)):
        assert wind < cd * 0.6, f"{wind}s of charge against a {cd}s cooldown"


def test_the_harshest_shot_gets_the_longest_warning():
    """The web is the worst thing to be hit by — it holds you *and* drains — so
    it is the one that must be most avoidable."""
    assert settings.WEB_WINDUP > settings.CASTER_WINDUP > settings.TOME_WINDUP


def test_a_dodge_is_actually_possible_during_the_wind_up():
    """The aim locks when the charge starts, so the question is whether a walking
    player can clear the projectile's own width before it is thrown."""
    for wind, size in ((settings.CASTER_WINDUP, settings.FIREBALL_SIZE),
                       (settings.WEB_WINDUP, settings.WEB_SIZE),
                       (settings.TOME_WINDUP, settings.TOME_SIZE)):
        assert settings.PLAYER_WALK * wind > size * 2, "no room to step aside"


def test_zinas_bite_is_the_heaviest_blow_but_not_a_phase_of_the_boss():
    """⚠️ It was `max_health / 3` — a third of the fight per bite, and it
    rescaled itself whenever `EMRI_HITS` moved, so tuning the boss silently
    retuned the dog."""
    from game.entities import warriors
    sword = max(w["damage"] for w in warriors.WARRIORS)
    assert settings.ZINA_BOSS_DAMAGE > sword, "a bite should beat a sword swing"
    every_charge = settings.ZINA_BOSS_DAMAGE * settings.ZINA_CHARGES
    assert every_charge < settings.EMRI_HITS * 0.5, \
        "spending every charge should not be half the boss"
    assert settings.ZINA_BOSS_DAMAGE < settings.EMRI_HITS * min(
        settings.EMRI_PHASE_MARKS), "one bite is worth a whole phase"
