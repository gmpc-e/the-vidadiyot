"""Entity base, Player, Pickup, Door, and the projectiles."""
import pygame
import pytest

import settings
from game.core.input import InputState
from game.core.camera import Camera
from game.entities import warriors
from game.entities.entity import Entity
from game.entities.fireball import Fireball
from game.entities.interactable import Door
from game.entities.lightbolt import LightBolt
from game.entities.pickup import Pickup, item_color
from game.entities.player import Player
from game.entities.web import WebProjectile
from game.systems.inventory import Inventory


class _Walls:
    """A collider exposing one solid rect, matching PlayState's interface."""
    def __init__(self, *rects):
        self.rects = [pygame.Rect(r) for r in rects]

    def solid_rects(self, box):
        return [r for r in self.rects if r.colliderect(box)]


@pytest.fixture
def camera():
    return Camera(settings.INTERNAL_RES)


# ── Entity ────────────────────────────────────────────────────────────────
def test_hitbox_is_centred_on_the_position():
    e = Entity(100, 50, 20, 10)
    assert e.hitbox.center == (100, 50)
    assert e.hitbox.size == (20, 10)


def test_update_integrates_velocity():
    e = Entity(0, 0, 4, 4)
    e.vel = pygame.Vector2(60, -30)
    e.update(0.5)
    assert e.pos == pygame.Vector2(30, -15)


def test_move_and_collide_stops_at_a_wall_instead_of_passing_through():
    e = Entity(0, 0, 20, 20)
    e.vel = pygame.Vector2(600, 0)
    for _ in range(20):
        e.move_and_collide(settings.FIXED_DT, _Walls((50, -50, 20, 200)))
    assert e.hitbox.right <= 50


def test_move_and_collide_resolves_axes_separately_so_walls_can_be_slid_along():
    """Blocked horizontally, the entity should still travel vertically."""
    e = Entity(0, 0, 20, 20)
    e.vel = pygame.Vector2(600, 100)
    for _ in range(20):
        e.move_and_collide(settings.FIXED_DT, _Walls((50, -500, 20, 1000)))
    assert e.hitbox.right <= 50 and e.pos.y > 0


def test_collision_is_a_destination_test_so_a_big_enough_step_tunnels():
    """Pins a known limitation rather than pretending it isn't there.

    `move_and_collide` moves first and only then checks the destination, so
    anything that crosses a whole wall inside one step passes straight through.
    Nothing in the game can: see the speed-margin test below, which is the guard
    that actually matters.
    """
    e = Entity(0, 0, 20, 20)
    e.vel = pygame.Vector2(1000, 0)
    e.move_and_collide(0.1, _Walls((50, -50, 20, 200)))
    assert e.pos.x > 50, "documented limitation — if this fails, sweeping landed"


def test_nothing_in_the_game_moves_far_enough_per_step_to_tunnel():
    """The real guard on the limitation above.

    A step must never cover a whole tile, or an entity could skip a wall. Raise
    any of these speeds past the margin and this fails before a player finds it.
    """
    fastest = max(
        settings.PLAYER_SPRINT,
        max(w["speed"] for w in warriors.WARRIORS) * (settings.PLAYER_SPRINT / settings.PLAYER_WALK),
        settings.ZINA_SPEED, settings.BOLT_SPEED, settings.FIREBALL_SPEED,
        settings.WEB_SPEED, settings.CASTER_SPEED, settings.WEBBER_SPEED,
        settings.MONSTER_SPEED,
    )
    per_step = fastest * settings.FIXED_DT
    assert per_step < settings.TILE, f"{per_step:.1f}px/step vs a {settings.TILE}px tile"


def test_a_free_entity_is_unaffected_by_distant_walls():
    e = Entity(0, 0, 10, 10)
    e.vel = pygame.Vector2(100, 0)
    e.move_and_collide(0.1, _Walls((500, 500, 10, 10)))
    assert e.pos.x == pytest.approx(10)


# ── Player: warrior wiring ────────────────────────────────────────────────
def test_player_takes_its_numbers_from_the_chosen_warrior():
    w = warriors.get("roni")
    p = Player(0, 0, warrior=w)
    assert (p.walk_speed, p.max_health, p.reach) == (w["speed"], w["max_health"], w["reach"])
    assert p.health == w["max_health"]


def test_player_defaults_to_the_default_warrior():
    assert Player(0, 0).warrior["id"] == warriors.DEFAULT_ID


def test_only_a_warrior_with_a_power_starts_with_charges():
    assert Player(0, 0, warriors.get("roni")).power_charges == settings.ZINA_CHARGES
    assert Player(0, 0, warriors.get("wallad")).power_charges == 0


def test_spending_a_power_runs_the_charges_out_and_then_refuses():
    p = Player(0, 0, warriors.get("roni"))
    assert all(p.spend_power() for _ in range(settings.ZINA_CHARGES))
    assert not p.spend_power()
    assert p.power_charges == 0


def test_a_powerless_warrior_can_never_spend():
    assert not Player(0, 0, warriors.get("wallad")).spend_power()


# ── Player: health ────────────────────────────────────────────────────────
def test_damage_and_death():
    p = Player(0, 0)
    p.take_damage(p.max_health)
    assert p.health == 0 and not p.alive


def test_health_never_goes_below_zero_or_above_the_warrior_maximum():
    p = Player(0, 0)
    p.take_damage(10 ** 6)
    assert p.health == 0
    p.heal(10 ** 6)
    assert p.health == p.max_health


def test_health_regenerates_only_after_the_delay():
    p = Player(0, 0)
    p.take_damage(50)
    hurt = p.health
    p._update_health(settings.PLAYER_REGEN_DELAY / 2)
    assert p.health == hurt, "regen must wait out the delay"
    p._update_health(settings.PLAYER_REGEN_DELAY)
    p._update_health(1.0)
    assert p.health > hurt


# ── Player: the web ───────────────────────────────────────────────────────
def test_the_web_takes_a_fixed_number_of_presses_to_break():
    p = Player(0, 0)
    p.take_web()
    assert p.webbed
    for _ in range(settings.WEB_STRUGGLE_HITS - 1):
        assert not p.struggle_free()
    assert p.struggle_free() and not p.webbed


def test_a_second_web_cannot_re_trap_someone_already_stuck():
    p = Player(0, 0)
    p.take_web()
    p.struggle_free()
    left = p.struggle
    p.take_web()
    assert p.struggle == left, "re-webbing must not top the counter back up"


def test_struggling_when_free_does_nothing():
    assert not Player(0, 0).struggle_free()


def test_a_webbed_player_cannot_move(inp):
    p = Player(100, 100)
    p.take_web()
    inp.move = pygame.Vector2(1, 0)
    p.update(0.1, inp)
    assert p.pos == pygame.Vector2(100, 100)


# ── Player: movement and animation ────────────────────────────────────────
def test_sprinting_is_faster_and_drains_stamina(inp):
    inp.move = pygame.Vector2(1, 0)
    walker, sprinter = Player(0, 0), Player(0, 0)
    walker.update(0.1, inp)
    inp.sprint = True
    sprinter.update(0.1, inp)
    assert sprinter.pos.x > walker.pos.x
    assert sprinter.stamina < settings.STAMINA_MAX


def test_sprint_scales_each_warrior_from_their_own_pace(inp):
    """The fast warrior must stay the fast one when sprinting."""
    inp.move = pygame.Vector2(1, 0)
    inp.sprint = True
    wallad = Player(0, 0, warriors.get("wallad"))
    roni = Player(0, 0, warriors.get("roni"))
    wallad.update(0.1, inp)
    roni.update(0.1, inp)
    assert roni.pos.x > wallad.pos.x


def test_stamina_cannot_be_spent_below_zero(inp):
    p = Player(0, 0)
    inp.move = pygame.Vector2(1, 0)
    inp.sprint = True
    for _ in range(200):
        p.update(0.1, inp)
    assert p.stamina == 0


def test_facing_follows_horizontal_movement(inp):
    p = Player(0, 0)
    inp.move = pygame.Vector2(-1, 0)
    p.update(0.1, inp)
    assert p.facing == -1
    inp.move = pygame.Vector2(1, 0)
    p.update(0.1, inp)
    assert p.facing == 1


def test_vertical_movement_leaves_facing_alone(inp):
    p = Player(0, 0)
    inp.move = pygame.Vector2(-1, 0)
    p.update(0.1, inp)
    inp.move = pygame.Vector2(0, 1)
    p.update(0.1, inp)
    assert p.facing == -1


def test_animation_state_priority_is_hurt_then_attack_then_walk(inp):
    p = Player(0, 0)
    assert p.anim_state == "idle"
    inp.move = pygame.Vector2(1, 0)
    p.update(0.1, inp)
    assert p.anim_state == "walk"
    p.start_swing()
    assert p.anim_state == "attack"
    p.take_damage(1)
    assert p.anim_state == "hurt"


def test_the_walk_cycle_really_alternates_between_two_frames():
    p = Player(0, 0)
    frames = [pygame.Surface((8, 8), pygame.SRCALPHA) for _ in range(4)]
    p.set_frames(**dict(zip(("idle", "walk", "attack", "hurt"), frames)))
    p._moving = True
    seen = {id(p._current_frame()) for i in range(20) for p._walk_t in (i * 0.05,)}
    assert len(seen) == 2


def test_set_frames_installs_every_state():
    p = Player(0, 0)
    frames = [pygame.Surface((8, 8), pygame.SRCALPHA) for _ in range(4)]
    p.set_frames(**dict(zip(("idle", "walk", "attack", "hurt"), frames)))
    assert set(p.frames) == {"idle", "walk", "attack", "hurt"}
    assert p.sprite is frames[0]


def test_the_player_draws_without_frames_installed(surface, camera):
    """The Entity fallback must still work — a missing sprite is not a crash."""
    Player(100, 100).draw(surface, camera)


def test_the_player_draws_in_every_state(surface, camera):
    p = Player(100, 100)
    p.set_frames(**{s: pygame.Surface((8, 8), pygame.SRCALPHA)
                    for s in ("idle", "walk", "attack", "hurt")})
    for setup in (lambda: None, p.start_swing, p.take_web,
                  lambda: p.take_damage(1)):
        setup()
        p.draw(surface, camera)


# ── Pickup ────────────────────────────────────────────────────────────────
def test_a_variant_colours_the_item_and_otherwise_the_type_does():
    from game.world.palette import color_rgb
    assert item_color("book", "red") == color_rgb("red")
    assert item_color("key") != (255, 255, 255)
    assert item_color("mystery") == (255, 255, 255)


def test_pickups_start_uncollected_and_unguarded():
    p = Pickup(0, 0, "book", "red")
    assert not p.collected and not p.guarded


@pytest.mark.parametrize("kind", ["book", "key", "health", "fuse"])
def test_every_pickup_kind_draws(kind, surface, camera):
    p = Pickup(50, 50, kind)
    p.update(0.3)
    p.draw(surface, camera)


# ── Door ──────────────────────────────────────────────────────────────────
def test_a_locked_door_blocks_and_an_unlocked_one_does_not():
    d = Door((0, 0, 32, 16), "classroom_a", "red")
    assert d.locked and d.blocks
    d.try_unlock(_inv_with_key())
    assert not d.locked and not d.blocks


def _inv_with_key():
    inv = Inventory(2)
    inv.add("key")
    return inv


def test_unlocking_spends_exactly_one_key():
    inv = _inv_with_key()
    inv.add("key")
    Door((0, 0, 32, 16), "a", "red").try_unlock(inv)
    assert inv.count("key") == 1


def test_unlocking_without_a_key_fails_and_leaves_it_locked():
    d = Door((0, 0, 32, 16), "a", "red")
    assert not d.try_unlock(Inventory(2))
    assert d.locked


def test_an_open_door_cannot_be_unlocked_again_and_costs_nothing():
    d = Door((0, 0, 32, 16), "a", "red")
    inv = _inv_with_key()
    inv.add("key")                       # two keys, so a wasted spend would show
    d.try_unlock(inv)
    assert not d.try_unlock(inv)
    assert inv.count("key") == 1, "a second try must not eat a key"


def test_door_distance_is_zero_inside_and_grows_outside():
    d = Door((0, 0, 32, 16), "a", "red")
    assert d.dist_to((16, 8)) == 0
    assert d.dist_to((32 + 10, 8)) == pytest.approx(10)


@pytest.mark.parametrize("locked", [True, False])
def test_doors_draw_in_both_states(locked, surface, camera):
    d = Door((40, 40, 64, 32), "a", "red")
    d.locked = locked
    d.draw(surface, camera)


# ── Projectiles ───────────────────────────────────────────────────────────
def test_a_fireball_travels_along_its_direction_and_damages_on_hit():
    f = Fireball(0, 0, (1, 0), damage=17)
    f.update(0.1)
    assert f.pos.x > 0 and f.pos.y == 0
    p = Player(0, 0)
    f.on_hit(p)
    assert p.health == p.max_health - 17


def test_a_web_entangles_rather_than_damaging():
    p = Player(0, 0)
    WebProjectile(0, 0, (1, 0)).on_hit(p)
    assert p.webbed and p.health == p.max_health


def test_a_lightbolt_damages_and_is_faster_than_a_fireball():
    p = Player(0, 0)
    b = LightBolt(0, 0, (1, 0), damage=9)
    b.on_hit(p)
    assert p.health == p.max_health - 9
    assert b.vel.length() > Fireball(0, 0, (1, 0), 1).vel.length()


@pytest.mark.parametrize("cls,args", [
    (Fireball, (5,)), (WebProjectile, ()), (LightBolt, (5,)),
])
def test_projectiles_expire_after_their_lifetime(cls, args):
    p = cls(0, 0, (1, 0), *args)
    p.update(p.life + 0.01)
    assert p.dead


@pytest.mark.parametrize("cls,args", [(Fireball, (5,)), (WebProjectile, ())])
def test_a_zero_direction_leaves_a_lobbed_projectile_stationary(cls, args):
    p = cls(0, 0, (0, 0), *args)
    p.update(0.1)
    assert p.vel == pygame.Vector2(0, 0)


def test_a_zero_direction_bolt_still_flies():
    """LightBolt deliberately differs: no aim means it defaults to one, rather
    than hanging motionless in the air the way a lobbed projectile does."""
    b = LightBolt(0, 0, (0, 0), 5)
    assert b.vel.length() == pytest.approx(settings.BOLT_SPEED)


@pytest.mark.parametrize("cls,args", [
    (Fireball, (5,)), (WebProjectile, ()), (LightBolt, (5,)),
])
def test_projectiles_draw(cls, args, surface, camera):
    p = cls(100, 100, (1, 0), *args)
    p.update(0.05)
    p.draw(surface, camera)


# ── directional facing ────────────────────────────────────────────────────
def _four_pose_player():
    p = Player(100, 100)
    frames = {s: pygame.Surface((8, 8), pygame.SRCALPHA)
              for s in ("idle", "walk", "attack", "hurt")}
    for d in ("down", "up", "side"):
        frames[f"walk_{d}"] = [pygame.Surface((8, 8), pygame.SRCALPHA)
                               for _ in range(3)]
    p.set_frames(**frames)
    return p


def _walk(p, dx, dy):
    inp = InputState()
    inp.move = pygame.Vector2(dx, dy)
    p.update(settings.FIXED_DT, inp, collider=None)
    return p.anim_state


def test_the_player_picks_the_view_that_matches_where_it_walks():
    """⚠️ A back view cannot be mirrored out of a front view — walking away is
    the direction that needs its own art, and this is what selects it."""
    p = _four_pose_player()
    assert _walk(p, 0, 1) == "walk_down"
    assert _walk(p, 0, -1) == "walk_up"
    assert _walk(p, 1, 0) == "walk_side"
    assert _walk(p, -1, 0) == "walk_side"
    # a diagonal reads better as a profile, and it is the one the mirror can
    # actually express
    assert _walk(p, 1, 1) == "walk_side"


def test_a_warrior_without_directional_art_behaves_exactly_as_before():
    """The rows are optional, so a character with one walk pose is untouched."""
    p = Player(0, 0)
    p.set_frames(**{s: pygame.Surface((8, 8), pygame.SRCALPHA)
                    for s in ("idle", "walk", "attack", "hurt")})
    assert _walk(p, 0, -1) == "walk"
    assert _walk(p, 1, 0) == "walk"


def test_only_the_side_view_is_mirrored(surface, camera):
    """Flipping a front or back view swaps the sword into the wrong hand for no
    gain — the character is symmetrical about the camera that way."""
    p = _four_pose_player()
    _walk(p, -1, 0)
    assert p.facing == -1 and p.anim_state == "walk_side"
    _walk(p, 0, -1)
    assert p.facing == -1, "walking up must not clear the horizontal facing"
    assert p.anim_state == "walk_up"
    for d in ((0, 1), (0, -1), (-1, 0), (1, 0)):
        _walk(p, *d)
        p.draw(surface, camera)


def test_stopping_does_not_spin_the_warrior_round_to_face_the_camera():
    """⚠️ Needs no art: a three-frame walk is contact / passing / contact, and
    the passing frame has the legs together and the body upright — near enough a
    standing pose to hold."""
    p = _four_pose_player()
    p.frames["idle_up"] = pygame.Surface((8, 8), pygame.SRCALPHA)
    p.frames["idle_side"] = pygame.Surface((8, 8), pygame.SRCALPHA)
    _walk(p, 0, -1)
    assert _walk(p, 0, 0) == "idle_up", "he turned around when he stopped"
    _walk(p, 1, 0)
    assert _walk(p, 0, 0) == "idle_side"
    _walk(p, 0, 1)
    assert _walk(p, 0, 0) == "idle", "down keeps the painted standing pose"


def test_a_warrior_with_no_directional_art_still_just_idles():
    p = Player(0, 0)
    p.set_frames(**{s: pygame.Surface((8, 8), pygame.SRCALPHA)
                    for s in ("idle", "walk", "attack", "hurt")})
    _walk(p, 0, -1)
    assert _walk(p, 0, 0) == "idle"


def test_only_sideways_views_mirror():
    """A mirrored front or back view puts the sword in the wrong hand."""
    p = _four_pose_player()
    p.frames["idle_up"] = pygame.Surface((8, 8), pygame.SRCALPHA)
    _walk(p, -1, 0)                       # facing left from here on
    assert p._mirrors(), "the side view must mirror"
    _walk(p, 0, -1)
    assert not p._mirrors(), "a back view must not mirror"
    _walk(p, 0, 1)
    assert not p._mirrors(), "a front view must not mirror"
    _walk(p, 0, 0)                        # idle, still facing down
    assert not p._mirrors(), "idle is a front view once directions exist"

    plain = Player(0, 0)
    plain.set_frames(**{s: pygame.Surface((8, 8), pygame.SRCALPHA)
                        for s in ("idle", "walk", "attack", "hurt")})
    _walk(plain, -1, 0)
    _walk(plain, 0, 0)
    assert plain._mirrors(), "a character with one pose keeps the old behaviour"


# ── the webbed pose (§22, §23) ────────────────────────────────────────────
def _webbed_player(frames=4):
    p = Player(0, 0)
    poses = {s: pygame.Surface((8, 8), pygame.SRCALPHA)
             for s in ("idle", "walk", "attack", "hurt")}
    poses["webbed"] = [pygame.Surface((8, 8), pygame.SRCALPHA) for _ in range(frames)]
    p.set_frames(**poses)
    return p


def test_the_web_pose_unwraps_as_you_mash_free():
    """⚠️ The strip runs barely-caught to fully-wrapped, so it plays *backwards*:
    struggling is the progress bar, not a clock."""
    p = _webbed_player()
    p.take_web()
    strip = p.frames["webbed"]
    assert p._current_frame() is strip[-1], "not fully wrapped when first caught"
    seen = [p._current_frame()]
    while p.webbed:
        p.struggle_free()
        if p.webbed:
            seen.append(p._current_frame())
    assert seen[-1] is not strip[-1], "it never unwrapped"
    assert strip.index(seen[-1]) < strip.index(seen[0])


def test_being_webbed_outranks_being_hit():
    """The web drains health every frame, so `hurt_flash` is nearly always up
    while caught — and a flinch pose over a trapped one reads as neither."""
    p = _webbed_player()
    p.take_web()
    p.take_damage(1)
    assert p.hurt_flash > 0
    assert p.anim_state == "webbed"


def test_a_warrior_with_no_webbed_art_falls_back_to_drawn_strands(surface, camera):
    p = Player(100, 100)
    p.set_frames(**{s: pygame.Surface((8, 8), pygame.SRCALPHA)
                    for s in ("idle", "walk", "attack", "hurt")})
    p.take_web()
    assert p.anim_state != "webbed"
    p.draw(surface, camera)          # the procedural fallback must still draw
