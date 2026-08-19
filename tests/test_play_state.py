"""PlayState — the whole gameplay loop wired together."""
import pygame
import pytest

import settings
from game.core.input import InputState
from game.core.play_state import PlayState
from game.entities.monster import Blinker, Monster
from game.systems.eventbus import Events


def _press(**edges):
    i = InputState()
    for k, v in edges.items():
        setattr(i, k, v)
    return i


def _room(play, rid="classroom_a"):
    return play.classrooms[rid]


def _stand_in(play, rid="classroom_a"):
    room = _room(play, rid)
    play.player.pos.update(room["rect"].center)
    play.camera.snap_to(play.player.pos)
    return room


# ── world loading ─────────────────────────────────────────────────────────
def test_the_map_loads_a_playable_world(play):
    assert play.doors and play.classrooms and play.pickups and play.monsters
    assert play.open_tiles, "Emri needs somewhere to wake"


def test_every_classroom_has_a_colour_a_tint_and_furniture(play):
    for rid, room in play.classrooms.items():
        assert room["color"], f"{rid} has no colour"
        assert rid in play.classroom_tints
        assert rid in play.classroom_pulses
        assert rid in play.classroom_decor


def test_every_door_matches_a_real_classroom(play):
    for d in play.doors:
        assert d.room_id in play.classrooms
        assert d.color == play.classrooms[d.room_id]["color"]


def test_locked_doors_are_solid_and_open_ones_are_not(play):
    d = play.doors[0]
    assert d.rect in play.solid_rects(d.rect)
    d.locked = False
    assert d.rect not in play.solid_rects(d.rect)


def test_the_starting_roster_is_the_fixed_cast(play):
    """No respawns means this is the whole level, and every book has a guard."""
    names = [m.name for m in play.monsters]
    assert set(names) == {"Little Terror", "Little Snir"}
    assert len(play.monsters) == len(play.classrooms) * 2, "one guard + one resident"


def test_every_book_on_the_map_is_guarded(play):
    """An unguarded book is a free objective — the level was finishable in about
    a minute when one of them could just be picked up."""
    books = [p for p in play.pickups if p.item_type == "book"]
    assert books
    guarded_variants = {m.guards for m in play.monsters if m.guards}
    for b in books:
        assert b.variant in guarded_variants, f"the {b.variant} book has no guard"
        assert b.guarded


def test_a_guarded_book_cannot_be_picked_up_until_its_guard_dies(play):
    guarded = [p for p in play.pickups if p.guarded]
    assert guarded, "the map should start with at least one guarded book"
    book = guarded[0]
    play.player.pos.update(book.pos)
    play._collect_pickups()
    assert book in play.pickups, "it must stay on the floor while guarded"


# ── interaction ───────────────────────────────────────────────────────────
def test_a_key_unlocks_the_nearest_door(play, step):
    d = play.doors[0]
    play.monsters.clear()
    play.player.pos.update(d.rect.centerx, d.rect.bottom + 20)
    play.inventory.add("key")
    step(play, 1, inp=_press(interact=True))
    assert not d.locked and play.inventory.count("key") == 0


def test_pressing_interact_without_a_key_leaves_the_door_shut(play, step):
    d = play.doors[0]
    play.monsters.clear()
    play.player.pos.update(d.rect.centerx, d.rect.bottom + 20)
    step(play, 1, inp=_press(interact=True))
    assert d.locked


def test_the_hint_says_what_the_interact_key_would_do(play):
    d = play.doors[0]
    play.monsters.clear()
    play.player.pos.update(d.rect.centerx, d.rect.bottom + 20)
    assert play._compute_hint() == "[E] Need a key"
    play.inventory.add("key")
    assert play._compute_hint() == "[E] Unlock door"


def test_returning_the_right_book_advances_the_quest(play, step):
    room = _stand_in(play)
    play.monsters.clear()
    play.inventory.add("book", room["color"])
    before = play.quests.get("return_books")
    step(play, 1, inp=_press(interact=True))
    assert play.quests.get("return_books")[0] == before[0] + 1
    assert play.inventory.items == []


def test_the_wrong_book_is_refused_and_the_hint_explains_why(play, step):
    room = _stand_in(play, "classroom_a")
    play.monsters.clear()
    other = next(r["color"] for rid, r in play.classrooms.items() if rid != "classroom_a")
    play.inventory.add("book", other)
    before = play.quests.get("return_books")
    step(play, 1, inp=_press(interact=True))
    assert play.quests.get("return_books") == before
    assert play.inventory.count("book") == 1
    assert play._compute_hint() == "Wrong classroom for this book"


def test_collecting_a_potion_only_works_when_hurt(play):
    potion = next(p for p in play.pickups if p.item_type == "health")
    play.player.pos.update(potion.pos)
    play._collect_pickups()
    assert potion in play.pickups, "a full-health player must not waste it"
    play.player.take_damage(50)
    hurt = play.player.health
    play._collect_pickups()
    assert potion not in play.pickups and play.player.health > hurt


def test_a_full_inventory_leaves_items_on_the_floor(play):
    key = next(p for p in play.pickups if p.item_type == "key")
    for _ in range(play.inventory.capacity):
        play.inventory.add("key")
    play.player.pos.update(key.pos)
    play._collect_pickups()
    assert key in play.pickups


# ── combat ────────────────────────────────────────────────────────────────
def test_attacking_kills_a_monster_and_it_stays_dead(play, step):
    play.monsters = [Monster(play.player.pos.x + 10, play.player.pos.y, hits=1)]
    target = play.monsters[0]
    step(play, 1, inp=_press(attack=True))
    assert target.dead and play.monsters == []


def test_nothing_respawns_after_a_kill(play, step):
    play.monsters = [Monster(play.player.pos.x + 10, play.player.pos.y, hits=1)]
    step(play, 1, inp=_press(attack=True))
    step(play, 1200)                       # far longer than the old respawn delay
    assert play.monsters == [], "the roster is fixed — nothing comes back"


def test_killing_a_guard_frees_its_book(play, step):
    guard = next(m for m in play.monsters if m.guards)
    book = next(p for p in play.pickups
                if p.item_type == "book" and p.variant == guard.guards)
    assert book.guarded
    guard.health = 1
    play.player.pos.update(guard.pos)
    step(play, 1, inp=_press(attack=True))
    assert not book.guarded


def test_a_warriors_reach_decides_what_it_can_hit(make_play):
    for wid in ("elad", "roni"):
        p = make_play(wid, clear_monsters=True)
        reach = p.player.reach
        p.monsters = [Monster(p.player.pos.x + reach - 4, p.player.pos.y, hits=9)]
        assert p._nearest_monster(p.player.reach) is p.monsters[0]
        p.monsters[0].pos.x = p.player.pos.x + reach + 20
        assert p._nearest_monster(p.player.reach) is None


def test_attacking_thin_air_is_harmless(play, step):
    play.monsters.clear()
    step(play, 1, inp=_press(attack=True))


def test_a_webbed_player_struggles_instead_of_swinging(play, step):
    play.monsters.clear()
    play.player.take_web()
    struggle = play.player.struggle
    step(play, 1, inp=_press(attack=True))
    assert play.player.struggle == struggle - 1


def test_a_caster_projectile_damages_the_player(play, step, surface):
    from game.entities.fireball import Fireball
    play.monsters.clear()
    play.projectiles = [Fireball(play.player.pos.x, play.player.pos.y, (1, 0), 20)]
    full = play.player.health
    step(play, 1, surface=surface)
    assert play.player.health < full and play.projectiles == []


def test_projectiles_fizzle_against_walls(play, step, surface):
    from game.entities.fireball import Fireball
    play.monsters.clear()
    wall = next(iter(play.tilemap.solid))
    play.projectiles = [Fireball(wall[0] * play.tilemap.tw + 16,
                                 wall[1] * play.tilemap.th + 16, (1, 0), 20)]
    step(play, 1, surface=surface)
    assert play.projectiles == []


def test_running_out_of_health_ends_the_run(play, step):
    from game.core.defeat_state import DefeatState
    play.monsters.clear()
    play.player.take_damage(play.player.max_health)
    step(play, 1)
    assert play.lost and isinstance(play.game.state_stack[-1], DefeatState)


def test_a_finished_run_stops_simulating(play, step):
    play.monsters.clear()
    play.won = True
    before = play.elapsed
    step(play, 10)
    assert play.elapsed == before


# ── casts ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("kind,cls", [
    ("fire", "Fireball"), ("web", "WebProjectile"), ("bolt", "LightBolt"),
])
def test_each_cast_kind_spawns_its_own_projectile(play, kind, cls):
    play.monsters.clear()
    m = Monster(play.player.pos.x + 100, play.player.pos.y, hits=3)
    m.cast_kind = kind
    m.cast_request = pygame.Vector2(1, 0)
    play.monsters.append(m)
    play._collect_casts()
    assert [type(p).__name__ for p in play.projectiles] == [cls]
    assert m.cast_request is None, "the request must be consumed"


def test_difficulty_scales_the_damage_a_cast_deals(game):
    from game.entities.fireball import Fireball
    dmg = {}
    for level in ("Easy", "Hard"):
        game.difficulty = level
        ps = PlayState(game)
        game.push(ps)
        ps.monsters.clear()
        m = Monster(0, 0, hits=1)
        m.cast_kind, m.cast_request = "fire", pygame.Vector2(1, 0)
        ps.monsters.append(m)
        ps._collect_casts()
        dmg[level] = next(p for p in ps.projectiles if isinstance(p, Fireball)).damage
        game.pop()
    assert dmg["Hard"] > dmg["Easy"]


# ── the book-return payoff (§6) ───────────────────────────────────────────
def test_returning_a_book_fires_sound_sparkles_glow_and_a_tint_pulse(play):
    room = _stand_in(play)
    play.bus.emit(Events.BOOK_RETURNED, room_id=room["id"], color=room["color"])
    assert play.effects.items and play.book_flash > 0
    assert room["id"] in play.tint_pulses


def test_the_payoff_expires_on_its_own(play, step, surface):
    room = _stand_in(play)
    play.monsters.clear()
    play.bus.emit(Events.BOOK_RETURNED, room_id=room["id"], color=room["color"])
    step(play, 180, surface=surface)
    assert play.effects.items == [] and play.book_flash == 0 and not play.tint_pulses


def test_a_book_with_no_colour_does_not_crash_the_payoff(play, step, surface):
    play.monsters.clear()
    play.bus.emit(Events.BOOK_RETURNED, room_id="nowhere", color=None)
    step(play, 2, surface=surface)


def test_leaving_playstate_detaches_it_from_the_shared_bus(game):
    """The bus lives on Game and outlives a run: a leak means the chime doubles."""
    before = len(game.bus._subs[Events.BOOK_RETURNED])
    first = PlayState(game)
    game.push(first)
    game.switch(PlayState(game))
    assert len(game.bus._subs[Events.BOOK_RETURNED]) == before + 2
    assert first.effects.items == []
    game.bus.emit(Events.BOOK_RETURNED, room_id="classroom_a", color="red")
    assert first.effects.items == [], "the old state is still listening"


# ── Emri in context ───────────────────────────────────────────────────────
def test_emri_never_shows_up_in_level_one(play, step, surface):
    """It was too strong for the opening level; it now waits on the boss level."""
    for rid, room in play.classrooms.items():
        play._on_book_returned(room_id=rid, color=room["color"])
    step(play, 120, surface=surface)
    assert play.emri is None
    assert not any(isinstance(m, Blinker) for m in play.monsters)


def test_emri_can_still_be_summoned_for_the_boss_level(play):
    """The behaviour stays built and reachable — only the level-1 spawn is gone."""
    play.wake_emri()
    assert isinstance(play.emri, Blinker) and play.emri in play.monsters
    assert play.banner and "EMRI" in play.banner[0]


def test_summoning_emri_twice_only_makes_one(play):
    for _ in range(3):
        play.wake_emri()
    assert sum(isinstance(m, Blinker) for m in play.monsters) == 1


def test_a_hidden_emri_is_neither_targetable_nor_hinted(play, step, surface):
    play.monsters.clear()
    play.wake_emri()
    emri = play.emri
    for _ in range(900):
        step(play, 1, surface=surface)
        if emri.state == Blinker.HIDDEN:
            assert play._nearest_monster(10 ** 6) is not emri
            assert emri.name not in (play._compute_hint() or "")


def test_banishing_emri_clears_it_and_announces(play):
    play.wake_emri()
    emri = play.emri
    emri.targetable = True
    for _ in range(settings.EMRI_HITS):
        emri.take_hit(play.player.pos)
    play._on_monster_died(emri)
    assert play.emri is None and emri not in play.monsters
    assert "BANISHED" in play.banner[0]


# ── Roni's power ──────────────────────────────────────────────────────────
def test_z_sends_zina_and_spends_a_charge(make_play, step):
    p = make_play("roni")
    p.monsters = [Monster(p.player.pos.x + 60, p.player.pos.y, hits=5)]
    before = p.player.power_charges
    step(p, 1, inp=_press(power=True))
    assert p.zina is not None and p.player.power_charges == before - 1


def test_a_bite_kills_outright_however_tough_the_monster(make_play, step, surface):
    p = make_play("roni")
    tough = Monster(p.player.pos.x + 60, p.player.pos.y, hits=99)
    p.monsters = [tough]
    step(p, 1, inp=_press(power=True))
    step(p, 600, surface=surface, until=lambda: p.zina is None)
    assert tough.dead and tough not in p.monsters


def test_pressing_z_with_nothing_in_range_costs_nothing(make_play, step):
    p = make_play("roni", clear_monsters=True)
    before = p.player.power_charges
    step(p, 1, inp=_press(power=True))
    assert p.zina is None and p.player.power_charges == before
    assert p.banner and "Zina" in p.banner[0]


def test_zina_cannot_be_sent_twice_at_once(make_play, step):
    p = make_play("roni")
    p.monsters = [Monster(p.player.pos.x + 60, p.player.pos.y, hits=5)]
    step(p, 1, inp=_press(power=True))
    charges = p.player.power_charges
    step(p, 1, inp=_press(power=True))
    assert p.player.power_charges == charges, "no double-sending"


def test_charges_run_out_and_say_so(make_play, step, surface):
    p = make_play("roni")
    for _ in range(settings.ZINA_CHARGES + 1):
        p.monsters = [Monster(p.player.pos.x + 60, p.player.pos.y, hits=5)]
        step(p, 1, inp=_press(power=True))
        step(p, 600, surface=surface, until=lambda: p.zina is None)
    assert p.player.power_charges == 0
    p.monsters = [Monster(p.player.pos.x + 60, p.player.pos.y, hits=5)]
    step(p, 1, inp=_press(power=True))
    assert p.zina is None and "out of bites" in p.banner[0]


def test_the_knight_has_no_power_to_press(make_play, step):
    p = make_play("elad")
    p.monsters = [Monster(p.player.pos.x + 20, p.player.pos.y, hits=5)]
    step(p, 1, inp=_press(power=True))
    assert p.zina is None and p.player.power_charges == 0


def test_the_chosen_warrior_drives_the_player(make_play):
    from game.entities import warriors
    for wid in ("elad", "roni"):
        p = make_play(wid)
        w = warriors.get(wid)
        assert p.player.walk_speed == w["speed"]
        assert set(p.player.frames) == {"idle", "walk", "attack", "hurt"}


# ── drawing ───────────────────────────────────────────────────────────────
def test_a_whole_frame_draws_with_everything_on_screen(play, surface, step):
    from game.entities.fireball import Fireball
    play._on_book_returned(room_id="classroom_a", color="red")
    play.projectiles.append(Fireball(play.player.pos.x, play.player.pos.y - 60, (0, 1), 5))
    play.player.take_web()
    step(play, 30, surface=surface)


def test_victory_is_declared_once_the_quest_completes(play, step):
    """The run ends on the level-complete celebration, which hands off to the
    name entry — see test_weapons_and_level_end.py for that handoff."""
    from game.core.level_complete_state import LevelCompleteState
    play.monsters.clear()
    for rid, room in play.classrooms.items():
        play.inventory.add("book", room["color"])
        play.player.pos.update(room["rect"].center)
        step(play, 1, inp=_press(interact=True))
        if play.won:
            break
    assert play.won and isinstance(play.game.state_stack[-1], LevelCompleteState)
