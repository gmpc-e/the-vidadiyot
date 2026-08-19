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
from game.core.assets import ASSETS
from game.world.tilemap import TileMap
from game.world.palette import color_rgb
from game.world import decor
from game.world.spawner import spawn_pickups, spawn_monsters
from game.entities.player import Player
from game.entities.monster import make_emri
from game.entities.fireball import Fireball
from game.entities.web import WebProjectile
from game.entities.knife import Knife
from game.entities.lightbolt import LightBolt
from game.entities.zina import Zina
from game.entities import warriors
from game.entities.interactable import Door
from game.systems.inventory import Inventory
from game.systems.quests import QuestManager
from game.systems.eventbus import Events
from game.systems.effects import Effects
from game.systems import difficulty
from game.ui.hud import HUD

MAP_PATH = os.path.join(ASSETS, "maps", "school_slice.tmx")
QUESTS_PATH = os.path.join(os.path.dirname(ASSETS), "data", "quests.json")
OPEN_ROOM_TYPES = ("corridor", "entrance")     # open areas Emri can wake in


class PlayState(State):
    def enter(self):
        self.bus = self.game.bus
        self.tilemap = TileMap(MAP_PATH)
        self.camera = Camera(settings.INTERNAL_RES)
        self.camera.set_world_bounds(pygame.Rect(0, 0, self.tilemap.px_w, self.tilemap.px_h))

        start = self.tilemap.object_by_name("player_start")
        px = (start.x, start.y) if start else (self.tilemap.px_w / 2, self.tilemap.px_h / 2)
        self.warrior = warriors.get(getattr(self.game, "warrior", warriors.DEFAULT_ID))
        self.player = Player(*px, warrior=self.warrior)
        self._load_warrior_frames()
        self.camera.snap_to(self.player.pos)

        self.doors, self.classrooms, open_regions = self._load_world_objects()
        self.inventory = Inventory(settings.CARRY_CAPACITY)
        self.quests = QuestManager.from_file(self.bus, QUESTS_PATH)
        self.pickups = spawn_pickups(self.tilemap)
        self.sprites = {"webber": self.game.assets.image("sprites/snir.png"),
                        "caster": self.game.assets.image("sprites/terror.png"),
                        "emri": self.game.assets.image("sprites/emri.png")}
        self.monsters = spawn_monsters(self.tilemap, self.pickups, self.sprites)
        self.projectiles = []        # monster casts, aimed at the player
        self.player_shots = []       # the player's own thrown weapons
        self.hud = HUD(self.game.assets, self.quests, self.inventory)
        self.hint = None
        self.effects = Effects()
        self.zina = None                     # Roni's dog while she is out
        self.zina_sprite = self.game.assets.image("sprites/zina.png")
        self.knife_sprite = self.game.assets.image("sprites/roni_knife.png")
        self.emri = None                     # the boss, once it has woken
        self.books_home = 0
        self.banner = None                   # (text, seconds left)
        self.book_flash = 0.0        # HUD counter glow, seconds remaining (§6)
        self.tint_pulses = {}        # room_id -> seconds remaining of its pulse

        self.elapsed = 0.0
        self.won = False
        self.lost = False
        self.kills = 0
        self._scare_cd = 0.0
        self.diff = difficulty.get(self.game.difficulty)
        self.open_tiles = self._collect_open_tiles(open_regions)
        self.classroom_tints = self._build_classroom_tints()
        self.classroom_pulses = self._build_classroom_pulses()
        self.classroom_decor = self._build_classroom_decor()

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
        """Load the chosen warrior's four painted poses into the player."""
        prefix = self.warrior["sprites"]
        img = self.game.assets.image
        self.player.set_frames(*(img(f"sprites/{prefix}_{state}.png")
                                 for state in ("idle", "walk", "attack", "hurt")))

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
            surf.fill((*color_rgb(room["color"]), 38))
            tints[rid] = surf
        return tints

    def _build_classroom_pulses(self):
        """Full-strength room tints, blitted at a fading alpha on a book return."""
        pulses = {}
        for rid, room in self.classrooms.items():
            if not room["color"]:
                continue
            surf = pygame.Surface(room["rect"].size)
            surf.fill(color_rgb(room["color"]))
            pulses[rid] = surf
        return pulses

    def _build_classroom_decor(self):
        """Bake each classroom's furniture once (see world/decor.py)."""
        return {rid: decor.build(room["rect"], room["color"], rid)
                for rid, room in self.classrooms.items()}

    # ── collision provider (walls + locked doors) ────────────────────────---
    def solid_rects(self, box):
        rects = self.tilemap.solid_rects(box)
        for d in self.doors:
            if d.blocks and d.rect.colliderect(box):
                rects.append(d.rect)
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
        self.player.update(dt, inp, collider=self)
        self.camera.update(dt, self.player.pos)
        for p in self.pickups:
            p.update(dt)
        for m in self.monsters:
            m.update(dt, self.player, self)
        self._collect_casts()
        self._update_projectiles(dt)      # only their attacks hurt (fire/web)
        self._update_player_shots(dt)
        if not self.player.alive:
            self._defeat()
            return
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

    def _collect_casts(self):
        """Spawn the projectile any caster requested this frame."""
        for m in self.monsters:
            req = getattr(m, "cast_request", None)
            if req is None:
                continue
            spawn = m.pos + pygame.Vector2(req) * 20      # emerge in front
            kind = getattr(m, "cast_kind", "fire")
            if kind == "web":
                self.projectiles.append(WebProjectile(spawn.x, spawn.y, req))
            elif kind == "bolt":
                dmg = settings.BOLT_DAMAGE * self.diff["dps"]
                self.projectiles.append(LightBolt(spawn.x, spawn.y, req, dmg))
            else:
                dmg = settings.FIREBALL_DAMAGE * self.diff["dps"]
                self.projectiles.append(Fireball(spawn.x, spawn.y, req, dmg))
            m.cast_request = None

    def _update_projectiles(self, dt):
        pbox = self.player.hitbox
        for f in list(self.projectiles):
            f.update(dt)
            if f.hitbox.colliderect(pbox):
                f.on_hit(self.player)             # damage or entangle
                self.camera.shake(2.5, 0.1)
                f.dead = True
            elif self.solid_rects(f.hitbox):      # hit a wall / locked door
                f.dead = True
            if f.dead:
                self.projectiles.remove(f)

    def _update_scare(self, dt):
        """Growl when a monster first locks onto the player (with a cooldown)."""
        self._scare_cd = max(0.0, self._scare_cd - dt)
        if self._scare_cd <= 0 and any(m.newly_chasing for m in self.monsters):
            self.game.audio.play_scare()
            self._scare_cd = 2.5

    def _collect_pickups(self):
        pbox = self.player.hitbox
        for p in list(self.pickups):
            if p.guarded or not pbox.colliderect(p.hitbox):
                continue
            if p.item_type == "health":
                if self.player.health < settings.PLAYER_MAX_HEALTH:
                    self.player.heal(settings.HEALTH_BOTTLE_HEAL * self.diff["potion"])
                    self.pickups.remove(p)
                continue
            if self.inventory.add(p.item_type, p.variant):
                self.pickups.remove(p)
                self.bus.emit(Events.ITEM_COLLECTED, item_type=p.item_type, variant=p.variant)

    def _attack(self):
        """Swing, or throw — whichever the chosen warrior carries."""
        if self.player.throws:
            self._throw_knife()
            return
        target = self._nearest_monster(self.player.reach)
        if not target:
            return
        self.camera.shake(3, 0.15)
        if target.take_hit(self.player.pos, self.player.damage):
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
        self.camera.shake(1.5, 0.08)

    def _update_player_shots(self, dt):
        for k in list(self.player_shots):
            k.update(dt)
            for m in self.monsters:
                if m.targetable and k.hitbox.colliderect(m.hitbox):
                    if k.on_hit(m):
                        self._on_monster_died(m)
                    break
            if not k.dead and self.solid_rects(k.hitbox):
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
        self.zina = Zina(self.player, target, sprite=self.zina_sprite)
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
            victim.dead = True                      # a bite kills outright
            self._on_monster_died(victim)
        if self.zina.done:
            self.zina = None

    def _on_monster_died(self, monster):
        """Shared death bookkeeping, whether by sword or by Zina."""
        if monster in self.monsters:
            self.monsters.remove(monster)
        self.kills += 1
        if monster is self.emri:
            self.emri = None
            self._announce("EMRI IS BANISHED!")
            self.game.audio.play_fanfare()
            return
        if monster.guards:                          # free the guarded book
            for p in self.pickups:
                if p.item_type == "book" and p.variant == monster.guards:
                    p.guarded = False

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
        self.monsters.append(self.emri)
        self._announce("EMRI AWAKENS — it strikes from nowhere!")
        self.game.audio.play_scare()
        self.camera.shake(5, 0.5)

    def _announce(self, text, seconds=2.6):
        self.banner = [text, seconds]

    def _tick_feedback(self, dt):
        """Age the cosmetic book-return feedback (particles, glow, tint pulse)."""
        self.effects.update(dt)
        self.book_flash = max(0.0, self.book_flash - dt)
        if self.banner:
            self.banner[1] -= dt
            if self.banner[1] <= 0:
                self.banner = None
        for rid in list(self.tint_pulses):
            self.tint_pulses[rid] -= dt
            if self.tint_pulses[rid] <= 0:
                del self.tint_pulses[rid]

    def _on_book_returned(self, room_id=None, color=None, **_):
        """Roadmap §6 — the payoff beat: chime, sparkles, tint pulse, HUD glow."""
        self.books_home += 1
        self.game.audio.play_success()
        self.effects.book_returned(self.player.pos, color_rgb(color))
        self.book_flash = settings.BOOK_FLASH_TIME
        if room_id in self.classroom_pulses:
            self.tint_pulses[room_id] = settings.BOOK_TINT_TIME
        self.camera.shake(settings.BOOK_SHAKE_MAG, settings.BOOK_SHAKE_TIME)

    def _pick_spawn_point(self):
        far = [t for t in self.open_tiles if self.player.pos.distance_to(t) > 220]
        return random.choice(far or self.open_tiles or [(self.tilemap.px_w / 2, self.tilemap.px_h / 2)])

    # ── interaction ──────────────────────────────────────────────────────--
    def _interact(self):
        door = self._nearest_locked_door()
        if door:
            if door.try_unlock(self.inventory):
                self.bus.emit(Events.DOOR_UNLOCKED, room_id=door.room_id)
            return
        room = self._classroom_at(self.player.pos)
        if room and self.inventory.remove("book", room["color"]):
            self.bus.emit(Events.BOOK_RETURNED, room_id=room["id"], color=room["color"])

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
        room = self._classroom_at(self.player.pos)
        if room:
            if self.inventory.find("book", room["color"]) >= 0:
                return "[E] Return book"
            if self.inventory.count("book"):
                return "Wrong classroom for this book"
        return None

    # ── outcomes ─────────────────────────────────────────────────────────--
    def _check_victory(self):
        if not self.won and self.quests.is_done("return_books"):
            self.won = True
            from game.core.level_complete_state import LevelCompleteState
            self.game.push(LevelCompleteState(self.game, self.elapsed))

    def _defeat(self):
        self.lost = True
        from game.core.defeat_state import DefeatState
        self.game.push(DefeatState(self.game))

    def _counters(self):
        return [("key", *self.quests.get("find_keys")),
                ("book", *self.quests.get("return_books"))]

    # ── draw ─────────────────────────────────────────────────────────────--
    def draw(self, surface):
        surface.fill(settings.BG_COLOR)
        self.tilemap.draw(surface, self.camera)
        self._draw_classroom_decor(surface)
        self._draw_classroom_tints(surface)
        for d in self.doors:
            d.draw(surface, self.camera)
        for p in self.pickups:
            p.draw(surface, self.camera)
        for m in self.monsters:
            m.draw(surface, self.camera)
        for f in self.projectiles:
            f.draw(surface, self.camera)
        for k in self.player_shots:
            k.draw(surface, self.camera)
        self.player.draw(surface, self.camera)
        if self.zina:
            self.zina.draw(surface, self.camera)
        self.effects.draw(surface, self.camera)
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
            pulse = self.tint_pulses.get(rid)
            if pulse:      # the room flushes to its own color, then fades back
                glow = self.classroom_pulses[rid]
                glow.set_alpha(int(settings.BOOK_TINT_ALPHA * pulse / settings.BOOK_TINT_TIME))
                surface.blit(glow, pos)

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
