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
    def __init__(self, x, y, hits=None, guards=None, sprite=None,
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
        self.dead = False
        self.targetable = True          # Blinker turns this off while it's gone
        self.chasing = False
        self.newly_chasing = False      # True only the frame it locks onto the player
        self._t = 0.0
        self._wander_target = pygame.Vector2(x, y)
        self._wander_timer = 0.0

    # ── behavior ─────────────────────────────────────────────────────────--
    def update(self, dt, player, collider):
        self._t += dt
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        to_player = player.pos - self.pos
        dist = to_player.length()
        was_chasing = self.chasing
        self.chasing = dist <= settings.MONSTER_AGGRO
        self.newly_chasing = self.chasing and not was_chasing

        if self.chasing:
            self._chase(dt, to_player, dist)
        elif self.mode == "hunt":
            self._wander_toward(dt, player.pos, radius=130, bias=0.65)   # search
        else:
            self._wander_toward(dt, self.home, radius=52, bias=0.0)      # guard post

        self.move_and_collide(dt, collider)

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
    def take_hit(self, from_pos, amount=1.0):
        """Take `amount` pips of damage. Returns True if this finished it off.

        Health is a float: weapons deal fractional pips (a thrown knife is worth
        less than a sword swing) and monsters carry fractional totals, so the
        two can be tuned by percentage without being forced onto whole numbers.
        One call is one blow — a two-pip swing knocks back once, not twice.
        """
        if not self.targetable:
            return False
        self.health -= amount
        self.flash = settings.HIT_FLASH_TIME
        push = self.pos - pygame.Vector2(from_pos)
        if push.length() > 0:
            self.pos += push.normalize() * settings.MONSTER_KNOCKBACK
        if self.health <= 0:
            self.dead = True
        return self.dead

    def dist_to(self, point):
        return self.pos.distance_to(point)

    # ── draw ─────────────────────────────────────────────────────────────--
    def draw(self, surface, camera):
        bob = math.sin(self._t * 4.0) * 1.5
        r = self.hitbox
        ox, oy = round(camera.offset.x), round(camera.offset.y)
        pygame.draw.ellipse(surface, (0, 0, 0),
                            pygame.Rect(r.centerx - 15 - ox, r.bottom - 5 - oy, 30, 7))
        if self.sprite:
            sx = r.centerx - self.sprite.get_width() // 2 - ox
            sy = r.bottom - self.sprite.get_height() - oy + bob     # feet-aligned
            surface.blit(self.sprite, (sx, sy))
            if self.flash > 0:
                flash = self.sprite.copy()
                flash.fill((255, 255, 255, 160), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(flash, (sx, sy))
        else:
            sx, sy = r.x - ox, r.y - oy
            pygame.draw.rect(surface, (120, 200, 120), (sx, sy, r.w, r.h))
        self._draw_health(surface, r.centerx - r.w // 2 - ox,
                          (r.bottom - (self.sprite.get_height() if self.sprite else r.h) - oy), r.w)

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
    """
    def __init__(self, x, y, cast_kind, name, hits, guards=None, sprite=None,
                 speed=70, cast_range=250, keep_min=120, cast_cd=2.0):
        super().__init__(x, y, hits, guards=guards, sprite=sprite,
                         name=name, mode="guard", speed=speed)
        self.cast_kind = cast_kind
        self.cast_range = cast_range
        self.keep_min = keep_min
        self.cast_cd_max = cast_cd
        self.cast_cd = cast_cd
        self.cast_request = None

    def update(self, dt, player, collider):
        self._t += dt
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)
        self.cast_cd = max(0.0, self.cast_cd - dt)

        to_player = player.pos - self.pos
        dist = to_player.length()
        was_chasing = self.chasing
        self.chasing = dist <= settings.MONSTER_AGGRO
        self.newly_chasing = self.chasing and not was_chasing

        direction = to_player.normalize() if dist > 0 else pygame.Vector2(1, 0)
        if dist > self.cast_range:
            self.vel = direction * self.speed                      # close in
        elif dist < self.keep_min:
            self.vel = -direction * self.speed                     # kite away
        else:
            perp = pygame.Vector2(-direction.y, direction.x)       # strafe
            self.vel = perp * math.sin(self._t * 1.5) * self.speed * 0.5
        self.move_and_collide(dt, collider)

        if dist <= self.cast_range and self.cast_cd <= 0:
            self.cast_request = direction
            self.cast_cd = self.cast_cd_max


def make_fire_caster(x, y, hits=None, guards=None, sprite=None):
    return Caster(x, y, "fire", "Little Terror",
                  hits if hits is not None else settings.CASTER_HITS,
                  guards=guards, sprite=sprite, speed=settings.CASTER_SPEED,
                  cast_range=settings.CASTER_CAST_RANGE,
                  keep_min=settings.CASTER_KEEP_MIN, cast_cd=settings.CASTER_CAST_CD)


def make_web_caster(x, y, hits=None, guards=None, sprite=None):
    return Caster(x, y, "web", "Little Snir",
                  hits if hits is not None else settings.WEBBER_HITS,
                  guards=guards, sprite=sprite, speed=settings.WEBBER_SPEED,
                  cast_range=settings.WEB_CAST_RANGE,
                  keep_min=settings.WEB_KEEP_MIN, cast_cd=settings.WEB_CAST_CD)


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

    def __init__(self, x, y, sprite=None, hits=None):
        super().__init__(x, y, hits if hits is not None else settings.EMRI_HITS,
                         sprite=sprite, name="Emri", mode="hunt",
                         speed=0)                      # it teleports; it never walks
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
        self.vel = pygame.Vector2()                    # never moves under its own power
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
        if self.sprite:
            img = self.sprite.copy()
            img.set_alpha(int(255 * a))
            sx = r.centerx - img.get_width() // 2 - ox
            sy = r.bottom - img.get_height() - oy
            surface.blit(img, (sx, sy))
            if self.flash > 0:
                flash = self.sprite.copy()
                flash.fill((255, 255, 255, 160), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(flash, (sx, sy))
        self._draw_crackle(surface, r, ox, oy, a)
        if self.targetable:
            top = r.bottom - (self.sprite.get_height() if self.sprite else r.h) - oy
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
