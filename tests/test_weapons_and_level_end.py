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
    assert not Player(0, 0, warriors.get("wallad")).throws


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
    for wid in ("wallad", "roni"):
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
    p = make_play("wallad", clear_monsters=True)
    m = Monster(p.player.pos.x + 20, p.player.pos.y, hits=5)
    p.monsters = [m]
    step(p, 1, inp=_press(attack=True))
    assert m.health == 3, "ATK 32 should land two pips"


def test_a_swing_that_kills_mid_way_does_not_keep_hitting(make_play, step):
    """Two pips against a one-pip monster must not run past its death."""
    p = make_play("wallad", clear_monsters=True)
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
    for wid, verb in (("wallad", "Attack"), ("roni", "Throw at")):
        p = make_play(wid, clear_monsters=True)
        p.monsters = [Monster(p.player.pos.x + 20, p.player.pos.y, hits=3)]
        assert verb in p._compute_hint()


# ── level complete ────────────────────────────────────────────────────────
def test_finishing_the_level_opens_the_celebration(play, step):
    play.monsters.clear()
    for rid, room in play.classrooms.items():
        play.inventory.add("book", room["color"])
        play.player.pos.update(play.lockers[rid].rect.center)
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
    # ⚠️ Clearing the level no longer ends the run — it opens the boss duel (§9).
    from game.core.play_state import PlayState
    nxt = game.state_stack[-1]
    assert isinstance(nxt, PlayState) and nxt.duel
    assert nxt.elapsed == 42.0, "the clock must carry into the duel"


def test_the_level_done_sting_is_registered_and_distinct():
    assert "level_done" in audio.SYNTHS
    rate = 2 * audio.SR
    sting = len(audio._synth_level_done()) / rate
    assert 1.0 < sting < 3.0, f"{sting:.2f}s"
    assert sting != len(audio._synth_fanfare()) / rate


# ── the boss duel (§9) ────────────────────────────────────────────────────
def test_the_duel_is_one_room_one_boss_and_nothing_else(game):
    """⚠️ The duel is the *same state* with the level stripped out, not a state
    of its own — Emri has to move, cast, be knocked back and die under exactly
    the rules the rest of the game runs on."""
    from game.core.play_state import PlayState
    d = PlayState(game, duel=True, elapsed=61.0)
    game.push(d)
    assert d.emri is not None, "no boss"
    assert d.monsters == [d.emri], "something else came along"
    assert d.pickups == [] and d.lockers == {}
    assert d.decor_solids == [], "a blink boss and furniture do not mix"
    assert d._counters() == [], "no keys or books to count"
    assert d.elapsed == 61.0, "the clock must carry over"


def test_the_duel_room_is_sealed_by_its_own_locked_door(game):
    """No new mechanic: a classroom's door starts locked, and in the duel the
    player has no key — so the room is an arena for free."""
    from game.core.play_state import PlayState
    d = PlayState(game, duel=True)
    game.push(d)
    assert d.inventory.count("key") == 0
    door = next(x for x in d.doors if x.room_id == d.DUEL_ROOM)
    assert door.locked and door.blocks
    room = d.classrooms[d.DUEL_ROOM]["rect"]
    assert room.collidepoint(d.player.pos), "the player starts outside the arena"
    assert room.collidepoint(d.emri.pos), "so does the boss"


def test_banishing_emri_wins_the_run(game, surface):
    from game.core.play_state import PlayState
    from game.core.victory_state import VictoryState
    d = PlayState(game, duel=True, elapsed=61.0)
    game.push(d)
    d._on_monster_died(d.emri)
    d._check_victory()
    assert d.won
    top = game.state_stack[-1]
    assert isinstance(top, VictoryState) and top.elapsed == 61.0


def test_an_empty_roster_on_frame_one_does_not_hand_over_the_win(game):
    """⚠️ Emri starts untargetable and away; winning on "no monsters left" would
    end the duel before the boss had arrived."""
    from game.core.play_state import PlayState
    d = PlayState(game, duel=True)
    game.push(d)
    d.monsters.clear()
    d.emri = None
    d._emri_woke = False
    d._check_victory()
    assert not d.won


def test_the_ordinary_level_still_ends_in_the_celebration(play, game):
    assert not play.duel
    assert play._counters(), "the level keeps its key and book counters"


def test_emri_phases_out_and_sends_help(game):
    """§9: at 75/50/25% it leaves, two of the school's own arrive, and only when
    they are dead does it come back."""
    from game.core.play_state import PlayState
    d = PlayState(game, duel=True)
    game.push(d)
    emri = d.emri
    assert d._adds == [] and len(d._phase_marks) == len(settings.EMRI_PHASE_MARKS)

    emri.health = emri.max_health * 0.6          # past the first mark
    d._update_duel(settings.FIXED_DT)
    assert emri.dormant, "it stayed and fought"
    assert len(d._adds) == settings.EMRI_PHASE_ADDS
    assert all(a in d.monsters for a in d._adds)
    assert len(d._phase_marks) == len(settings.EMRI_PHASE_MARKS) - 1, \
        "the mark must be one-way"

    # ...and it does not summon again while the help is still alive
    d._update_duel(settings.FIXED_DT)
    assert len(d._adds) == settings.EMRI_PHASE_ADDS

    for a in list(d._adds):
        d._on_monster_died(a)
    d._update_duel(settings.FIXED_DT)
    assert not emri.dormant, "it never came back"


def test_the_phase_marks_do_not_fire_twice_at_the_same_health(game):
    """⚠️ Sitting exactly on a mark would summon a room's worth of monsters one
    frame at a time."""
    from game.core.play_state import PlayState
    d = PlayState(game, duel=True)
    game.push(d)
    d.emri.health = d.emri.max_health * settings.EMRI_PHASE_MARKS[0]
    d._update_duel(settings.FIXED_DT)
    summoned = len(d.monsters)
    for a in list(d._adds):
        d._on_monster_died(a)
    d._update_duel(settings.FIXED_DT)
    d._update_duel(settings.FIXED_DT)
    assert len(d.monsters) <= summoned, "it summoned again at the same health"


def test_zina_wounds_the_boss_instead_of_killing_it(game, step):
    """⚠️ An instant kill made Emri a formality — one charge of a power the
    player has three of."""
    from game.core.play_state import PlayState
    game.warrior = "roni"
    d = PlayState(game, duel=True)
    game.push(d)
    emri = d.emri
    emri.targetable = True
    full = emri.health
    for i in range(settings.ZINA_CHARGES):
        d.zina = None
        d.player.power_charges = 1
        d.player.pos.update(emri.pos)
        d._use_power()
        d.zina.killed = emri
        d._update_zina(settings.FIXED_DT)
        if emri.dead:
            break
    assert emri.health < full, "the bite did nothing"
    assert not emri.dead, "⚠️ every charge Roni has must not finish the boss"
    spent = full - emri.health
    assert spent < full * 0.5, f"three bites took {spent / full:.0%} of the boss"


def test_the_boss_flag_starts_the_duel(monkeypatch):
    """`--boss` is a test hatch, and deliberately not a menu entry: the duel is
    the end of a run, and the title screen must not be able to skip to it."""
    import main as entry
    started = {}
    monkeypatch.setattr(entry.Game, "run", lambda self: None)
    monkeypatch.setattr(entry.Game, "push",
                        lambda self, st: started.setdefault("state", st))
    monkeypatch.setattr("sys.argv", ["main.py", "--boss"])
    entry.main()
    assert getattr(started["state"], "duel", False)


def test_one_blow_crossing_two_marks_is_still_one_phase_break(game):
    """⚠️ The bug that stranded a live playtest: `_summon_help` fired once per
    *mark*, and a heavy hit can cross two — which put four monsters on the two
    spawn points, two of them standing exactly inside the other two. The player
    killed the pair they could see and Emri never returned, because `_adds` still
    held the pair hidden inside them."""
    from game.core.play_state import PlayState
    d = PlayState(game, duel=True)
    game.push(d)
    d.emri.health = d.emri.max_health * 0.1       # past every mark at once
    d._update_duel(settings.FIXED_DT)
    assert len(d._adds) == settings.EMRI_PHASE_ADDS, \
        f"{len(d._adds)} monsters for one phase break"
    assert d._phase_marks == [], "every crossed mark must be spent"

    spots = {(round(a.pos.x), round(a.pos.y)) for a in d._adds}
    assert len(spots) == len(d._adds), "two monsters share a spawn point"

    for a in list(d._adds):
        d._on_monster_died(a)
    d._update_duel(settings.FIXED_DT)
    assert not d.emri.dormant, "Emri never came back"


def test_the_duel_doors_cannot_be_opened_at_all(game):
    """⚠️ The arena is a locked classroom, and a locked door opens with a key —
    so a key dropped by one of Emri's summons let the player walk out of the
    boss fight. Sealed doors take no key."""
    from game.core.play_state import PlayState
    d = PlayState(game, duel=True)
    game.push(d)
    door = next(x for x in d.doors if x.room_id == d.DUEL_ROOM)
    assert door.sealed and door.locked
    d.inventory.add("key")                       # even if one somehow existed
    d.player.pos.update(door.rect.centerx, door.rect.top - 20)
    d._interact()
    assert door.locked, "walked out of the boss fight"
    assert d.inventory.count("key") == 1, "it ate the key too"


def test_emri_survives_a_swing_without_phasing(game):
    """⚠️ At 8 hits one sword swing was 25% of the boss, so Wallad's *first* hit
    triggered the 75% phase break and the fight was over before it had a shape."""
    from game.core.play_state import PlayState
    from game.entities import warriors
    d = PlayState(game, duel=True)
    game.push(d)
    swing = warriors.get("wallad")["damage"]
    assert swing / d.emri.max_health < 0.1, "one swing is more than a tenth of it"
    d.emri.health -= swing
    d._update_duel(settings.FIXED_DT)
    assert not d.emri.dormant, "one hit called for backup"


def test_emri_will_not_phase_out_twice_in_quick_succession(game):
    """⚠️ "Calls for help too frequently": damage arrives in bursts, so marks
    alone cannot space the breaks out. A grace period after it returns can."""
    from game.core.play_state import PlayState
    d = PlayState(game, duel=True)
    game.push(d)
    d.emri.health = d.emri.max_health * 0.6
    d._update_duel(settings.FIXED_DT)
    for a in list(d._adds):
        d._on_monster_died(a)
    d._update_duel(settings.FIXED_DT)
    assert not d.emri.dormant and d._phase_grace > 0

    d.emri.health = d.emri.max_health * 0.05      # straight past the next mark
    d._update_duel(settings.FIXED_DT)
    assert not d.emri.dormant, "it phased again immediately"
    assert d._phase_marks, "⚠️ the deferred mark must not be silently spent"

    for _ in range(int(settings.EMRI_PHASE_GRACE / settings.FIXED_DT) + 2):
        d._update_duel(settings.FIXED_DT)
    assert d.emri.dormant, "the deferred break never happened"


def test_summons_always_land_somewhere_reachable(game):
    """⚠️ **This deadlocked a live duel.** The spawn was `player.y - 90` with no
    lower bound, so a player standing near the top of the room put the summons
    *above the room's own top edge*, inside the wall. Unreachable monsters never
    die, `_adds` never empties, and Emri never comes back."""
    from game.core.play_state import PlayState
    d = PlayState(game, duel=True)
    game.push(d)
    room = d.classrooms[d.DUEL_ROOM]["rect"]
    for y in (room.y + 5, room.y + 60, room.centery, room.bottom - 20):
        d.player.pos.update(room.centerx, y)
        d._adds = []
        d.emri.dormant = False
        d._summon_help()
        for a in d._adds:
            assert room.collidepoint(a.pos), f"summoned outside the arena from y={y}"
            assert not d.solid_rects(a.hitbox), f"summoned inside a wall from y={y}"
            d.monsters.remove(a)


def test_zina_does_not_come_back_for_the_boss(game):
    """⚠️ She is three bites a *level*, and the duel is the end of the same
    level. Refilling her at the boss would make "save her by not using her" the
    correct play in the school, which is the opposite of what a power is for."""
    from game.core.play_state import PlayState
    from game.core.level_complete_state import LevelCompleteState
    import game.core.level_complete_state as L
    game.warrior = "roni"
    lvl = PlayState(game)
    game.push(lvl)
    lvl.player.power_charges = 1                 # two bites spent in the school
    lvl.quests.get = lambda k: (3, 3)
    lvl._check_victory()
    lc = game.state_stack[-1]
    assert isinstance(lc, LevelCompleteState) and lc.charges == 1
    lc.t = L.CAN_SKIP_AT
    lc.update(settings.FIXED_DT, _press(interact=True))
    duel = game.state_stack[-1]
    assert duel.duel and duel.player.power_charges == 1, "Zina refilled at the boss"


def test_the_boss_flag_still_gives_a_full_kit(game):
    """`--boss` has no level behind it, so it starts from the warrior's own
    defaults rather than from nothing."""
    from game.core.play_state import PlayState
    game.warrior = "roni"
    d = PlayState(game, duel=True)
    game.push(d)
    assert d.player.power_charges == settings.ZINA_CHARGES
