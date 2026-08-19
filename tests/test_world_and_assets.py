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
    pickups = spawn_pickups(tilemap)
    assert pickups
    kinds = {p.item_type for p in pickups}
    assert {"key", "book"} <= kinds
    for book in (p for p in pickups if p.item_type == "book"):
        assert book.variant in ROOM_COLORS


def test_monsters_spawn_and_flag_the_books_they_guard(tilemap):
    pickups = spawn_pickups(tilemap)
    sprites = {"webber": None, "caster": None, "melee": None}
    monsters = spawn_monsters(tilemap, pickups, sprites)
    assert monsters
    for m in monsters:
        if m.guards:
            book = next(p for p in pickups
                        if p.item_type == "book" and p.variant == m.guards)
            assert book.guarded


def test_every_spawned_monster_stands_somewhere_walkable(tilemap):
    monsters = spawn_monsters(tilemap, spawn_pickups(tilemap),
                              {"webber": None, "caster": None, "melee": None})
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
    """Fewer keys than doors would make the level unwinnable."""
    keys = sum(1 for p in spawn_pickups(tilemap) if p.item_type == "key")
    doors = sum(1 for o in tilemap.objects() if getattr(o, "type", None) == "door")
    assert keys >= doors, f"{keys} keys for {doors} doors"


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
    surf = decor.build(rect, "red", "classroom_a")
    assert surf.get_size() == rect.size
    opaque = sum(1 for y in range(0, 384, 4) for x in range(0, 416, 4)
                 if surf.get_at((x, y))[3] > 0)
    total = len(range(0, 384, 4)) * len(range(0, 416, 4))
    assert 0.02 < opaque / total < 0.5, "furniture should dress the room, not fill it"


def test_decor_is_deterministic_per_room():
    a = decor.build(pygame.Rect(0, 0, 416, 384), "red", "classroom_a")
    b = decor.build(pygame.Rect(0, 0, 416, 384), "red", "classroom_a")
    assert pygame.image.tobytes(a, "RGBA") == pygame.image.tobytes(b, "RGBA")


def test_different_rooms_are_furnished_differently():
    a = decor.build(pygame.Rect(0, 0, 416, 384), "red", "classroom_a")
    b = decor.build(pygame.Rect(0, 0, 416, 384), "red", "classroom_c")
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
