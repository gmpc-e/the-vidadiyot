"""PlayState — the actual game (combat model, doc §2.11).

Collect keys to unlock color-coded doors, fight guardian monsters to free the
books, and return every book to its matching classroom to win.

The roster is **fixed**: Little Snir and Little Terror hold the corridor, and a
Little Terror stands in each classroom. Killing one is permanent — nothing
respawns, so clearing a room stays cleared and the level can actually be won by
fighting. The one exception is Emri, the blink boss, which wakes on the first
book returned. Run out of health and it's YOU LOST; return all books and it's
VICTORY (+ leaderboard).
"""
import os
import random
import pygame

import settings
from game.core.state import State
from game.core.camera import Camera
from game.core.assets import ASSETS, load
from game.world.tilemap import TileMap
from game.world.palette import color_rgb
from game.world import ambience, decor
from game.world.spawner import _pose as _monster_pose
from game.world.spawner import spawn_pickups, spawn_monsters
from game.entities.pickup import Pickup
from game.entities.player import Player
from game.entities.monster import (make_emri, make_fire_caster,
                                   make_web_caster)
from game.entities.fireball import Fireball
from game.entities.web import WebProjectile
from game.entities.knife import Knife
from game.entities.lightbolt import LightBolt
from game.entities.tome import DarkTome
from game.entities.zina import Zina
from game.entities import warriors
from game.entities.interactable import Door, Locker

# cast_kind -> the sound made on the frame the projectile spawns. A kind with no
# entry falls back to the fire cast rather than going silent, since a new caster
# is far more likely to arrive before its audio than after it.
CAST_SOUND = {"web": "web_cast", "fire": "fire_cast",
              "bolt": "fire_cast", "tome": "tome_cast"}
from game.systems.inventory import Inventory
from game.systems.quests import QuestManager
from game.systems.eventbus import Events
from game.systems import difficulty
from game.ui.hud import HUD

MAP_PATH = os.path.join(ASSETS, "maps", "school_slice.tmx")
QUESTS_PATH = os.path.join(os.path.dirname(ASSETS), "data", "quests.json")
OPEN_ROOM_TYPES = ("corridor", "entrance")     # open areas Emri can wake in


class PlayState(State):
    """The level — and, with `duel=True`, the boss fight after it (§9).

    The duel is the *same state* with the level stripped out rather than a state
    of its own, and that is the point: Emri has to move, cast, be knocked back,
    be hit and die under exactly the rules the rest of the game runs on. A
    bespoke boss state would have been a second implementation of all of it, and
    the second one is always the one with the bugs.

    What `duel` removes: every other monster, every pickup, every locker, the
    room's furniture, and the book quest. What it leaves: one arena with the
    doors already locked, one very strong monster, and a clock that carries over
    from the level so the leaderboard still measures the whole run.
    """

    #: The classroom the duel is fought in. Its doors are locked from the start,
    #: which is what makes a room an arena without any new mechanic.
    DUEL_ROOM = "classroom_b"

    def __init__(self, game, duel=False, elapsed=0.0, charges=None):
        super().__init__(game)
        self.duel = duel
        self._carried = elapsed
        # Power charges brought in from the level. None means "whatever the
        # warrior starts with" — a fresh run, or `--boss` with no level behind it.
        self._carried_charges = charges

    def enter(self):
        # The duel asks for its own track (§M5). It does not exist yet, and
        # `play_music` deliberately leaves whatever is playing alone rather than
        # cutting to silence — so today the level track carries over.
        self.game.audio.play_music("duel" if self.duel else "level_one")
        self.bus = self.game.bus
        self.tilemap = TileMap(MAP_PATH)
        self.camera = Camera(settings.INTERNAL_RES)
        self.camera.set_world_bounds(pygame.Rect(0, 0, self.tilemap.px_w, self.tilemap.px_h))

        start = self.tilemap.object_by_name("player_start")
        px = (start.x, start.y) if start else (self.tilemap.px_w / 2, self.tilemap.px_h / 2)
        # ⚠️ Read first: the roster's health and the player's regeneration are
        # both scaled by it, and both are set up below.
        self.diff = difficulty.get(self.game.difficulty)
        self.warrior = warriors.get(getattr(self.game, "warrior", warriors.DEFAULT_ID))
        self.player = Player(*px, warrior=self.warrior)
        self.player.regen = self.diff.get("regen", 1.0)
        if self._carried_charges is not None:
            # ⚠️ Zina does not come back for the boss. She is three bites a
            # *level* and the duel is the end of the same level; refilling her
            # would make "save her by not using her" the correct play in the
            # school, which is the opposite of what a power is for.
            self.player.power_charges = self._carried_charges
        self._load_warrior_frames()
        self.camera.snap_to(self.player.pos)

        self.doors, self.classrooms, open_regions = self._load_world_objects()
        self.lockers = self._build_lockers()
        self.inventory = Inventory(settings.CARRY_CAPACITY)
        self.quests = QuestManager.from_file(self.bus, QUESTS_PATH)
        self.pickups = spawn_pickups(self.tilemap)
        self.sprites = {"webber": self.game.assets.image("sprites/snir.png"),
                        "caster": self.game.assets.image("sprites/terror.png"),
                        "teacher_f": self.game.assets.image("sprites/teacher_f.png"),
                        "teacher_m": self.game.assets.image("sprites/teacher_m.png"),
                        "emri": self.game.assets.image("sprites/emri.png")}
        # Extra poses, where the sheet carried them. A monster with no entry
        # here keeps its single sprite and simply never changes stance — which
        # is what every monster did before the teachers arrived.
        # map kind -> (art prefix, stances). ⚠️ The prefix is not the kind: the
        # map says "caster", the art says `terror_`.
        self.monster_poses = {
            "teacher_f": ("teacher_f", ("walk",)),
            "teacher_m": ("teacher_m", ("walk",)),
            # Little Terror is the first monster with a full sheet: a walk, a
            # fireball wind-up wired to `Caster.charge`, a flinch, and side
            # views of all three. ⚠️ No back-facing walk on the sheet, so she
            # turns toward the camera and sideways but never away.
            "caster": ("terror", ("walk", "cast", "hurt", "walk_up",
                                  "walk_side", "cast_side", "hurt_side")),
            # ⚠️ Snir's two sheets are **both** needed and neither is a superset:
            # v2 is entirely front-facing and v3 entirely side-facing. No back
            # walk on either, so she never turns away from the camera.
            "webber": ("snir", ("walk", "cast", "hurt",
                                "walk_side", "cast_side", "hurt_side")),
        }
        # The one projectile in the game with painted art, so unlike the others
        # it has to be handed its sprite when PlayState spawns it.
        self.tome_sprite = self.game.assets.image("sprites/tome.png")
        self.web_sprite = load("sprites/web_ball.png")   # None -> drawn fallback
        self.bite_sprite = load("sprites/bite_splash.png")
        self.fire_sprite = load("sprites/fireball.png")
        self.splashes = []
        self.monsters = spawn_monsters(self.tilemap, self.pickups, self.sprites,
                                       poses=self.monster_poses)
        self._scale_monster_health()
        self.player_collider = self._WithMonsters(self)
        self.projectiles = []        # monster casts, aimed at the player
        self.player_shots = []       # the player's own thrown weapons
        self.hud = HUD(self.game.assets, self.quests, self.inventory)
        self.hint = None
        self.zina = None                     # Roni's dog while she is out
        self.zina_sprite = self.game.assets.image("sprites/zina.png")
        self.knife_sprite = self.game.assets.image("sprites/roni_knife.png")
        self.emri = None                     # the boss, once it has woken
        self.books_home = 0
        self.keys_earned = 0
        self.banner = None                   # (text, seconds left)
        self.book_flash = 0.0        # HUD counter glow, seconds remaining (§6)

        self.elapsed = self._carried
        self._emri_woke = False
        self._phase_marks = []
        self._adds = []
        self._phase_grace = 0.0
        self.won = False
        self.lost = False
        self.kills = 0
        self._scare_cd = 0.0
        self.open_tiles = self._collect_open_tiles(open_regions)
        self.classroom_tints = self._build_classroom_tints()
        self.classroom_decor = self._build_classroom_decor()
        # Ambience goes in **every** room, not just the furnished classrooms —
        # the corridor and the entrance have never had anything in them.
        if self.duel:
            self._strip_for_duel()
        self.ambience = ambience.build(
            [r["rect"] for r in self.classrooms.values()] + open_regions,
            seed=len(self.classrooms))

        # keep the unsubscribes: the EventBus outlives this state (it lives on
        # Game), so a restart would otherwise leave the old PlayState listening
        # and every return would fire its effects twice.
        self._unsubs = [
            self.bus.on(Events.QUEST_COMPLETED,
                        lambda quest_id, **_: print(f"[quest] completed: {quest_id}")),
            self.bus.on(Events.BOOK_RETURNED, self._on_book_returned),
        ]

    def exit(self):
        for off in getattr(self, "_unsubs", []):
            off()
        self._unsubs = []
        self.quests.dispose()

    def _load_warrior_frames(self):
        """Load the chosen warrior's poses — a painted strip where one exists.

        A state is a **list** if `<prefix>_<state>_0.png` is on disk (a Phase 2
        animation strip) and a single Surface otherwise. Both forms play, so the
        strips can land one character at a time instead of all at once, and a
        checkout that has never run `extract_phase2.py` still animates off the
        synthesized gait.
        """
        prefix = self.warrior["sprites"]
        poses = {state: self._pose_or_strip(f"{prefix}_{state}")
                 for state in ("idle", "walk", "attack", "hurt")}
        # Directional walks are optional: a warrior whose sheet carries them
        # turns to face where it is going, and one that does not keeps the
        # single "walk" and behaves exactly as before.
        webbed = self._pose_or_strip(f"{prefix}_webbed", optional=True)
        if webbed:
            poses["webbed"] = webbed
        for facing in ("down", "up", "side"):
            got = self._pose_or_strip(f"{prefix}_walk_{facing}", optional=True)
            if got:
                poses[f"walk_{facing}"] = got
        poses.update(self._directional_idles(poses))
        self.player.set_frames(**poses)

    @staticmethod
    def _directional_idles(poses):
        """Standing poses for up and sideways, taken from the walk strips.

        ⚠️ **This needs no art.** A three-frame walk is contact / passing /
        contact, and the *passing* frame is the one with the legs together and
        the body upright — which is very nearly a standing pose already. Holding
        it is what stops a warrior spinning round to face the camera the moment
        it stops walking away.

        "down" is left alone on purpose: the painted `idle` is already a
        front-facing standing pose, and a real one beats a borrowed walk frame.
        """
        idles = {}
        for facing in ("up", "side"):
            strip = poses.get(f"walk_{facing}")
            if isinstance(strip, list) and len(strip) >= 2:
                idles[f"idle_{facing}"] = strip[1]
        return idles

    def _pose_or_strip(self, name, optional=False):
        strip = []
        while True:
            frame = load(f"sprites/{name}_{len(strip)}.png")
            if frame is None:
                break
            strip.append(frame)
        if strip:
            return strip
        if optional:
            return load(f"sprites/{name}.png")
        return self.game.assets.image(f"sprites/{name}.png")

    def _load_world_objects(self):
        doors, classrooms, open_regions = [], {}, []
        for obj in self.tilemap.objects():
            t = getattr(obj, "type", None)
            if t == "door":
                rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                doors.append(Door(rect, obj.properties["room_id"], obj.properties["color"]))
            elif t == "room":
                rtype = obj.properties.get("room_type")
                rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                if rtype == "classroom":
                    classrooms[obj.name] = {"id": obj.name, "rect": rect,
                                            "color": obj.properties.get("color")}
                elif rtype in OPEN_ROOM_TYPES:
                    open_regions.append(rect)
        return doors, classrooms, open_regions

    def _build_lockers(self):
        """One Return Locker per classroom — the book's actual destination (§5).

        Derived from the room rect rather than placed as a map object. The
        roadmap planned to put them in the .tmx, but the locker has to land in
        the gap `world/decor.py` leaves for it, so the map would have been a
        third file that must agree on a position decor already owns. One
        constant, `decor.LOCKER_SLOT`, is the whole contract — and "exactly one
        locker per classroom" stops being something the map data could get wrong.
        """
        return {rid: Locker(decor.LOCKER_SLOT.move(room["rect"].topleft),
                            rid, room["color"])
                for rid, room in self.classrooms.items()}

    def _collect_open_tiles(self, regions):
        """Walkable tile centers in corridor/entrance — where Emri can wake."""
        tw, th = self.tilemap.tw, self.tilemap.th
        tiles = []
        for reg in regions:
            for ty in range(reg.top // th, reg.bottom // th):
                for tx in range(reg.left // tw, reg.right // tw):
                    if (tx, ty) not in self.tilemap.solid:
                        tiles.append((tx * tw + tw // 2, ty * th + th // 2))
        return tiles

    def _build_classroom_tints(self):
        tints = {}
        for rid, room in self.classrooms.items():
            if not room["color"]:
                continue
            surf = pygame.Surface(room["rect"].size, pygame.SRCALPHA)
            surf.fill((*color_rgb(room["color"]), settings.ROOM_TINT_ALPHA))
            tints[rid] = surf
        return tints

    def _build_classroom_decor(self):
        """Bake each classroom's furniture once (see world/decor.py).

        Fills `self.decor_solids` on the way through: the furniture is solid now,
        and its rects come back room-local, so they are offset into world space
        here and never recomputed."""
        decorated, self.decor_solids = {}, []
        for rid, room in self.classrooms.items():
            rect = room["rect"]
            keep = [d.rect for d in self.doors if d.room_id == rid]
            # ⚠️ ...and wherever a monster stands. Furniture is baked *after* the
            # roster is spawned, so without this a teacher starts the level
            # embedded in a desk — it shoves itself out on the first step, which
            # looks exactly like the bug it is.
            keep += [m.hitbox for m in self.monsters if rect.collidepoint(m.pos)]
            doors = [r.move(-rect.x, -rect.y) for r in keep]
            surf, solids = decor.build(rect, room["color"], rid, doorways=doors)
            decorated[rid] = surf
            self.decor_solids += [r.move(rect.topleft) for r in solids]
        return decorated

    # ── collision provider (walls + locked doors) ────────────────────────---
    class _WithMonsters:
        """The player's collider: the world, plus every living monster.

        ⚠️ **Only the player uses this.** Monsters resolve against
        `PlayState.solid_rects` directly, because feeding them each other's
        hitboxes makes a monster collide with *itself* and jams the roster in
        place the moment two of them meet.

        ⚠️ **Nothing is excluded, and that was the bug.** This used to skip any
        monster the player was *already* touching, so that a monster which had
        walked onto the player could be escaped. But monsters close on you
        constantly, so contact is the normal state — and while touching, the
        collision was simply off and the player walked straight through.

        No exclusion is needed: `Entity._resolve` snaps a body **out** of a solid
        it starts inside, so being overlapped resolves outward rather than
        sealing. `PlayState._separate_from_monsters` then handles the other half
        — a monster walking onto a stationary player, where nothing the player
        does would trigger a resolve at all.
        """

        def __init__(self, play):
            self.play = play

        def solid_rects(self, box):
            rects = self.play.solid_rects(box)
            for m in self.play.monsters:
                if m.targetable and m.hitbox.colliderect(box):
                    rects.append(m.hitbox)
            return rects

    def wall_rects(self, box):
        """Walls and locked doors only — **no furniture**.

        What a projectile stops on. `solid_rects` grew to include desks so a
        body would bump into them, and that quietly meant a thrown book died
        against the nearest chair: the teachers hold rooms full of furniture,
        so they were mostly shooting their own classroom.
        """
        rects = self.tilemap.solid_rects(box)
        for d in self.doors:
            if d.blocks and d.rect.colliderect(box):
                rects.append(d.rect)
        return rects

    def solid_rects(self, box):
        rects = self.tilemap.solid_rects(box)
        for d in self.doors:
            if d.blocks and d.rect.colliderect(box):
                rects.append(d.rect)
        # Classroom furniture. Linear over every desk in the level, which is a
        # few dozen rects and cheaper than the quadtree that would replace it —
        # but if a level ever carries hundreds, this is the line to revisit.
        rects += [r for r in self.decor_solids if r.colliderect(box)]
        return rects

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from game.core.pause_state import PauseState
            self.game.push(PauseState(self.game))

    # ── update ─────────────────────────────────────────────────────────────
    def update(self, dt, inp):
        if self.won or self.lost:
            return
        self.elapsed += dt
        self.player.update(dt, inp, collider=self.player_collider)
        self._separate_from_monsters()
        self.camera.update(dt, self.player.pos)
        for p in self.pickups:
            p.update(dt)
        for m in self.monsters:
            m.update(dt, self.player, self)
        self._collect_windups()
        self._collect_casts()
        self._update_projectiles(dt)      # only their attacks hurt (fire/web)
        self._update_player_shots(dt)
        self._drain_sounds()
        if not self.player.alive:
            self._defeat()
            return
        if self.player.webbed:
            self.player.drain(settings.WEB_DPS * self.diff["dps"] * dt)
            if not self.player.alive:
                self._defeat()
                return
        self._update_duel(dt)
        self._update_scare(dt)
        self._collect_pickups()
        if inp.interact:
            self._interact()
        if inp.attack:
            if self.player.webbed:
                self.player.struggle_free()      # mash Space to break the web
            elif self.player.can_attack():
                self.player.start_swing()
                self._attack()
        if inp.power:
            self._use_power()
        self._update_zina(dt)
        if inp.mute:
            self.game.audio.toggle()
        self._tick_feedback(dt)
        self.hint = self._compute_hint()
        self._check_victory()

    def _update_duel(self, dt):
        """Emri's phase breaks: it leaves, help arrives, it comes back (§9).

        ⚠️ **The marks are one-way.** Emri does not regenerate, so a fraction it
        has already passed is popped off the list rather than compared again —
        otherwise sitting exactly on 0.5 would summon a room's worth of monsters
        one frame at a time.
        """
        if not self.duel or self.emri is None:
            return
        if self._adds:
            self._adds = [m for m in self._adds if m in self.monsters]
            if not self._adds:
                self.emri.dormant = False
                self._phase_grace = settings.EMRI_PHASE_GRACE
                self._announce("EMRI RETURNS!")
            return
        frac = self.emri.health / max(1e-6, self.emri.max_health)
        # ⚠️ **One phase break per crossing, however many marks it crossed.**
        # This used to call `_summon_help` once per mark, and a single heavy blow
        # can cross two — which spawned four monsters onto the *two* spawn
        # points, so two of them stood exactly underneath the other two. The
        # player killed the two they could see and Emri never came back, because
        # `_adds` still held the pair hiding inside them.
        # ⚠️ A grace period on top of the marks. Damage arrives in bursts, so
        # marks alone cannot space the breaks out — cross two in one flurry and
        # Emri looks like it is running away rather than fighting in phases.
        #
        # ⚠️ The marks are only *spent* when the break actually happens. Popping
        # them while the grace is running would silently throw the phase away
        # rather than delaying it, and a player who burst Emri down would get no
        # break at all.
        self._phase_grace = max(0.0, self._phase_grace - dt)
        if self._phase_grace > 0:
            return
        crossed = False
        while self._phase_marks and frac <= self._phase_marks[0]:
            self._phase_marks.pop(0)
            crossed = True
        if crossed:
            self._summon_help()

    def _spawn_spot(self, room, x, y):
        """A point inside `room` that a 44x44 monster can actually stand on.

        ⚠️ **This is what deadlocked a duel.** The spawn was
        `min(room.bottom - 60, player.y - 90)` with no *lower* bound — so a
        player standing near the top of the room put the summons above the
        room's own top edge, inside the wall. Unreachable monsters never die,
        `_adds` never empties, and Emri never comes back.
        """
        pad = settings.MONSTER_SIZE[0]
        x = min(max(x, room.x + pad), room.right - pad)
        y = min(max(y, room.y + pad), room.bottom - pad)
        box = pygame.Rect(0, 0, *settings.MONSTER_SIZE)
        # ...and if that lands on furniture or a wall anyway, walk it down the
        # room until it does not. The room is bigger than the search.
        for step in range(0, room.height, 24):
            box.center = (x, min(y + step, room.bottom - pad))
            if not self.solid_rects(box):
                return box.centerx, box.centery
        return room.centerx, room.centery

    def _summon_help(self):
        """Emri vanishes and sends two of the school's own after you."""
        room = self.classrooms[self.DUEL_ROOM]["rect"]
        makers = (make_fire_caster, make_web_caster)
        kinds = ("caster", "webber")
        self.emri.dormant = True
        for i in range(settings.EMRI_PHASE_ADDS):
            pick = random.randrange(len(makers))
            # ⚠️ Flanking the *player*, not the top of the room. Spawned at the
            # room's edge they arrived off-screen and the phase break read as
            # "the boss left and nothing happened".
            x = room.x + room.width * (0.22 + 0.56 * i)
            y = self.player.pos.y - 90
            add = makers[pick](*self._spawn_spot(room, x, y),
                               sprite=self.sprites[kinds[pick]])
            prefix, stances = self.monster_poses.get(kinds[pick], (None, ()))
            if stances:
                add.set_frames(idle=self.sprites[kinds[pick]],
                               **{n: _monster_pose(prefix, n) for n in stances})
            self.monsters.append(add)
            self._adds.append(add)
        self._announce("EMRI CALLS FOR HELP!", 2.2)
        self.game.audio.play_scare()
        self.camera.shake(4, 0.4)

    def _strip_for_duel(self):
        """Clear the level away and leave one room, one boss (§9).

        Called after the world is built rather than instead of building it — the
        map, the collision, the camera bounds and the room rects are all still
        wanted, and rebuilding a cut-down version of them is how the two paths
        drift apart.
        """
        room = self.classrooms.get(self.DUEL_ROOM) or \
            next(iter(self.classrooms.values()))
        rect = room["rect"]
        self.monsters.clear()
        self.pickups.clear()
        self.lockers.clear()
        # ⚠️ The furniture goes too. A duel against something that blinks to
        # arm's length is about spacing, and desks turn that into a scenery
        # problem — the boss can appear behind one, and you cannot back away in
        # a straight line.
        self.decor_solids = []
        self.classroom_decor.pop(self.DUEL_ROOM, None)

        # ⚠️ **The doors are sealed, not merely locked.** A locked door opens
        # with a key, and the duel used to hand out keys for its own summons —
        # so the player could unlock the classroom and walk out of the boss
        # fight. Keys no longer drop here, and this makes that belt-and-braces:
        # nothing in the duel can open a door.
        for d in self.doors:
            d.sealed = True
        self.player.pos.update(rect.centerx, rect.bottom - 70)
        self.camera.snap_to(self.player.pos)
        self.wake_emri()
        self.emri.pos.update(rect.centerx, rect.top + 80)
        self._emri_woke = True
        self._phase_marks = list(settings.EMRI_PHASE_MARKS)
        self._adds = []
        self._phase_grace = 0.0
        self._announce("THE LAST CLASSROOM — EMRI IS WAITING", 3.0)

    def _separate_from_monsters(self):
        """Push the player out of any monster standing on them.

        Monsters do not collide with the player when *they* move, so one can walk
        onto a player who is holding still — and a player holding still never
        calls `move_and_collide`, so nothing would ever resolve it. The push is
        along the **shallowest** axis, which is the shortest way out and the one
        that does not fling the player across the room, and it goes through
        `displace` so it still respects walls.
        """
        for m in self.monsters:
            if not m.targetable:
                continue
            box, hb = self.player.hitbox, m.hitbox
            if not box.colliderect(hb):
                continue
            dx, dy = hb.centerx - box.centerx, hb.centery - box.centery
            overlap_x = (box.width + hb.width) / 2 - abs(dx)
            overlap_y = (box.height + hb.height) / 2 - abs(dy)
            if overlap_x <= overlap_y:
                push = pygame.Vector2(-overlap_x if dx > 0 else overlap_x, 0)
            else:
                push = pygame.Vector2(0, -overlap_y if dy > 0 else overlap_y)
            self.player.displace(push, self)      # walls, not monsters: no loop

    def _scale_monster_health(self):
        """Apply difficulty's `hp` dial to the roster.

        ⚠️ Done here rather than in the spawner because the spawner has no idea
        what difficulty is running, and threading one through it would put a
        gameplay dial into map loading. Scaled at full health, before anything
        can have been hit.
        """
        mult = self.diff.get("hp", 1.0)
        for m in self.monsters:
            m.max_health *= mult
            m.health = m.max_health

    class _Splash:
        """A one-shot sprite that fades where something died.

        Deliberately three fields and no module. `systems/effects.py` was a
        general pool for exactly one caller and was deleted with it (§6); this is
        one caller again, and a list of these is cheaper than the pool was.
        """
        LIFE = 0.38

        def __init__(self, sprite, pos):
            self.sprite = sprite
            self.pos = pygame.Vector2(pos)
            self.life = self.LIFE

        @property
        def dead(self):
            return self.life <= 0

        def update(self, dt):
            self.life -= dt

        def draw(self, surface, camera):
            # ⚠️ **Not `set_alpha`.** On a surface with per-pixel alpha it throws
            # the mask away and fades the whole *rectangle* instead — which is
            # the box that showed up around every fireball impact and every
            # Zina bite. Multiplying into the existing alpha keeps the shape.
            img = self.sprite.copy()
            fade = int(255 * max(0.0, self.life / self.LIFE))
            img.fill((255, 255, 255, fade), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(img, img.get_rect(
                center=(self.pos.x - round(camera.offset.x),
                        self.pos.y - round(camera.offset.y))))

    def _drain_sounds(self):
        """Play whatever the monsters asked for this frame, once each.

        Entities have no reference to the audio system — they set
        `sound_request` and it is cleared here. Emri's blink and the player's
        hurt grunt use it; the growl still comes from `_update_scare`, which is a
        *cooldown* on a condition rather than a one-shot event.

        ⚠️ Drained after the projectiles land but **before** the defeat check, or
        the killing blow is the one hit that never makes a sound. Anything raised
        later in the frame — `web_break`, from mashing Space — is played on the
        next one instead, which is 16ms and inaudible."""
        for e in [self.player] + self.monsters:
            if e.sound_request:
                self.game.audio.play(e.sound_request)
                e.sound_request = None

    def _collect_windups(self):
        """Announce a caster that has just started charging.

        ⚠️ The cast sound plays **here, not when the projectile spawns**. It is
        the audible half of the tell, and a warning that arrives with the shot is
        not a warning. Each caster sounds different, so it also says *which*
        monster woke up before it is on screen.
        """
        for m in self.monsters:
            if getattr(m, "cast_started", False):
                m.cast_started = False
                self.game.audio.play_voiced(
                    m.voice, "throw",
                    default=CAST_SOUND.get(getattr(m, "cast_kind", ""), "fire_cast"))

    def _collect_casts(self):
        """Spawn the projectile any caster requested this frame."""
        for m in self.monsters:
            req = getattr(m, "cast_request", None)
            if req is None:
                continue
            spawn = m.pos + pygame.Vector2(req) * 20      # emerge in front
            kind = getattr(m, "cast_kind", "fire")
            if kind == "web":
                self.projectiles.append(WebProjectile(spawn.x, spawn.y, req,
                                                     sprite=self.web_sprite))
            elif kind == "tome":
                dmg = settings.TOME_DAMAGE * self.diff["dps"]
                self.projectiles.append(DarkTome(spawn.x, spawn.y, req, dmg,
                                                 sprite=self.tome_sprite))
            elif kind == "bolt":
                dmg = settings.BOLT_DAMAGE * self.diff["dps"]
                self.projectiles.append(LightBolt(spawn.x, spawn.y, req, dmg))
            else:
                dmg = settings.FIREBALL_DAMAGE * self.diff["dps"]
                self.projectiles.append(Fireball(spawn.x, spawn.y, req, dmg,
                                                 sprite=self.fire_sprite))
            m.cast_request = None

    def _update_projectiles(self, dt):
        pbox = self.player.hitbox
        for f in list(self.projectiles):
            f.update(dt)
            if f.hitbox.colliderect(pbox):
                f.on_hit(self.player)             # damage or entangle
                art = load(f"sprites/{getattr(f, 'impact_art', '')}.png")
                if art:
                    self.splashes.append(self._Splash(art, f.pos))
                self.game.audio.play(getattr(f, "hit_sound", ""))
                self.camera.shake(2.5, 0.1)
                f.dead = True
            elif self.wall_rects(f.hitbox):       # a wall or a locked door only
                f.dead = True
            if f.dead:
                self.projectiles.remove(f)

    def _update_scare(self, dt):
        """Noise when a monster first locks onto the player (with a cooldown).

        A monster with a voice pack says its own line; everything else growls.
        The female teacher has no `spotplayer` take yet and falls back — which
        is exactly what `play_voiced`'s default is for."""
        self._scare_cd = max(0.0, self._scare_cd - dt)
        if self._scare_cd > 0:
            return
        spotted = next((m for m in self.monsters if m.newly_chasing), None)
        if spotted is None:
            return
        self.game.audio.play_voiced(spotted.voice, "spotplayer", default="monster")
        self._scare_cd = 2.5

    def _collect_pickups(self):
        pbox = self.player.hitbox
        for p in list(self.pickups):
            if p.guarded or not pbox.colliderect(p.hitbox):
                continue
            if p.item_type == "health":
                if self.player.health < settings.PLAYER_MAX_HEALTH:
                    self.player.heal(settings.HEALTH_BOTTLE_HEAL * self.diff["potion"])
                    self.game.audio.play("potion")
                    self.pickups.remove(p)
                continue
            if self.inventory.add(p.item_type, p.variant):
                self.game.audio.play("pickup")
                self.pickups.remove(p)
                self.bus.emit(Events.ITEM_COLLECTED, item_type=p.item_type, variant=p.variant)

    def _attack(self):
        """Swing, or throw — whichever the chosen warrior carries."""
        if self.player.throws:
            self._throw_knife()
            return
        # on the swing, not on the hit: a miss still swings, and a weapon that
        # only makes a sound when it connects reads as having no weight
        self.game.audio.play("sword_swing")
        target = self._nearest_monster(self.player.reach)
        if not target:
            return
        self.camera.shake(3, 0.15)
        self._hurt_monster(target, self.player.damage, self.player.pos)

    def _hurt_monster(self, target, damage, from_pos, direction=None):
        """Land a blow: the impact, the victim's reaction, and the bookkeeping.

        Two sounds on purpose. `hit_flesh` is the *weapon connecting* and has to
        fire on the exact frame for the hit to feel landed; the voice is the
        monster reacting to it, and is allowed to be slower and to be skipped
        while it is still talking."""
        self.game.audio.play("hit_flesh")
        self.game.audio.play_voiced(target.voice, "hit")
        if target.take_hit(from_pos, damage, direction=direction):
            self._on_monster_died(target)

    def _throw_knife(self):
        """Unlimited, but paced by a cooldown and aimed where you face."""
        aim = pygame.Vector2(self.player.facing, 0)
        target = self._nearest_monster(settings.KNIFE_RANGE)
        if target is not None:          # gentle aim assist toward a real threat
            to_target = target.pos - self.player.pos
            if to_target.length() > 0 and to_target.x * self.player.facing >= 0:
                aim = to_target.normalize()
        self.player_shots.append(
            Knife(self.player.pos.x, self.player.pos.y - 6, aim,
                  self.player.damage, sprite=self.knife_sprite))
        self.game.audio.play("knife_throw")     # silent until the file lands
        self.camera.shake(1.5, 0.08)

    def _update_player_shots(self, dt):
        for k in list(self.player_shots):
            k.update(dt)
            for m in self.monsters:
                if m.targetable and k.hitbox.colliderect(m.hitbox):
                    # the knife carries its own damage and travel direction, so
                    # it lands the blow itself — but the noise is shared
                    self.game.audio.play("hit_flesh")
                    self.game.audio.play_voiced(m.voice, "hit")
                    if k.on_hit(m):
                        self._on_monster_died(m)
                    break
            if not k.dead and self.wall_rects(k.hitbox):
                k.dead = True
            if k.dead:
                self.player_shots.remove(k)

    # ── the warrior's active power ───────────────────────────────────────--
    def _use_power(self):
        """Z — Roni sends Zina at the nearest monster. One bite, one charge."""
        if self.player.power != "zina" or self.zina is not None:
            return
        if self.player.power_charges <= 0:
            self._announce("Zina is out of bites!", 1.4)
            return
        target = self._nearest_monster(settings.ZINA_RANGE)
        if target is None:
            self._announce("Nothing close enough for Zina", 1.4)
            return          # a charge is only spent when she actually goes
        self.player.spend_power()
        self.zina = Zina(self.player, target, sprite=self.zina_sprite,
                         painted_bite=bool(self.bite_sprite))
        self.camera.shake(2.0, 0.12)

    def _update_zina(self, dt):
        if self.zina is None:
            return
        self.zina.update(dt)
        if self.zina.sound_request:
            self.game.audio.play(self.zina.sound_request)
            self.zina.sound_request = None
        victim = self.zina.killed
        if victim is not None and not victim.dead:
            if self.bite_sprite:
                self.splashes.append(self._Splash(self.bite_sprite, victim.pos))
            if victim.boss:
                # ⚠️ A bite *wounds* a boss rather than killing it — and for a
                # flat number of pips, not a share of its health. As a share it
                # took a third of the fight in one bite, and it rescaled itself
                # every time `EMRI_HITS` moved, so tuning the boss silently
                # retuned the dog.
                if victim.take_hit(self.zina.pos, settings.ZINA_BOSS_DAMAGE):
                    self._on_monster_died(victim)
            else:
                victim.dead = True                  # a bite kills outright
                self._on_monster_died(victim)
        if self.zina.done:
            self.zina = None

    def _on_monster_died(self, monster):
        """Shared death bookkeeping, whether by sword or by Zina."""
        if monster in self.monsters:
            self.monsters.remove(monster)
        self.kills += 1
        self.game.audio.play_voiced(monster.voice, "die", default="monster_die")
        self._drop_key(monster)
        if monster is self.emri:
            self.emri = None
            self._announce("EMRI IS BANISHED!")
            self.game.audio.play_fanfare()
            return
        if monster.drops:                           # it was carrying the book
            self._drop_book(monster)
        if monster.guards:                          # (older maps) free a placed book
            for p in self.pickups:
                if p.item_type == "book" and p.variant == monster.guards:
                    p.guarded = False

    def _drop_key(self, monster):
        """The first `KEYS_FROM_KILLS` kills each hand over a door key.

        ⚠️ **It drops on the floor to be walked over**, not into the pack. Handing
        it over silently meant a key you never saw — the counter ticked and
        nothing else happened, so the reward for a fight was a number changing in
        a corner. Dropped, it is a thing on the ground where the monster was.

        ⚠️ **Never in the duel.** A key opens a classroom door, and the duel's
        arena *is* a locked classroom — so a key dropped by one of Emri's summons
        let the player unlock the door and walk out of the boss fight.
        """
        if self.duel or self.keys_earned >= settings.KEYS_FROM_KILLS:
            return
        self.keys_earned += 1
        key = Pickup(monster.pos.x, monster.pos.y, "key")
        key.shining = True          # it was won, like the books
        self.pickups.append(key)

    def _drop_book(self, monster):
        """The classroom's book falls where its teacher did (§5).

        This is the whole reason the books left the map. Lying in a corridor
        behind a `guarded` flag, a book was visible and inert from the first
        minute and the fight that freed it happened in another room entirely.
        Dropped, the reward appears **in the room, at the moment the room is
        won**, and the walk to the locker is the victory lap."""
        book = Pickup(monster.pos.x, monster.pos.y, "book", monster.drops)
        book.shining = True         # it is a prize; it should say so
        self.pickups.append(book)

    # ── Emri, the boss ───────────────────────────────────────────────────--
    def wake_emri(self):
        """Summon the blink boss.

        Nothing calls this during level 1 any more: Emri overwhelmed the opening
        level and vanished faster than a player could answer it. The behaviour
        stays built and tested, waiting on the boss level in the roadmap — a
        duel in a hidden classroom once every book is home.
        """
        if self.emri is not None:
            return
        pos = self._pick_spawn_point()
        self.emri = make_emri(pos[0], pos[1], sprite=self.sprites["emri"])
        # Emri is not spawned by the map, so its poses are installed here rather
        # than through `spawn_monsters`.
        emri_poses = {n: _monster_pose("emri", n)
                      for n in ("walk", "walk_up", "walk_side", "cast", "hurt")}
        if any(emri_poses.values()):
            self.emri.set_frames(idle=self.sprites["emri"],
                                 **{k: v for k, v in emri_poses.items() if v})
        self.monsters.append(self.emri)
        self._announce("EMRI AWAKENS — it strikes from nowhere!")
        self.game.audio.play_scare()
        self.camera.shake(5, 0.5)

    def _announce(self, text, seconds=2.6):
        self.banner = [text, seconds]

    def _tick_feedback(self, dt):
        """Age the cosmetic book-return feedback (particles, glow, tint pulse)."""
        for a in self.ambience:
            a.update(dt)
        for sp in self.splashes:
            sp.update(dt)
        self.splashes = [sp for sp in self.splashes if not sp.dead]
        self.book_flash = max(0.0, self.book_flash - dt)
        if self.banner:
            self.banner[1] -= dt
            if self.banner[1] <= 0:
                self.banner = None

    def _on_book_returned(self, room_id=None, color=None, **_):
        """Roadmap §6 — the payoff beat: the chime, the shake, the HUD counter.

        ⚠️ **No particle burst and no room-colour pulse.** Both were here and
        both were wrong for the same reason the confetti on the victory screen
        was: a shower of coloured sparks over a rising icon reads as a mobile
        game's reward animation, dropped into a dark school at night. What is
        left is the part that carries weight without changing register — the
        building shudders, the chime lands, the counter ticks."""
        self.books_home += 1
        self.game.audio.play_success()
        self.book_flash = settings.BOOK_FLASH_TIME
        self.camera.shake(settings.BOOK_SHAKE_MAG, settings.BOOK_SHAKE_TIME)

    def _pick_spawn_point(self):
        far = [t for t in self.open_tiles if self.player.pos.distance_to(t) > 220]
        return random.choice(far or self.open_tiles or [(self.tilemap.px_w / 2, self.tilemap.px_h / 2)])

    # ── interaction ──────────────────────────────────────────────────────--
    def _interact(self):
        door = self._nearest_locked_door()
        if door and getattr(door, "sealed", False):
            self._announce("THE DOOR WILL NOT BUDGE", 1.4)
            return
        if door:
            if door.try_unlock(self.inventory):
                self.game.audio.play("door_unlock")
                self.bus.emit(Events.DOOR_UNLOCKED, room_id=door.room_id)
            return
        locker = self._nearest_locker()
        if locker is None or not self.room_cleared(locker.room_id):
            return                      # `_compute_hint` says which of the two
        if self.inventory.remove("book", locker.color):
            locker.filled = True
            self.game.audio.play("locker_open")   # silent until the file lands
            self.bus.emit(Events.BOOK_RETURNED,
                          room_id=locker.room_id, color=locker.color)

    def room_cleared(self, room_id):
        """No living monster stands inside the room (§5).

        Deliberately *any* monster, not just the one posted here at spawn. A
        webber chased in from the corridor still blocks the drop, which reads
        instantly — "there's something in here with me" — where "only the
        original guardian counts" would leave a monster breathing down your neck
        while the delivery quietly worked. Nothing respawns, so this can never
        deadlock: whatever walked in can be killed.
        """
        rect = self.classrooms[room_id]["rect"]
        return not any(rect.collidepoint(m.pos) for m in self.monsters)

    def _nearest_monster(self, within):
        """Nearest *targetable* monster — Emri is untouchable while it's gone."""
        best, chosen = within, None
        for m in self.monsters:
            if not m.targetable:
                continue
            d = m.dist_to(self.player.pos)
            if d <= best:
                best, chosen = d, m
        return chosen

    def _nearest_locker(self):
        best, chosen = settings.INTERACT_RANGE, None
        for locker in self.lockers.values():
            d = locker.dist_to(self.player.pos)
            if d <= best:
                best, chosen = d, locker
        return chosen

    def _nearest_locked_door(self):
        best, chosen = settings.INTERACT_RANGE, None
        for d in self.doors:
            if d.locked and d.dist_to(self.player.pos) <= best:
                best, chosen = d.dist_to(self.player.pos), d
        return chosen

    def _classroom_at(self, point):
        for room in self.classrooms.values():
            if room["rect"].collidepoint(point):
                return room
        return None

    def _compute_hint(self):
        if self.player.webbed:
            return None      # the web prompt is drawn separately
        monster = self._nearest_monster(self.player.reach)
        if monster:
            verb = "Throw at" if self.player.throws else "Attack"
            return f"[Space] {verb} the {monster.name}!"
        door = self._nearest_locked_door()
        if door:
            return "[E] Unlock door" if self.inventory.count("key") else "[E] Need a key"
        locker = self._nearest_locker()
        if locker and self.inventory.find("book", locker.color) >= 0:
            if not self.room_cleared(locker.room_id):
                return "Clear the room first!"
            return "[E] Return book"
        room = self._classroom_at(self.player.pos)
        if room:
            if self.inventory.find("book", room["color"]) >= 0:
                return "Put the book in the locker"
            if self.inventory.count("book"):
                return "Wrong classroom for this book"
        return None

    # ── outcomes ─────────────────────────────────────────────────────────--
    def _check_victory(self):
        if self.won:
            return
        if self.duel:
            # ⚠️ Won when Emri is *gone*, not when the roster empties: it starts
            # the fight untargetable and away, and an empty roster on frame one
            # would hand the player the win before the boss arrived.
            if self.emri is None and self._emri_woke:
                self.won = True
                from game.core.victory_state import VictoryState
                self.game.push(VictoryState(self.game, self.elapsed))
            return
        if self.quests.is_done("return_books"):
            self.won = True
            from game.core.level_complete_state import LevelCompleteState
            self.game.push(LevelCompleteState(self.game, self.elapsed,
                                              charges=self.player.power_charges))

    def _defeat(self):
        self.lost = True
        from game.core.defeat_state import DefeatState
        self.game.push(DefeatState(self.game))

    def _counters(self):
        if self.duel:
            return []          # no keys, no books — there is only the boss
        return [("key", *self.quests.get("find_keys")),
                ("book", *self.quests.get("return_books"))]

    # ── draw ─────────────────────────────────────────────────────────────--
    def draw(self, surface):
        surface.fill(settings.BG_COLOR)
        self.tilemap.draw(surface, self.camera)
        self._draw_classroom_decor(surface)
        for a in self.ambience:
            a.draw(surface, self.camera)
        self._draw_classroom_tints(surface)
        for d in self.doors:
            d.draw(surface, self.camera)
        for locker in self.lockers.values():
            locker.draw(surface, self.camera)
        for p in self.pickups:
            p.draw(surface, self.camera)
        for m in self.monsters:
            m.draw(surface, self.camera)
        for sp in self.splashes:       # over the monster, where the bite landed
            sp.draw(surface, self.camera)
        for f in self.projectiles:
            f.draw(surface, self.camera)
        for k in self.player_shots:
            k.draw(surface, self.camera)
        self.player.draw(surface, self.camera)
        if self.zina:
            self.zina.draw(surface, self.camera)
        if self.player.hurt_flash > 0:
            self._draw_hurt_flash(surface)
        self.hud.draw(surface, self.player, self._counters(), self.hint, self.elapsed,
                      flashes={"book": self.book_flash / settings.BOOK_FLASH_TIME})
        if self.player.webbed:
            self._draw_web_prompt(surface)
        if self.banner:
            self._draw_banner(surface)

    def _draw_classroom_decor(self, surface):
        off = self.camera.offset
        for rid, room in self.classrooms.items():
            surf = self.classroom_decor.get(rid)
            if surf:
                surface.blit(surf, (room["rect"].x - off.x, room["rect"].y - off.y))

    def _draw_classroom_tints(self, surface):
        off = self.camera.offset
        for rid, room in self.classrooms.items():
            pos = (room["rect"].x - off.x, room["rect"].y - off.y)
            surf = self.classroom_tints.get(rid)
            if surf:
                surface.blit(surf, pos)

    def _draw_hurt_flash(self, surface):
        overlay = pygame.Surface(settings.INTERNAL_RES, pygame.SRCALPHA)
        overlay.fill((200, 30, 30, 70))
        surface.blit(overlay, (0, 0))

    def _draw_banner(self, surface):
        """A short centered callout — the boss arriving, or being banished."""
        text, left = self.banner
        w = settings.INTERNAL_RES[0]
        font = self.game.assets.font(None, 20)
        surf = font.render(text, True, (255, 236, 180))
        x = (w - surf.get_width()) // 2
        y = 54
        panel = pygame.Surface((surf.get_width() + 20, surf.get_height() + 10),
                               pygame.SRCALPHA)
        panel.fill((60, 8, 14, 205))
        surface.blit(panel, (x - 10, y - 5))
        pygame.draw.rect(surface, (215, 70, 60),
                         (x - 10, y - 5, surf.get_width() + 20, surf.get_height() + 10), 1)
        surface.blit(surf, (x, y))

    def _draw_web_prompt(self, surface):
        w, h = settings.INTERNAL_RES
        font = self.game.assets.font(None, 22)
        small = self.game.assets.font(None, 16)
        msg = font.render("STUCK IN THE WEB!", True, (255, 240, 255))
        sub = small.render(f"Mash SPACE to break free!   {self.player.struggle} left",
                           True, (230, 230, 240))
        y = h // 2 - 30
        for surf in (msg, sub):
            x = (w - surf.get_width()) // 2
            bg = pygame.Rect(x - 8, y - 3, surf.get_width() + 16, surf.get_height() + 6)
            panel = pygame.Surface(bg.size, pygame.SRCALPHA); panel.fill((20, 10, 30, 170))
            surface.blit(panel, bg.topleft)
            surface.blit(surf, (x, y))
            y += surf.get_height() + 8
