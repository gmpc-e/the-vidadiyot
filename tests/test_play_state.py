"""PlayState — the whole gameplay loop wired together."""
import pygame
import pytest

import settings
from game.core.input import InputState
from game.core.play_state import PlayState
from game.entities.pickup import Pickup
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
    """Stand at the room's return locker — the book's destination since §5.

    Standing anywhere in the room used to be enough. It isn't: the drop is a
    specific spot you have to walk to, which is the whole point of the locker.
    """
    room = _room(play, rid)
    play.player.pos.update(play.lockers[rid].rect.center)
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
    assert set(names) == {"Little Terror", "Little Snir", "Teacher", "Schoolmaster"}
    # three classrooms x (a teacher inside + a corridor monster), plus one in the
    # electrical room, which used to be the only room you could cross for free
    assert len(play.monsters) == len(play.classrooms) * 2 + 1


def test_the_classrooms_hold_teachers_and_the_corridors_hold_the_casters(play):
    """A range decision, not a flavour one — see MONSTERS in tools/gen_map.py.

    Snir and Little Terror reach 250-260px and kite away below 120. A classroom
    is barely wider than that, so indoors they back into a corner and the fight
    stops working. Put one of them inside again and this speaks up."""
    rooms = [room["rect"] for room in play.classrooms.values()]
    for m in play.monsters:
        indoors = any(r.collidepoint(m.pos) for r in rooms)
        if indoors:
            assert m.cast_kind == "tome", f"{m.name} is a corridor monster indoors"
        else:
            assert m.cast_kind in ("fire", "web"), f"{m.name} belongs in a room"


def test_no_book_starts_on_the_floor_and_every_locker_has_a_carrier(play):
    """§5: a book is *won*, not found.

    Lying in the corridor behind a `guarded` flag, a book was visible and inert
    from the first minute, and the fight that freed it happened in another room.
    Every book now starts in a teacher's hands, and there is exactly one carrier
    per locker or a room becomes uncompletable."""
    assert not [p for p in play.pickups if p.item_type == "book"]
    carried = [m.drops for m in play.monsters if m.drops]
    assert sorted(carried) == sorted(set(carried)), "two monsters carry one book"
    assert set(carried) == {lk.color for lk in play.lockers.values()}


def test_killing_a_carrier_drops_a_shining_book_where_it_stood(play):
    teacher = next(m for m in play.monsters if m.drops)
    where = pygame.Vector2(teacher.pos)
    play._on_monster_died(teacher)
    book = next(p for p in play.pickups if p.item_type == "book")
    assert book.variant == teacher.drops
    assert book.pos.distance_to(where) < 1
    assert book.shining, "a won book has to announce itself"
    assert not book.guarded, "nothing is left to guard it"


def test_a_guarded_pickup_cannot_be_taken_until_its_guard_dies(play):
    """The `guarded` flag is unused by level one now that books drop from their
    carriers, but the mechanic stays: it is how a map places an item behind a
    fight rather than behind a door."""
    book = Pickup(play.player.pos.x, play.player.pos.y, "book", "red")
    book.guarded = True
    play.pickups.append(book)
    play._collect_pickups()
    assert book in play.pickups, "it must stay on the floor while guarded"
    book.guarded = False
    play._collect_pickups()
    assert book not in play.pickups


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


def test_a_book_cannot_go_home_while_a_monster_is_still_in_the_room(play, step):
    """§5's whole point: the drop is earned with a fight, not a walk."""
    room = _stand_in(play, "classroom_a")
    play.inventory.add("book", room["color"])
    resident = next(m for m in play.monsters if room["rect"].collidepoint(m.pos))
    before = play.quests.get("return_books")
    step(play, 1, inp=_press(interact=True))
    assert play.quests.get("return_books") == before, "it delivered past a guard"
    assert play.inventory.count("book") == 1
    assert play._compute_hint() == "Clear the room first!"
    play.monsters.remove(resident)
    _stand_in(play, "classroom_a")
    step(play, 1, inp=_press(interact=True))
    assert play.quests.get("return_books")[0] == before[0] + 1


def test_any_monster_in_the_room_blocks_the_drop_not_just_its_guard(play):
    """A monster chased in from the corridor counts too — "something is in here
    with me" is the readable rule. Nothing respawns, so it can't deadlock."""
    room = _room(play, "classroom_a")
    for m in list(play.monsters):
        if room["rect"].collidepoint(m.pos):
            play.monsters.remove(m)
    assert play.room_cleared("classroom_a")
    intruder = play.monsters[0]
    intruder.pos.update(room["rect"].center)
    assert not play.room_cleared("classroom_a")


def test_the_locker_sits_in_its_room_and_the_hint_points_you_at_it(play):
    """One per classroom, inside it, and reachable — a locker outside the room
    or inside a wall would make its book undeliverable."""
    assert set(play.lockers) == set(play.classrooms)
    for rid, locker in play.lockers.items():
        room = play.classrooms[rid]
        assert room["rect"].contains(locker.rect), f"{rid}'s locker is outside it"
        assert locker.color == room["color"]
    room = _room(play, "classroom_a")
    play.monsters.clear()
    play.inventory.add("book", room["color"])
    play.player.pos.update(room["rect"].center)      # in the room, off the locker
    assert play._compute_hint() == "Put the book in the locker"


def test_a_delivered_locker_shows_it(play, step, surface):
    room = _stand_in(play, "classroom_a")
    play.monsters.clear()
    play.inventory.add("book", room["color"])
    step(play, 1, inp=_press(interact=True))
    assert play.lockers["classroom_a"].filled
    step(play, 3, surface=surface)


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
    book = Pickup(play.player.pos.x, play.player.pos.y, "book", "red")
    play.pickups.append(book)
    for _ in range(play.inventory.capacity):
        play.inventory.add("key")
    play._collect_pickups()
    assert book in play.pickups


# ── keys are killed for, and dropped where the monster fell (§13) ─────────
def test_killing_monsters_drops_the_keys_on_the_floor(play):
    """⚠️ Three keys for three doors, and no more: a fourth is dead weight.

    They land on the ground rather than going into the pack — handing one over
    silently meant a key you never saw, so the reward for a fight was a number
    changing in a corner."""
    assert not [p for p in play.pickups if p.item_type == "key"]
    for m in list(play.monsters):
        where = pygame.Vector2(m.pos)
        play._on_monster_died(m)
    keys = [p for p in play.pickups if p.item_type == "key"]
    assert len(keys) == settings.KEYS_FROM_KILLS
    assert play.keys_earned == settings.KEYS_FROM_KILLS
    assert all(k.shining for k in keys), "a won key should announce itself"
    assert play.inventory.count("key") == 0, "it must be picked up, not granted"


def test_a_dropped_key_lands_where_the_monster_fell(play):
    m = play.monsters[0]
    where = pygame.Vector2(m.pos)
    play._on_monster_died(m)
    key = next(p for p in play.pickups if p.item_type == "key")
    assert key.pos.distance_to(where) < 1


def test_the_key_counter_moves_only_once_it_is_actually_picked_up(play):
    """The quest counts `ITEM_COLLECTED`, which `_collect_pickups` emits."""
    before = play.quests.get("find_keys")[0]
    play._on_monster_died(play.monsters[0])
    assert play.quests.get("find_keys")[0] == before, "counted before pickup"
    key = next(p for p in play.pickups if p.item_type == "key")
    play.player.pos.update(key.pos)
    play._collect_pickups()
    assert play.quests.get("find_keys")[0] == before + 1


def test_the_duel_never_drops_a_key(game):
    """⚠️ A key opens a classroom door and the arena *is* a locked classroom —
    so a key dropped by one of Emri's summons let the player unlock the door and
    walk out of the boss fight."""
    from game.core.play_state import PlayState
    d = PlayState(game, duel=True)
    game.push(d)
    d.emri.health = d.emri.max_health * 0.7
    d._update_duel(settings.FIXED_DT)
    for a in list(d._adds):
        d._on_monster_died(a)
    assert not [p for p in d.pickups if p.item_type == "key"]
    assert d.inventory.count("key") == 0



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


def test_killing_a_carrier_in_the_room_completes_that_room(play, step):
    """The §5 loop end to end: the fight produces the objective it gates."""
    teacher = next(m for m in play.monsters if m.drops)
    assert not [p for p in play.pickups if p.item_type == "book"]
    teacher.health = 1
    play.player.pos.update(teacher.pos)
    step(play, 1, inp=_press(attack=True))
    book = next(p for p in play.pickups if p.item_type == "book")
    assert book.variant == teacher.drops and book.shining


def test_a_warriors_reach_decides_what_it_can_hit(make_play):
    for wid in ("wallad", "roni"):
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
def test_returning_a_book_counts_it_shakes_the_room_and_glows_the_hud(play):
    """⚠️ Deliberately **no** particle burst and no room-colour flush — see
    `_on_book_returned`. If a reward animation reappears here, this is the test
    that was supposed to argue with it."""
    room = _stand_in(play)
    before = play.books_home
    play.bus.emit(Events.BOOK_RETURNED, room_id=room["id"], color=room["color"])
    assert play.books_home == before + 1
    assert play.book_flash > 0
    assert play.camera._shake > 0


def test_the_payoff_expires_on_its_own(play, step, surface):
    room = _stand_in(play)
    play.monsters.clear()
    play.bus.emit(Events.BOOK_RETURNED, room_id=room["id"], color=room["color"])
    step(play, 180, surface=surface)
    assert play.book_flash == 0


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
    assert first.books_home == 0
    game.bus.emit(Events.BOOK_RETURNED, room_id="classroom_a", color="red")
    assert first.books_home == 0, "the old state is still listening"


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
    p = make_play("wallad")
    p.monsters = [Monster(p.player.pos.x + 20, p.player.pos.y, hits=5)]
    step(p, 1, inp=_press(power=True))
    assert p.zina is None and p.player.power_charges == 0


def test_the_chosen_warrior_drives_the_player(make_play):
    from game.entities import warriors
    for wid in ("wallad", "roni"):
        p = make_play(wid)
        w = warriors.get(wid)
        assert p.player.walk_speed == w["speed"]
        assert {"idle", "walk", "attack", "hurt"} <= set(p.player.frames)


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
        play.player.pos.update(play.lockers[rid].rect.center)
        step(play, 1, inp=_press(interact=True))
        if play.won:
            break
    assert play.won and isinstance(play.game.state_stack[-1], LevelCompleteState)


# ── the web bites (§5) ────────────────────────────────────────────────────
def test_being_webbed_drains_health_until_you_break_free(play, step):
    """⚠️ A web used to be a pure pause: it held you still and did nothing, so
    the right play was to ignore it and mash. Now being stuck costs something."""
    play.monsters.clear()
    play.player.take_web()
    start = play.player.health
    step(play, 60)
    assert play.player.health < start, "the web did nothing"
    caught = start - play.player.health
    play.player.webbed = False
    play.player.health = start
    step(play, 60)
    assert start - play.player.health < caught, "it drained after release too"


def test_the_web_drain_does_not_spam_the_hurt_grunt(play, step):
    """`take_damage` flinches and asks for a grunt, which is right for a blow
    and wrong sixty times a second."""
    play.monsters.clear()
    play.player.take_web()
    play.player.sound_request = None
    step(play, 30)
    assert play.player.sound_request is None
    assert play.player.hurt_flash == 0


def test_a_web_can_finish_a_dying_player(play, step):
    play.monsters.clear()
    play.player.health = 1.0
    play.player.take_web()
    step(play, 30)
    assert play.lost


# ── monsters are solid to the player (§10) ────────────────────────────────
def test_the_player_cannot_walk_through_a_monster(play):
    m = play.monsters[0]
    play.player.pos.update(m.pos.x - 60, m.pos.y)
    before = pygame.Vector2(play.player.pos)
    for _ in range(90):
        play.player.update(settings.FIXED_DT, _press(), collider=play.player_collider)
        play.player.vel.update(settings.PLAYER_WALK, 0)
        play.player.move_and_collide(settings.FIXED_DT, play.player_collider)
    assert play.player.pos.x > before.x, "it never moved at all"
    assert not play.player.hitbox.colliderect(m.hitbox), "walked into the monster"


def test_a_monster_standing_on_the_player_is_pushed_apart(play, step):
    """Monsters do not collide with the player when *they* move, so one can walk
    onto a player who is holding still — and a player holding still never calls
    `move_and_collide`, so nothing would resolve it.

    ⚠️ The guarantee is *separation*, not a direction. The push goes along the
    shallowest axis, which is the shortest way out; asserting the player escapes
    to any particular side would be asserting an implementation detail."""
    m = play.monsters[0]
    play.player.pos.update(m.pos)
    assert play.player.hitbox.colliderect(m.hitbox), "they should start overlapped"
    step(play, 4)
    assert not play.player.hitbox.colliderect(m.hitbox), "still inside it"


def test_contact_does_not_switch_collision_off(play):
    """⚠️ The bug this replaced: monsters already *touching* the player were
    excluded from its collider so that an overlap could be escaped. Monsters
    close on you constantly, so contact is the normal state — and while touching,
    collision was simply off and the player walked straight through."""
    m = play.monsters[0]
    p = play.player
    p.pos.update(m.pos.x - 40, m.pos.y)
    m.pos.update(p.pos.x + 30, p.pos.y)
    assert p.hitbox.colliderect(m.hitbox), "this test needs them touching"
    for _ in range(200):
        p.vel.update(settings.PLAYER_WALK, 0)
        p.move_and_collide(settings.FIXED_DT, play.player_collider)
        play._separate_from_monsters()
    assert p.pos.x < m.pos.x, "walked straight through it"
    assert not p.hitbox.colliderect(m.hitbox)


# ── projectiles clear the furniture (§11) ─────────────────────────────────
def test_a_thrown_book_flies_over_a_desk_but_not_through_a_wall(play):
    desk = play.decor_solids[0]
    assert play.solid_rects(desk), "the desk is not solid at all"
    assert not play.wall_rects(desk), "a desk must not stop a projectile"
    wall = play.tilemap.solid_rects(pygame.Rect(0, 0, 4000, 4000))[0]
    assert play.wall_rects(wall), "a wall must stop one"
