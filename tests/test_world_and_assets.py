"""Tilemap, spawner, palette, decor, icons, assets, and the outcome screens."""
import os

import pygame
import pytest

import settings
from game.core.assets import ASSETS, AssetManager, CrispFont
from game.core.camera import Camera
from game.core.input import InputState
from game.entities.pickup import Pickup
from game.ui import icons
from game.world import decor
from game.world.palette import ROOM_COLORS, color_rgb
from game.world.spawner import spawn_monsters, spawn_pickups
from game.world.tilemap import TileMap

MAP_PATH = os.path.join(ASSETS, "maps", "school_slice.tmx")


@pytest.fixture(scope="module")
def tilemap():
    return TileMap(MAP_PATH)


@pytest.fixture
def camera():
    return Camera(settings.INTERNAL_RES)


# ── tilemap ───────────────────────────────────────────────────────────────
def test_the_map_has_size_and_walls(tilemap):
    assert tilemap.cols > 0 and tilemap.rows > 0
    assert tilemap.px_w == tilemap.cols * tilemap.tw
    assert tilemap.solid, "a map with no walls would let the player leave"


def test_the_map_edge_is_solid_so_the_player_cannot_walk_out(tilemap):
    assert (0, 0) in tilemap.solid
    assert (tilemap.cols - 1, tilemap.rows - 1) in tilemap.solid


def test_a_query_outside_the_map_is_clamped_rather_than_crashing(tilemap):
    assert tilemap.solid_rects(pygame.Rect(-500, -500, 32, 32)) == []


def test_solid_rects_only_returns_overlapping_tiles(tilemap):
    tx, ty = next(iter(tilemap.solid))
    box = pygame.Rect(tx * tilemap.tw, ty * tilemap.th, tilemap.tw, tilemap.th)
    rects = tilemap.solid_rects(box)
    assert box in rects
    assert all(r.colliderect(box) for r in rects)


def test_solid_rects_is_empty_in_open_floor(tilemap):
    for ty in range(tilemap.rows):
        for tx in range(tilemap.cols):
            if (tx, ty) not in tilemap.solid:
                box = pygame.Rect(tx * tilemap.tw + 8, ty * tilemap.th + 8, 8, 8)
                assert tilemap.solid_rects(box) == []
                return
    pytest.fail("the map has no walkable tile at all")


def test_every_tile_the_map_uses_exists_in_the_tileset(tilemap):
    """The .tmx names a tile count and the tileset PNG has to back it.

    These are written by one tool run (`gen_map.py` calls `extract_map_art`)
    precisely so they cannot drift — but they are two files, and the failure
    when they do drift is silent: pytmx hands back no image for a GID past the
    end of the strip, so the tile is simply never drawn and the map gains
    invisible holes.
    """
    used = {gid for layer in tilemap._tile_layers
            for row in layer.data for gid in row if gid}
    assert used, "the map draws no tiles at all"
    for gid in used:
        assert tilemap.tmx.get_tile_image_by_gid(gid), f"GID {gid} has no image"


def test_the_floor_is_made_of_more_than_one_tile(tilemap):
    """Worn-floor variants are scattered through the classrooms so the parquet
    stops reading as wallpaper. If the sprinkle in `gen_map.build_grid` is lost,
    the map still works and just looks flat again — which nothing else notices."""
    used = {gid for layer in tilemap._tile_layers
            for row in layer.data for gid in row if gid}
    assert len(used) >= 6, f"only {len(used)} distinct tiles on the map"


def test_walls_are_solid_and_floors_are_not(tilemap):
    """The `solid=true` property is written per tile id by `gen_map`; getting
    that list wrong is how you get a map you can walk through."""
    walkable = tilemap.solid_rects(pygame.Rect(25 * 32, 17 * 32, 8, 8))
    assert walkable == [], "the middle of the corridor should be walkable"
    assert tilemap.solid_rects(pygame.Rect(0, 0, 8, 8)), "the corner should be solid"


def test_named_objects_can_be_looked_up(tilemap):
    assert tilemap.object_by_name("player_start") is not None
    assert tilemap.object_by_name("no_such_object") is None


def test_the_player_starts_somewhere_walkable(tilemap):
    start = tilemap.object_by_name("player_start")
    box = pygame.Rect(0, 0, *settings.PLAYER_SIZE)
    box.center = (int(start.x), int(start.y))
    assert tilemap.solid_rects(box) == [], "the player would start inside a wall"


# ── spawner ───────────────────────────────────────────────────────────────
def test_pickups_spawn_with_their_type_and_variant(tilemap):
    """No books: since §5 they are carried by the teachers, not placed."""
    pickups = spawn_pickups(tilemap)
    assert pickups
    kinds = {p.item_type for p in pickups}
    assert kinds == {"health"}, "keys and books are both earned now, not placed"


def test_monsters_spawn_carrying_the_book_the_map_gave_them(tilemap):
    """`drops` has to survive the trip through the .tmx — it is the only thing
    connecting a classroom's fight to that classroom's objective."""
    pickups = spawn_pickups(tilemap)
    sprites = {"webber": None, "caster": None, "melee": None,
               "teacher_f": None, "teacher_m": None}
    monsters = spawn_monsters(tilemap, pickups, sprites)
    assert monsters
    carried = sorted(m.drops for m in monsters if m.drops)
    assert carried == ["blue", "green", "red"], carried   # one per classroom
    assert all(c in ROOM_COLORS for c in carried)
    for m in monsters:
        if m.drops:
            assert m.cast_kind == "tome", "only the teachers carry books"


def test_every_spawned_monster_stands_somewhere_walkable(tilemap):
    monsters = spawn_monsters(tilemap, spawn_pickups(tilemap),
                              {"webber": None, "caster": None, "melee": None,
                               "teacher_f": None, "teacher_m": None})
    for m in monsters:
        assert tilemap.solid_rects(m.hitbox) == [], f"{m.name} spawned in a wall"


def test_no_pickup_is_stuck_inside_a_wall(tilemap):
    for p in spawn_pickups(tilemap):
        assert tilemap.solid_rects(p.hitbox) == [], f"{p.item_type} is in a wall"


def test_every_book_has_a_classroom_to_go_home_to(tilemap):
    """A book whose colour matches no room can never be returned."""
    rooms = {o.properties.get("color") for o in tilemap.objects()
             if getattr(o, "type", None) == "room"}
    for p in spawn_pickups(tilemap):
        if p.item_type == "book":
            assert p.variant in rooms, f"no classroom for a {p.variant} book"


def test_there_are_at_least_as_many_keys_as_locked_doors(tilemap):
    """Fewer keys than doors makes the level unwinnable — and since 2026-08-20
    the keys come from **kills**, not from the floor, so the count that has to
    cover the doors is `KEYS_FROM_KILLS` and the size of the roster."""
    assert not [p for p in spawn_pickups(tilemap) if p.item_type == "key"], \
        "keys are dropped by monsters now, not placed"
    doors = sum(1 for o in tilemap.objects() if getattr(o, "type", None) == "door")
    monsters = sum(1 for o in tilemap.objects()
                   if getattr(o, "type", None) == "monster")
    assert settings.KEYS_FROM_KILLS >= doors, "not enough keys to open every door"
    assert monsters >= settings.KEYS_FROM_KILLS, "not enough monsters to drop them"


# ── palette ───────────────────────────────────────────────────────────────
def test_known_colours_resolve_and_unknown_ones_fall_back():
    assert color_rgb("red") == ROOM_COLORS["red"]
    assert color_rgb("chartreuse") == (255, 255, 255)
    assert color_rgb("chartreuse", (1, 2, 3)) == (1, 2, 3)


def test_room_colours_are_distinguishable_from_each_other():
    """Book/room matching is purely visual, so near-identical colours break it."""
    values = list(ROOM_COLORS.values())
    for i, a in enumerate(values):
        for b in values[i + 1:]:
            distance = sum(abs(x - y) for x, y in zip(a, b))
            assert distance > 90, f"{a} and {b} are too close to tell apart"


# ── decor ─────────────────────────────────────────────────────────────────
def test_decor_covers_the_room_and_leaves_the_floor_showing():
    rect = pygame.Rect(0, 0, 416, 384)
    surf, _ = decor.build(rect, "red", "classroom_a")
    assert surf.get_size() == rect.size
    opaque = sum(1 for y in range(0, 384, 4) for x in range(0, 416, 4)
                 if surf.get_at((x, y))[3] > 0)
    total = len(range(0, 384, 4)) * len(range(0, 416, 4))
    assert 0.02 < opaque / total < 0.5, "furniture should dress the room, not fill it"


def test_decor_is_deterministic_per_room():
    a, _ = decor.build(pygame.Rect(0, 0, 416, 384), "red", "classroom_a")
    b, _ = decor.build(pygame.Rect(0, 0, 416, 384), "red", "classroom_a")
    assert pygame.image.tobytes(a, "RGBA") == pygame.image.tobytes(b, "RGBA")


def test_different_rooms_are_furnished_differently():
    a, _ = decor.build(pygame.Rect(0, 0, 416, 384), "red", "classroom_a")
    b, _ = decor.build(pygame.Rect(0, 0, 416, 384), "red", "classroom_c")
    assert pygame.image.tobytes(a, "RGBA") != pygame.image.tobytes(b, "RGBA")


def test_decor_copes_with_a_small_room():
    decor.build(pygame.Rect(0, 0, 160, 120), "blue", "tiny")


def test_decor_has_no_colour_when_the_room_has_none():
    decor.build(pygame.Rect(0, 0, 416, 384), None, "colourless")


# ── icons ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("fn", [icons.draw_key, icons.draw_book, icons.draw_bottle])
@pytest.mark.parametrize("size", [(8, 8), (18, 18), (48, 48)])
def test_icons_draw_at_any_size(fn, size, surface):
    fn(surface, pygame.Rect(10, 10, *size))


def test_icons_actually_put_pixels_down():
    surf = pygame.Surface((24, 24))
    surf.fill((0, 0, 0))
    icons.draw_key(surf, pygame.Rect(2, 2, 20, 20), (255, 0, 0))
    assert any(surf.get_at((x, y))[:3] != (0, 0, 0)
               for x in range(24) for y in range(24))


# ── assets ────────────────────────────────────────────────────────────────
def test_images_are_cached_not_reloaded():
    a = AssetManager()
    assert a.image("sprites/knight_idle.png") is a.image("sprites/knight_idle.png")


def test_fonts_are_cached_per_size():
    a = AssetManager()
    assert a.font(None, 16) is a.font(None, 16)
    assert a.font(None, 16) is not a.font(None, 18)


def test_fonts_never_antialias():
    """Everything is drawn small then upscaled, so a blurred glyph is magnified."""
    font = AssetManager().font(None, 20)
    assert isinstance(font, CrispFont)
    hard = font.render("W", True, (255, 255, 255))
    alphas = {hard.get_at((x, y))[3] for x in range(hard.get_width())
              for y in range(hard.get_height())}
    assert alphas <= {0, 255}, "antialiasing crept back in"


def test_crispfont_still_answers_normal_font_questions():
    font = AssetManager().font(None, 16)
    assert font.get_height() > 0 and font.size("hello")[0] > 0


def test_every_sprite_the_game_asks_for_exists():
    """A missing file only fails at the moment the state loads it, which may be
    deep in a run; this catches it at build time instead."""
    a = AssetManager()
    for rel in ("sprites/snir.png", "sprites/terror.png", "sprites/emri.png",
                "sprites/zina.png", "ui/title.png", "ui/title_rule.png"):
        assert a.image(rel).get_width() > 0, rel


# ── outcome screens ───────────────────────────────────────────────────────
def test_defeat_draws(game, surface):
    from game.core.defeat_state import DefeatState
    from game.core.play_state import PlayState
    game.push(PlayState(game))
    d = DefeatState(game)
    game.push(d)
    d.update(settings.FIXED_DT, InputState())
    d.draw(surface)


@pytest.mark.parametrize("trigger", ["enter", "interact", "attack"])
def test_every_advertised_retry_key_actually_retries(game, trigger):
    """The screen prints 'Enter: try again', so Enter has to work — no intent is
    mapped to Return, which made that prompt a dead key."""
    from game.core.defeat_state import DefeatState
    from game.core.play_state import PlayState
    game.push(PlayState(game))
    d = DefeatState(game)
    game.push(d)
    if trigger == "enter":
        d.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    else:
        inp = InputState()
        setattr(inp, trigger, True)
        d.update(settings.FIXED_DT, inp)
    assert isinstance(game.state_stack[-1], PlayState)


def test_escape_from_defeat_goes_back_to_the_menu(game):
    from game.core.defeat_state import DefeatState
    from game.core.menu_state import MenuState
    from game.core.play_state import PlayState
    game.push(PlayState(game))
    d = DefeatState(game)
    game.push(d)
    inp = InputState()
    inp.pause = True
    d.update(settings.FIXED_DT, inp)
    assert isinstance(game.state_stack[-1], MenuState)


def test_victory_takes_a_name_and_shows_the_board(game, surface):
    from game.core.victory_state import VictoryState
    v = VictoryState(game, elapsed=42.0)
    game.push(v)
    for _ in range(5):
        v.update(settings.FIXED_DT, InputState())
        v.draw(surface)
    for ch in "RONI":
        v.handle_event(pygame.event.Event(pygame.KEYDOWN, key=ord(ch.lower()),
                                          unicode=ch))
    v.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    v.draw(surface)
    from game.systems import scores
    assert any(e["name"] == "RONI" for e in scores.load())


def test_a_duplicate_name_is_rejected_with_a_message(game, surface):
    from game.core.victory_state import VictoryState
    from game.systems import scores
    scores.add("Elad", 10.0)
    v = VictoryState(game, elapsed=99.0)
    game.push(v)
    for ch in "Elad":
        v.handle_event(pygame.event.Event(pygame.KEYDOWN, key=ord(ch.lower()),
                                          unicode=ch))
    v.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    v.draw(surface)
    assert len(scores.load()) == 1


def test_the_leaderboard_draws_empty_and_full(game, surface):
    from game.systems import scores
    from game.ui.leaderboard import draw_board
    font, big = game.assets.font(None, 18), game.assets.font(None, 24)
    draw_board(surface, font, big, scores.top(10), 320, 40)
    for i in range(12):
        scores.add(f"player{i}", i * 3.5)
    draw_board(surface, font, big, scores.top(10), 320, 40)


def test_the_victory_screen_owns_the_whole_frame(game, surface):
    """It used to draw the paused level underneath, so the run's HUD and the
    level's still-decaying camera shake sat behind the banner."""
    from game.core.victory_state import VictoryState, SCRIM
    import settings as _s
    v = VictoryState(game, elapsed=42.0)
    game.push(v)
    assert v.draw_below is False
    v.draw(surface)
    # nothing of the level shows through: every corner is the screen's own fill
    for pos in ((0, 0), (surface.get_width() - 1, 0), (0, surface.get_height() - 1)):
        assert surface.get_at(pos)[:3] == (8, 7, 12), pos
    # ...and the banner is genuinely large now, not the 253px it shipped at
    assert v.banner.get_width() > 0.85 * _s.INTERNAL_RES[0]
    assert SCRIM.bottom <= _s.INTERNAL_RES[1]


def test_the_victory_skulls_recycle_forever(game, surface):
    """They rise off the top of the frame and must come back from the bottom."""
    from game.core.victory_state import VictoryState
    import settings as _s
    from game.core.input import InputState
    v = VictoryState(game, elapsed=42.0)
    game.push(v)
    assert v.skulls
    for _ in range(1200):
        v.update(_s.FIXED_DT, InputState())
        assert all(-10 <= sk["y"] <= _s.INTERNAL_RES[1] + 50 for sk in v.skulls)
    v.draw(surface)


# ── the room stays crossable (the invariant that lets furniture be solid) ──
def _reachable(play, room, start, goal, body=44, step=8):
    """Walk a `body`-sized square from `start` to `goal` on a `step` grid.

    A flood fill, not a path: the question is only "can the thing that lives in
    this room get across it", which is what the old non-solid rule guaranteed
    for free and what solid furniture has to earn.
    """
    import collections
    r = room["rect"]
    def free(px, py):
        box = pygame.Rect(0, 0, body, body)
        box.center = (px, py)
        return not play.solid_rects(box)

    start = (int(start[0]) // step * step, int(start[1]) // step * step)
    seen, queue = {start}, collections.deque([start])
    goal_box = pygame.Rect(0, 0, body, body)
    while queue:
        px, py = queue.popleft()
        goal_box.center = (px, py)
        if goal_box.collidepoint(goal):
            return True
        for nx, ny in ((px + step, py), (px - step, py), (px, py + step), (px, py - step)):
            if (nx, ny) in seen or not r.inflate(80, 80).collidepoint(nx, ny):
                continue
            if free(nx, ny):
                seen.add((nx, ny))
                queue.append((nx, ny))
    return False


def test_a_monster_can_still_cross_every_furnished_classroom(play):
    """⚠️ The classroom furniture is **solid** since the player walked through
    desks. That is only safe while the aisles stay wider than the 44x44 thing
    living in the room — widen a desk or add a column back and this fails."""
    for rid, room in play.classrooms.items():
        teacher = next(m for m in play.monsters if room["rect"].collidepoint(m.pos))
        locker = play.lockers[rid]
        assert _reachable(play, room, teacher.pos, locker.rect.center), \
            f"{rid}: its own monster cannot reach the return locker"


def test_the_player_can_walk_in_through_every_classroom_door(play):
    """Nothing solid may be placed in a doorway — the scenery locker bank runs
    along the same wall the door is in and used to be painted straight across
    it."""
    for d in play.doors:
        room = play.classrooms[d.room_id]
        inside = (d.rect.centerx, room["rect"].bottom - 40)
        assert _reachable(play, room, inside, play.lockers[d.room_id].rect.center,
                          body=settings.PLAYER_SIZE[0]), \
            f"{d.room_id}: blocked between its door and its locker"


def test_the_furniture_actually_stops_a_body(play):
    """The point of the change: a desk is a thing you bump into."""
    assert play.decor_solids, "no furniture is solid at all"
    desk = play.decor_solids[0]
    box = pygame.Rect(0, 0, *settings.PLAYER_SIZE)
    box.center = desk.center
    assert play.solid_rects(box), "walked straight through it"


def test_nothing_spawns_inside_the_furniture(play):
    """Decor is baked after the roster is placed, so the furnisher has to be
    told where everyone is standing."""
    for m in play.monsters:
        assert not [r for r in play.decor_solids if r.colliderect(m.hitbox)], \
            f"{m.name} spawned inside a desk"
    assert not [r for r in play.decor_solids if r.colliderect(play.player.hitbox)]
    for p in play.pickups:
        assert not [r for r in play.decor_solids if r.colliderect(p.hitbox)], \
            f"a {p.item_type} spawned inside the furniture"


# ── animation strips ──────────────────────────────────────────────────────
def _fake_strip(n=4, heights=(120, 130, 170, 140)):
    """A strip of n figures, all standing on the same line, on black."""
    surf = pygame.Surface((160 * n, 260))
    surf.fill((0, 0, 0))
    for i in range(n):
        h = heights[i % len(heights)]
        pygame.draw.rect(surf, (200, 190, 170), (60 + i * 160, 230 - h, 40, h))
    return surf


def test_a_strip_slices_into_frames_that_share_one_scale_and_one_baseline():
    """⚠️ The trap this exists to avoid: fitting each frame to its own height
    shrinks the body on exactly the frame where the arms go up, so the sprite
    pulses as it plays. One scale, one bottom edge."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools"))
    import spritelib
    frames = spritelib.slice_strip(_fake_strip(), target_h=54, expect=4)
    assert len(frames) == 4
    assert {f.get_size() for f in frames} == {frames[0].get_size()}, \
        "frames must share a canvas so one blit position serves them all"
    assert max(f.get_height() for f in frames) == 54
    # the tallest source frame is the one that reaches `target_h`; the others
    # stay proportionally shorter rather than being stretched to match
    filled = [f.get_bounding_rect().height for f in frames]
    assert filled[2] == max(filled), "the tallest pose did not stay tallest"
    assert min(filled) < max(filled), "every frame was normalised to one height"
    for f in frames:
        assert f.get_bounding_rect().bottom == f.get_height(), "not bottom-aligned"


def test_slicing_a_strip_with_the_wrong_frame_count_fails_loudly():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools"))
    import spritelib
    with pytest.raises(SystemExit) as e:
        spritelib.slice_strip(_fake_strip(n=3), target_h=54, expect=4)
    assert "expected 4" in str(e.value)


def test_an_entity_plays_a_strip_and_a_lone_pose_side_by_side(surface, camera):
    """Strips land one sheet at a time, so both forms have to coexist."""
    from game.entities.entity import Entity
    e = Entity(50, 50, 20, 20)
    strip = [pygame.Surface((8, 8), pygame.SRCALPHA) for _ in range(4)]
    e.set_frames(idle=pygame.Surface((8, 8), pygame.SRCALPHA), walk=strip)
    assert e.frame_for("walk", 0.0) is strip[0]
    seen = {id(e.frame_for("walk", t / 30)) for t in range(40)}
    assert len(seen) == 4, "the painted strip did not cycle through all frames"
    # ...and a lone pose still synthesizes its two-step gait
    lone = Entity(0, 0, 20, 20)
    lone.set_frames(idle=pygame.Surface((8, 8), pygame.SRCALPHA),
                    walk=pygame.Surface((8, 8), pygame.SRCALPHA))
    assert len({id(lone.frame_for("walk", t / 30)) for t in range(40)}) == 2


def test_a_strip_can_be_driven_by_progress_instead_of_the_clock():
    """A wind-up has to line up with the moment the shot leaves, or the
    telegraph is decoration."""
    from game.entities.entity import Entity
    e = Entity(0, 0, 20, 20)
    strip = [pygame.Surface((8, 8), pygame.SRCALPHA) for _ in range(4)]
    e.set_frames(idle=strip[0], cast=strip)
    assert e.frame_for("cast", 0, progress=0.0) is strip[0]
    assert e.frame_for("cast", 0, progress=0.99) is strip[3]
    assert e.frame_for("cast", 0, progress=1.5) is strip[3], "must clamp"
    assert e.frame_for("cast", 0, progress=-1) is strip[0], "must clamp"


# ── ambience (§P4) ────────────────────────────────────────────────────────
def test_ambience_reaches_the_rooms_decor_never_furnished(play):
    """`decor` furnishes classrooms only; the corridor and entrance have never
    had anything in them, and that is what the roadmap calls the thing holding
    the look back."""
    assert play.ambience, "no ambience placed at all"
    rooms = [r["rect"] for r in play.classrooms.values()]
    corridor_props = [a for a in play.ambience
                      if not any(r.collidepoint(a.pos) for r in rooms)]
    assert corridor_props, "everything landed in the classrooms again"


def test_ambience_is_never_solid(play):
    """It is decoration. Nothing here may block a body."""
    for a in play.ambience:
        box = pygame.Rect(a.pos[0], a.pos[1], 8, 8)
        assert not [r for r in play.decor_solids if r.colliderect(box)]


def test_the_lamps_do_not_all_flicker_on_the_same_frame(play):
    """⚠️ Without a per-instance phase the whole level stutters together and it
    reads as the *screen* glitching, not as tired light fittings."""
    lamps = [a for a in play.ambience if len(a.frames) > 1]
    assert len(lamps) > 2
    assert len({round(a.t, 3) for a in lamps}) > 1, "every lamp shares a phase"


def test_an_animated_prop_cycles_and_comes_back(play, surface):
    prop = next(a for a in play.ambience if len(a.frames) > 1)
    seen = set()
    for _ in range(int(prop.period / settings.FIXED_DT) + 5):
        prop.update(settings.FIXED_DT)
        seen.add(id(prop.image))
        prop.draw(surface, play.camera)
    assert len(seen) > 1, "it never changed frame"
    assert 0 <= prop.t < prop.period, "the clock did not wrap"


def test_ambience_with_no_art_installed_is_empty_not_broken(monkeypatch):
    from game.world import ambience
    monkeypatch.setattr(ambience, "load", lambda name: None)
    assert ambience.build([pygame.Rect(0, 0, 400, 300)]) == []


def test_flattening_keeps_the_shape_and_replaces_the_colour():
    """⚠️ The fix for thin line art: a cobweb's strands average to luma ~14 in a
    big downscale, but the shape is intact in the alpha the whole time."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools"))
    import spritelib
    src = pygame.Surface((4, 4), pygame.SRCALPHA)
    src.set_at((1, 1), (10, 10, 12, 200))     # a dark, mostly-opaque strand
    src.set_at((2, 2), (0, 0, 0, 0))          # ...and a hole
    out = spritelib.flatten_color(src, (200, 200, 210), 0.5)
    assert out.get_at((1, 1))[:3] == (200, 200, 210)
    assert out.get_at((1, 1))[3] == 100, "alpha must scale, not reset"
    assert out.get_at((2, 2))[3] == 0, "a transparent pixel must stay transparent"


def test_the_end_screens_fit_their_leaderboards(game, surface):
    """⚠️ Both panels were resized for the art behind them and both then had a
    row land on the "play again" line. Rendered, the last row must clear it."""
    from game.core.victory_state import VictoryState, SCRIM_BOARD as VS
    from game.core.defeat_state import DefeatState, SCRIM as DS
    from game.systems import scores
    for i in range(8):
        scores.add(f"P{i}", 60.0 + i)

    v = VictoryState(game, 61.0)
    game.push(v)
    v.name = "P0"
    v._submit_name()
    rows = len(scores.top(6))
    # `draw_board` draws its title at top_y, then rows 8px under it. The note
    # line above is already paid for by the +34 offset the board is drawn at.
    pitch = v.font.get_height() + 4
    used = v.font_mid.get_height() + 8 + rows * pitch
    assert VS.y + 34 + used < VS.bottom - 18, "the victory board runs into the tip"
    v.draw(surface)
    game.pop()

    d = DefeatState(game)
    game.push(d)
    used = d.font_mid.get_height() + 8 + len(scores.top(6)) * (d.font.get_height() + 4)
    assert DS.y + 14 + used < DS.bottom - 18, "the defeat board runs into the tip"
    d.draw(surface)
