"""Monster: a lively guardian / hunter creature (combat model, doc §2.11).

Two modes:
- "guard"  — idles near its home post (wandering, not static) until the player
             comes within aggro range, then chases. Starts guarding a book.
- "hunt"   — a respawned hunter with no post: it *searches* by wandering toward
             the player's area, locking into a chase once close.

Movement is deliberately non-linear (wander targets + a sideways weave while
chasing) so the creature feels alive. Strength = hits to kill. Speed is per
instance so each respawn can be faster.
"""
import math
import random
import pygame

import settings
from game.entities.entity import Entity


class Monster(Entity):
    #: A boss survives what kills an ordinary monster outright — Zina's bite.
    boss = False

    def __init__(self, x, y, hits=None, guards=None, sprite=None, drops=None,
                 voice=None,
                 name="Vidadiya", mode="guard", speed=None):
        w, h = settings.MONSTER_SIZE
        super().__init__(x, y, w, h)
        self.max_health = hits if hits is not None else settings.MONSTER_HITS
        self.health = self.max_health
        self.guards = guards
        self.name = name
        self.mode = mode
        self.speed = speed if speed is not None else settings.MONSTER_SPEED
        self.sprite = sprite
        self.home = pygame.Vector2(x, y)
        self.flash = 0.0
        # Seconds of *hurt pose* left. Separate from `flash` on purpose — see
        # settings.MONSTER_HURT_TIME.
        self.hurt_t = 0.0
        # Which painted view to use, updated only **while moving** (see
        # `_track_facing`) so a monster that stops, is hit, or winds up a cast
        # keeps facing the way it was going. "down" means the plain front art.
        self.facing_dir = "down"
        self.face_left = False
        self.dead = False
        self.targetable = True          # Blinker turns this off while it's gone
        self.chasing = False
        self.newly_chasing = False      # True only the frame it locks onto the player
        self.knockback = pygame.Vector2()   # pending shove, spent on the next update
        self._t = 0.0
        # The book this one is carrying, by colour, or None. It hits the floor
        # where the monster dies — see `PlayState._on_monster_died`.
        self.drops = drops
        # Name of this character's voice pack, or None for the generic effects.
        # `AudioSystem.play_voiced(self.voice, "die")` looks for `<voice>_die`.
        self.voice = voice
        self.sound_request = None      # a noise for PlayState to play, once
        self._wander_target = pygame.Vector2(x, y)
        self._wander_timer = 0.0

    # ── behavior ─────────────────────────────────────────────────────────--
    def update(self, dt, player, collider):
        self._t += dt
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)
        if self.hurt_t > 0:
            self.hurt_t = max(0.0, self.hurt_t - dt)

        to_player = player.pos - self.pos
        dist = to_player.length()
        was_chasing = self.chasing
        self.chasing = (dist <= settings.MONSTER_AGGRO
                        and self.home.distance_to(self.pos) <= settings.MONSTER_LEASH
                        and self._can_see(player.pos, collider))
        self.newly_chasing = self.chasing and not was_chasing

        if self.knockback.length_squared():
            # Spent here, not in take_hit: this is the only place with a collider
            # to resolve against, and an unresolved shove goes through walls.
            self.displace(self.knockback, collider)
            self.knockback = pygame.Vector2()

        if self.chasing:
            self._chase(dt, to_player, dist)
        elif self.mode == "hunt":
            self._wander_toward(dt, player.pos, radius=130, bias=0.65)   # search
        else:
            self._wander_toward(dt, self.home, radius=52, bias=0.0)      # guard post

        self._track_facing()
        self.move_and_collide(dt, collider)

    def _can_see(self, target, collider):
        """Is there a clear line from here to `target`?

        Aggro used to be pure distance, so a monster locked on *through a wall*
        and then walked out of its room to reach the player — which reads as it
        teleporting between classrooms, because the moment you see it, it is
        already somewhere it has no business being. Walking the segment in short
        steps is crude but exact enough at 32px tiles, and it runs only while a
        player is within aggro range.
        """
        if not settings.MONSTER_SIGHT_STEP:
            return True
        d = pygame.Vector2(target) - self.pos
        steps = int(d.length() // settings.MONSTER_SIGHT_STEP)
        for i in range(1, steps + 1):
            p = self.pos + d * (i / (steps + 1))
            if collider.solid_rects(pygame.Rect(int(p.x) - 1, int(p.y) - 1, 2, 2)):
                return False
        return True

    def _chase(self, dt, to_player, dist):
        if dist < 1:
            self.vel = pygame.Vector2()
            return
        d = to_player / dist
        perp = pygame.Vector2(-d.y, d.x)          # sideways weave -> "alive"
        weave = math.sin(self._t * 6.0) * settings.MONSTER_WEAVE_AMP
        self.vel = (d + perp * weave).normalize() * self.speed

    def _wander_toward(self, dt, center, radius, bias):
        """Roam around `center`; `bias` (0..1) pulls new targets toward center."""
        self._wander_timer -= dt
        if self._wander_timer <= 0 or self.pos.distance_to(self._wander_target) < 10:
            angle = random.uniform(0, math.tau)
            dist = random.uniform(0.3, 1.0) * radius
            offset = pygame.Vector2(math.cos(angle), math.sin(angle)) * dist
            toward = (pygame.Vector2(center) - self.pos)
            if toward.length() > 0:
                offset = offset.lerp(toward, bias)
            self._wander_target = pygame.Vector2(center) + offset * (1 - bias)
            self._wander_timer = random.uniform(0.8, 2.0)
        d = self._wander_target - self.pos
        if d.length() > 4:
            self.vel = d.normalize() * self.speed * settings.MONSTER_WANDER_MULT
        else:
            self.vel = pygame.Vector2()

    # ── combat ───────────────────────────────────────────────────────────--
    def take_hit(self, from_pos, amount=1.0, direction=None):
        """Take `amount` pips of damage. Returns True if this finished it off.

        Health is a float: weapons deal fractional pips (a thrown knife is worth
        less than a sword swing) and monsters carry fractional totals, so the
        two can be tuned by percentage without being forced onto whole numbers.
        One call is one blow — a two-pip swing knocks back once, not twice.

        The shove is only *recorded* here. It is applied in `update()`, which is
        the one place with a collider to resolve it against.
        """
        if not self.targetable:
            return False
        self.health -= amount
        self.flash = settings.HIT_FLASH_TIME
        self.hurt_t = settings.MONSTER_HURT_TIME
        self.knockback = self._knock_dir(from_pos, direction) * settings.MONSTER_KNOCKBACK
        if self.health <= 0:
            self.dead = True
        return self.dead

    def _knock_dir(self, from_pos, direction):
        """Which way a blow shoves it, as a unit vector (or zero for none).

        A thrown weapon lands *inside* its target, so `self.pos - knife.pos` is a
        near-zero vector — and `normalize()` on near-zero is direction noise at
        full magnitude. That is why a knife hit made the monster hop somewhere
        random while a sword hit, thrown from a body-width away, did not. A
        weapon that knows its own travel direction passes it and that wins;
        otherwise the blow must land far enough away to mean something.
        """
        if direction is not None:
            aim = pygame.Vector2(direction)
            if aim.length() > 0:
                return aim.normalize()
        push = self.pos - pygame.Vector2(from_pos)
        return push.normalize() if push.length() >= settings.KNOCKBACK_MIN_DIST \
            else pygame.Vector2()

    def dist_to(self, point):
        return self.pos.distance_to(point)

    # ── animation ────────────────────────────────────────────────────────--
    # Most monsters ship as a single painted pose and stay on "idle" forever;
    # the teachers have a walk too (§R8/§R9 asked for four poses). The state
    # machine is the same one the player uses, on `Entity`.
    #
    # ⚠️ **No "attack" state, even though the sheets carry an ATTACK pose.** The
    # delivered pose is drawn a quarter smaller than the other three, so cutting
    # it at the sheet's own scale makes the teacher visibly *shrink* every time
    # it casts. The pose is extracted and waiting; it needs either a re-roll or a
    # per-pose scale correction in `extract_teacher.py` before it can be used.
    WALK_HZ = 4             # slower than the player's 7: these things shuffle
    PINGPONG = ("walk", "walk_side", "walk_down")

    @property
    def anim_state(self):
        """hurt > cast > walk > idle, and directional where the art exists.

        ⚠️ **Hurt outranks casting.** Being hit mid-wind-up has to *look* like
        being interrupted, or the flinch is invisible exactly when it matters —
        during the one moment the monster is standing still.
        """
        if self.hurt_t > 0 and "hurt" in self.frames:
            return self._directional("hurt")
        if getattr(self, "charge", None) is not None and "cast" in self.frames:
            return self._directional("cast")
        stem = "walk" if self.vel.length_squared() > 4 else "idle"
        return self._directional(stem)

    def _frame_for_state(self, state):
        """The frame for `state`, played by *its own* clock where it has one.

        A hurt and a cast are one-shots tied to something the game is already
        timing — `hurt_t` counting down, `charge` counting up — so they step
        through their strip in time with it. A walk just loops.
        """
        if state.startswith("hurt"):
            done = 1.0 - (self.hurt_t / settings.MONSTER_HURT_TIME)
            return self.frame_for(state, 0.0, progress=min(0.999, max(0.0, done)))
        if state.startswith("cast") and getattr(self, "charge", None) is not None:
            return self.frame_for(state, 0.0, progress=min(0.999, self.charge))
        return self.frame_for(state, self._t)

    def _track_facing(self):
        """Remember which way it is going, so a stopped monster keeps facing it.

        Called from every `update()` that moves. ⚠️ It deliberately does nothing
        when the monster is still: a caster stands still for its whole wind-up,
        and clearing the facing there would snap it round to front mid-cast.
        """
        if self.vel.length_squared() <= 4:
            return
        if abs(self.vel.x) >= abs(self.vel.y):
            self.facing_dir = "side"
            self.face_left = self.vel.x < 0
        else:
            self.facing_dir = "up" if self.vel.y < 0 else "down"

    def _directional(self, stem):
        """`<stem>_<facing>` where that art exists, else the plain stem.

        ⚠️ It reads `facing_dir`, which is only updated **while moving** — so a
        monster that stops, gets hit, or winds up a cast keeps facing the way it
        was going. Deriving the view from the *current* velocity instead made it
        snap back to front the instant it stood still, which for a caster is its
        entire wind-up.

        "down" has no suffix because the front view *is* the plain stem — that is
        how every monster's art was named before any of them could turn.
        """
        if self.facing_dir != "down":
            cand = f"{stem}_{self.facing_dir}"
            if cand in self.frames:
                return cand
        return stem if stem in self.frames else "idle"

    # ── draw ─────────────────────────────────────────────────────────────--
    def draw(self, surface, camera):
        bob = math.sin(self._t * 4.0) * 1.5
        r = self.hitbox
        ox, oy = round(camera.offset.x), round(camera.offset.y)
        pygame.draw.ellipse(surface, (0, 0, 0),
                            pygame.Rect(r.centerx - 15 - ox, r.bottom - 5 - oy, 30, 7))
        state = self.anim_state
        img = self._frame_for_state(state) if self.sprite else None
        if img:
            if getattr(self, "face_left", False) and state.endswith("_side"):
                img = pygame.transform.flip(img, True, False)
            sx = r.centerx - img.get_width() // 2 - ox
            sy = r.bottom - img.get_height() - oy + bob     # feet-aligned
            surface.blit(img, (sx, sy))
            # ⚠️ The white tint is now the **fallback**, not the effect. It was
            # the whole "you hit me" signal — a monster flashing into a white
            # box, which reads as a rendering glitch rather than as pain. A
            # painted flinch says it properly; the tint stays only for monsters
            # that have no hurt art yet, and never on top of one that does.
            if self.flash > 0 and "hurt" not in self.frames:
                flash = img.copy()
                flash.fill((255, 255, 255, 160), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(flash, (sx, sy))
        else:
            sx, sy = r.x - ox, r.y - oy
            pygame.draw.rect(surface, (120, 200, 120), (sx, sy, r.w, r.h))
        self._draw_health(surface, r.centerx - r.w // 2 - ox,
                          (r.bottom - (img.get_height() if img else r.h) - oy), r.w)

    def _draw_health(self, surface, sx, sy, w):
        """One pip per whole point of health, the last one partly filled.

        Totals are fractional now, so a pip has to be able to show a part-hit —
        otherwise a monster on 4.6 health looks identical to one on 4.0 and the
        player cannot tell whether the next blow lands the kill.
        """
        pips = max(1, int(math.ceil(self.max_health)))
        pw, gap = 6, 2
        total = pips * pw + (pips - 1) * gap
        x0 = sx + (w - total) // 2
        y = sy - 8
        for i in range(pips):
            rect = pygame.Rect(x0 + i * (pw + gap), y, pw, 4)
            pygame.draw.rect(surface, (60, 60, 66), rect)
            filled = max(0.0, min(1.0, self.health - i))
            if filled > 0:
                pygame.draw.rect(surface, (230, 80, 80),
                                 (rect.x, rect.y, max(1, round(pw * filled)), rect.h))


class Caster(Monster):
    """A ranged monster that fights at a distance and lobs projectiles.

    `cast_kind` selects the projectile PlayState spawns ("fire" -> Fireball,
    "web" -> WebProjectile). It closes to `cast_range`, kites away inside
    `keep_min`, strafes in the sweet spot, and casts on `cast_cd`. After update()
    PlayState reads `cast_request` (a direction) + `cast_kind` to spawn it.

    **The wind-up is the whole fight.** It used to fire on the frame its cooldown
    expired — the shot simply existed, and being hit was a question of where you
    happened to be standing rather than of anything you did. Now it *commits*:

    - it **stops moving** for `wind_up` seconds, which is the readable tell;
    - it **locks its aim** at the start, so walking sideways actually dodges —
      tracking the player through the wind-up would make the tell decorative;
    - it **gives up** if the player breaks line of sight or leaves its range,
      because a wind-up you can hide from is worth answering.
    """
    def __init__(self, x, y, cast_kind, name, hits, guards=None, sprite=None,
                 speed=70, cast_range=250, keep_min=120, cast_cd=2.0, drops=None,
                 voice=None, wind_up=0.0):
        super().__init__(x, y, hits, guards=guards, sprite=sprite, drops=drops,
                         name=name, mode="guard", speed=speed, voice=voice)
        self.cast_kind = cast_kind
        self.cast_range = cast_range
        self.keep_min = keep_min
        self.cast_cd_max = cast_cd
        self.cast_cd = cast_cd
        self.cast_request = None
        self.wind_up = wind_up
        self.winding = 0.0          # seconds of charge left, 0 = not charging
        self.wind_aim = None        # the direction locked in when it started
        self.cast_started = False   # one frame, for PlayState to play the tell
        self.can_shoot = False      # in range, on the leash, with a clear line

    @property
    def charge(self):
        """0 -> 1 through the wind-up, or None when it is not charging.

        What a charge effect and (once §S5/§S6 land) a cast animation read to
        stay in step with the shot — which is the entire point of a wind-up
        drawn rather than merely waited out."""
        if self.winding <= 0 or not self.wind_up:
            return None
        return 1.0 - self.winding / self.wind_up

    def update(self, dt, player, collider):
        self._t += dt
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)
        if self.hurt_t > 0:
            self.hurt_t = max(0.0, self.hurt_t - dt)
        self.cast_cd = max(0.0, self.cast_cd - dt)

        to_player = player.pos - self.pos
        dist = to_player.length()
        was_chasing = self.chasing
        self.chasing = (dist <= settings.MONSTER_AGGRO
                        and self.home.distance_to(self.pos) <= settings.MONSTER_LEASH
                        and self._can_see(player.pos, collider))
        self.newly_chasing = self.chasing and not was_chasing

        # ⚠️ **Shooting is not the same test as chasing.** `chasing` also requires
        # `MONSTER_AGGRO` (190px), and a caster's range is 250 — so gating the
        # cast on `chasing` quietly capped every caster at 190 and made
        # `CASTER_CAST_RANGE` a dead number. What a shot actually needs is: in
        # range, on its leash, and a clear line. The line is the part that
        # matters, because without it a caster fires through walls.
        self.can_shoot = (dist <= self.cast_range
                          and self.home.distance_to(self.pos) <= settings.MONSTER_LEASH
                          and self._can_see(player.pos, collider))

        direction = to_player.normalize() if dist > 0 else pygame.Vector2(1, 0)
        if self.winding > 0:
            # Committed: stopped, and throwing where it aimed. ⚠️ No
            # `_track_facing` here — it is not moving, and the whole point of
            # keeping the last facing is that it does not spin round mid-cast.
            self.vel = pygame.Vector2()
            self.winding -= dt
            if not self.can_shoot:
                self.winding = 0.0
            elif self.winding <= 0:
                self.cast_request = self.wind_aim or direction
                self.cast_cd = self.cast_cd_max
                self.winding = 0.0
            self.move_and_collide(dt, collider)
            return

        if dist > self.cast_range:
            self.vel = direction * self.speed                      # close in
        elif dist < self.keep_min:
            self.vel = -direction * self.speed                     # kite away
        else:
            # ⚠️ Strafe at a **steady** speed that reverses, not a sine through
            # zero. Scaling by `sin` left it barely moving for half of every
            # cycle and then reversing — on screen that is not circling, it is a
            # sprite juddering on the spot, and it read as the monster being
            # stuck. Constant speed with an occasional turn is what circling
            # somebody actually looks like.
            perp = pygame.Vector2(-direction.y, direction.x)
            way = 1 if math.sin(self._t * 0.7) >= 0 else -1
            self.vel = perp * way * self.speed * 0.65
        self._track_facing()
        self.move_and_collide(dt, collider)

        if self.can_shoot and self.cast_cd <= 0:
            if self.wind_up <= 0:
                self.cast_request = direction
                self.cast_cd = self.cast_cd_max
            else:
                self.winding = self.wind_up
                self.wind_aim = pygame.Vector2(direction)
                self.cast_started = True


    # The charge, by projectile. Bright and saturated on purpose: it is the one
    # thing on screen the player has to notice in half a second.
    CHARGE_COLOR = {"fire": (238, 132, 54), "web": (226, 226, 236),
                    "tome": (172, 112, 226), "bolt": (150, 200, 255)}

    def draw(self, surface, camera):
        super().draw(surface, camera)
        charge = self.charge
        if charge is None:
            return
        # ⚠️ Drawn **at the hands, not centred on the body**, and offset toward
        # the aim: a glow behind the monster reads as being lit, not as winding
        # up. Grows with the charge so the moment of release is predictable.
        rgb = self.CHARGE_COLOR.get(self.cast_kind, (240, 220, 160))
        aim = self.wind_aim or pygame.Vector2(1, 0)
        r = self.hitbox
        cx = r.centerx - round(camera.offset.x) + aim.x * 12
        cy = r.centery - round(camera.offset.y) + aim.y * 12 - 4
        peak = 2 + charge * 6
        layer = pygame.Surface((int(peak * 4), int(peak * 4)), pygame.SRCALPHA)
        mid = layer.get_width() // 2
        for i in range(4):
            rad = max(1, int(peak * (4 - i) / 4))
            step = (i + 1) / 4 * (0.45 + 0.55 * charge)
            pygame.draw.circle(layer, tuple(int(c * step) for c in rgb),
                               (mid, mid), rad)
        surface.blit(layer, (cx - mid, cy - mid),
                     special_flags=pygame.BLEND_RGB_ADD)


def make_fire_caster(x, y, hits=None, guards=None, sprite=None, drops=None):
    return Caster(x, y, "fire", "Little Terror",
                  hits if hits is not None else settings.CASTER_HITS,
                  guards=guards, sprite=sprite, drops=drops, speed=settings.CASTER_SPEED,
                  cast_range=settings.CASTER_CAST_RANGE,
                  keep_min=settings.CASTER_KEEP_MIN, wind_up=settings.CASTER_WINDUP, cast_cd=settings.CASTER_CAST_CD)


def make_web_caster(x, y, hits=None, guards=None, sprite=None, drops=None):
    return Caster(x, y, "web", "Little Snir",
                  hits if hits is not None else settings.WEBBER_HITS,
                  guards=guards, sprite=sprite, drops=drops, speed=settings.WEBBER_SPEED,
                  cast_range=settings.WEB_CAST_RANGE,
                  keep_min=settings.WEB_KEEP_MIN, wind_up=settings.WEB_WINDUP, cast_cd=settings.WEB_CAST_CD)


class Teacher(Caster):
    """A teacher: a caster that **holds a room** instead of beelining across one.

    `Caster.update` closes on the player from any distance — beyond `cast_range`
    it walks straight at them, which is right for a corridor monster with a
    250px reach and a whole hallway to work in. Dropped into a classroom it makes
    the room pointless: the teacher is already crossing the floor before the
    player is through the door.

    So when it cannot see the player, this one wanders its post instead — the
    behaviour `Monster` already has for guards, at a radius wide enough to cover
    a classroom rather than orbit one tile. The fight only starts once the player
    is actually in the room.
    """
    def update(self, dt, player, collider):
        seen = (self.pos.distance_to(player.pos) <= settings.MONSTER_AGGRO
                and self.home.distance_to(self.pos) <= settings.MONSTER_LEASH
                and self._can_see(player.pos, collider))
        if seen:
            return super().update(dt, player, collider)

        self._t += dt
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)
        if self.hurt_t > 0:
            self.hurt_t = max(0.0, self.hurt_t - dt)
        self.cast_cd = max(0.0, self.cast_cd - dt)
        # ⚠️ Both flags must be cleared, not left at last frame's value:
        # `newly_chasing` drives the growl, and a stale True re-growls every
        # frame the teacher spends out of sight.
        self.chasing = False
        self.newly_chasing = False
        self._wander_toward(dt, self.home, radius=settings.TEACHER_WANDER, bias=0.0)
        self._track_facing()
        self.move_and_collide(dt, collider)


def make_teacher(x, y, female=True, hits=None, guards=None, sprite=None, drops=None):
    return Teacher(x, y, "tome", "Teacher" if female else "Schoolmaster",
                   hits if hits is not None else settings.TEACHER_HITS,
                   voice="teacher_f" if female else "teacher_m",
                   guards=guards, sprite=sprite, drops=drops, speed=settings.TEACHER_SPEED,
                   cast_range=settings.TOME_CAST_RANGE,
                   keep_min=settings.TOME_KEEP_MIN, wind_up=settings.TOME_WINDUP, cast_cd=settings.TOME_CAST_CD)


class Blinker(Monster):
    """Emri — "the disappearing monster". A boss that fights in blinks.

    It is never *approached*: it waits out of the world entirely (hidden and
    untargetable), materializes at arm's length behind or beside the player,
    charges for `EMRI_TELEGRAPH` seconds, throws a lightbolt, and dissolves.

    The telegraph is the entire fight. It is the only window in which the boss
    can be hit, which is what makes it hard without giving it unfair damage —
    so `EMRI_TELEGRAPH` is the difficulty dial here, not `EMRI_HITS`.

    States: hidden -> appear -> strike -> vanish -> hidden.
    """
    HIDDEN, APPEAR, STRIKE, VANISH = "hidden", "appear", "strike", "vanish"

    boss = True          # Zina's bite wounds it rather than killing it outright

    def __init__(self, x, y, sprite=None, hits=None):
        super().__init__(x, y, hits if hits is not None else settings.EMRI_HITS,
                         sprite=sprite, name="Emri", mode="hunt",
                         speed=settings.EMRI_DRIFT)
        self.size = pygame.Vector2(settings.EMRI_SIZE)
        # ⚠️ While `dormant` it stays gone: hidden, untargetable and not
        # advancing its own state machine. That is what a phase break is — the
        # boss leaves, help arrives, and only when the help is dead does it come
        # back. See `PlayState._update_duel`.
        self.dormant = False
        self.cast_kind = "bolt"
        self.cast_request = None
        self.state = self.HIDDEN
        self.state_t = random.uniform(0.6, 1.2)        # a beat before the first blink
        self.targetable = False
        self.spark_seed = 0.0

    # ── behavior ─────────────────────────────────────────────────────────--
    def update(self, dt, player, collider):
        self._t += dt
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)
        if self.hurt_t > 0:
            self.hurt_t = max(0.0, self.hurt_t - dt)
        # ⚠️ It used to be nailed to the floor between blinks. A boss that stands
        # perfectly still for a 1.3s telegraph reads as a prop, so it now drifts
        # around the player while it is *visible* — slowly enough that the
        # telegraph is still a window to swing into, not a chase.
        if self.state in (self.APPEAR, self.STRIKE) and not self.dormant:
            to_player = player.pos - self.pos
            if to_player.length() > 1:
                perp = pygame.Vector2(-to_player.y, to_player.x).normalize()
                way = 1 if math.sin(self._t * 0.9) >= 0 else -1
                self.vel = perp * way * self.speed
            else:
                self.vel = pygame.Vector2()
            self._track_facing()
            self.move_and_collide(dt, collider)
        else:
            self.vel = pygame.Vector2()
        if self.dormant:
            self.state, self.targetable = self.HIDDEN, False
            self.chasing = self.newly_chasing = False
            return
        self.state_t -= dt
        if self.state_t <= 0:
            self._advance(player, collider)
        # it is "chasing" whenever it is present, so the growl cue still fires
        was = self.chasing
        self.chasing = self.state != self.HIDDEN
        self.newly_chasing = self.chasing and not was

    def _advance(self, player, collider):
        if self.state == self.HIDDEN:
            self.pos = self._blink_spot(player, collider)
            self.state, self.state_t = self.APPEAR, settings.EMRI_TELEGRAPH
            self.targetable = True
            # Entities do not own the audio system — they *ask*, and PlayState
            # plays it. Same contract as Zina's bark; see `_drain_sounds`.
            self.sound_request = "emri_blink"
        elif self.state == self.APPEAR:
            aim = player.pos - self.pos
            self.cast_request = aim.normalize() if aim.length() else pygame.Vector2(1, 0)
            self.state, self.state_t = self.STRIKE, settings.EMRI_STRIKE_TIME
        elif self.state == self.STRIKE:
            self.state, self.state_t = self.VANISH, settings.EMRI_VANISH_TIME
        else:                                           # VANISH -> gone again
            self.state = self.HIDDEN
            self.state_t = random.uniform(settings.EMRI_HIDDEN_MIN, settings.EMRI_HIDDEN_MAX)
            self.targetable = False

    def _blink_spot(self, player, collider):
        """A walkable point one arm's length from the player, angle at random."""
        for _ in range(settings.EMRI_BLINK_TRIES):
            a = random.uniform(0, math.tau)
            spot = player.pos + pygame.Vector2(math.cos(a), math.sin(a)) * settings.EMRI_BLINK_DIST
            box = pygame.Rect(0, 0, int(self.size.x), int(self.size.y))
            box.center = (round(spot.x), round(spot.y))
            if not collider.solid_rects(box):
                return spot
        return pygame.Vector2(player.pos)               # cornered: land on them

    # ── presence ─────────────────────────────────────────────────────────--
    @property
    def alpha(self):
        """0..1 visibility — drives both the fade and the danger read."""
        if self.state == self.HIDDEN:
            return 0.0
        if self.state == self.APPEAR:
            return min(1.0, 1.0 - self.state_t / settings.EMRI_TELEGRAPH + 0.25)
        if self.state == self.VANISH:
            return max(0.0, self.state_t / settings.EMRI_VANISH_TIME)
        return 1.0

    def draw(self, surface, camera):
        if self.state == self.HIDDEN:
            return
        a = self.alpha
        r = self.hitbox
        ox, oy = round(camera.offset.x), round(camera.offset.y)
        state = self.anim_state
        img = self._frame_for_state(state) if self.sprite else None
        if img:
            if self.face_left and state.endswith("_side"):
                img = pygame.transform.flip(img, True, False)
            # ⚠️ **Not `set_alpha`.** On a per-pixel-alpha surface it discards
            # the mask and fades the whole rectangle — the same box that showed
            # up around every impact splash. Multiply into the alpha instead.
            faded = img.copy()
            faded.fill((255, 255, 255, int(255 * a)),
                       special_flags=pygame.BLEND_RGBA_MULT)
            sx = r.centerx - img.get_width() // 2 - ox
            sy = r.bottom - img.get_height() - oy
            surface.blit(faded, (sx, sy))
            # the white tint is the fallback, exactly as it is for every other
            # monster: a painted flinch says it better
            if self.flash > 0 and "hurt" not in self.frames:
                flash = img.copy()
                flash.fill((255, 255, 255, 160), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(flash, (sx, sy))
        self._draw_crackle(surface, r, ox, oy, a)
        if self.targetable:
            top = r.bottom - (img.get_height() if img else r.h) - oy
            self._draw_health(surface, r.centerx - r.w // 2 - ox, top, r.w)

    def _draw_crackle(self, surface, r, ox, oy, a):
        """Lightning gathering around it — brightest just before the strike."""
        charge = 1.0 if self.state == self.STRIKE else a
        cx, cy = r.centerx - ox, r.centery - oy
        for i in range(int(3 + 5 * charge)):
            ang = random.uniform(0, math.tau)
            r0 = random.uniform(6, 14)
            r1 = r0 + random.uniform(5, 14) * charge
            col = (255, 245, 200) if i % 3 == 0 else (250, 200, 80)
            pygame.draw.line(surface, col,
                             (cx + math.cos(ang) * r0, cy + math.sin(ang) * r0),
                             (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1), 1)


def make_emri(x, y, sprite=None, hits=None):
    return Blinker(x, y, sprite=sprite, hits=hits)
