"""Player: the chosen warrior — intent-driven movement, sprint, stamina, combat.

Which warrior you picked is data (`entities/warriors.py`), not a subclass: it
supplies the sprite set to animate plus the numbers that actually differ (speed,
health, reach, active power). Anything a warrior can do that another cannot lives
behind `self.power`.

Animation is state-driven — hurt beats attack beats walk beats idle — off four
painted poses per warrior. The sheets give one frame per state, so the walk cycle
is synthesized: a two-step bob paired with a squash on the off-beat, which reads
as a gait without inventing frames the artist never drew.
"""
import math
import pygame

import settings
from game.entities import warriors
from game.entities.entity import Entity


class Player(Entity):
    def __init__(self, x, y, warrior=None):
        w, h = settings.PLAYER_SIZE
        super().__init__(x, y, w, h)
        self.color = (90, 170, 240)
        self.warrior = warrior or warriors.get(warriors.DEFAULT_ID)
        self.max_health = self.warrior["max_health"]
        self.walk_speed = self.warrior["speed"]
        self.reach = self.warrior["reach"]
        self.weapon = self.warrior.get("weapon", "melee")
        self.damage = self.warrior.get("damage", 1)
        self.cooldown = self.warrior.get("cooldown", settings.SWING_COOLDOWN)
        self.attack_cd = 0.0        # every weapon is paced; see warriors.py
        self.power = self.warrior["power"]
        self.power_charges = settings.ZINA_CHARGES if self.power == "zina" else 0

        self.stamina = settings.STAMINA_MAX
        self._regen_delay = 0.0     # time left before stamina regens
        self.is_sprinting = False
        self.health = self.max_health
        self._dmg_delay = 0.0       # time left before health regens
        self.hurt_flash = 0.0       # brief flash timer when damaged
        self.sound_request = None   # a noise for PlayState to play, once
        # Difficulty's `regen` dial. 1.0 unless PlayState says otherwise, so a
        # Player built outside a run (tests, the select screen) heals normally.
        self.regen = 1.0
        self.facing = 1             # 1 = right, -1 = left (for sprite flip)
        # Which painted view to use: "down" (toward the camera), "up" (away) or
        # "side". ⚠️ **A back view cannot be mirrored out of a front view**, so
        # this only does anything for a warrior whose sheet carries the extra
        # rows; everyone else falls back to plain "walk" and looks exactly as
        # they did before.
        self.facing_dir = "down"
        self._walk_t = 0.0          # animation clock
        self._moving = False
        self.swing = 0.0            # sword-swing effect timer
        self.webbed = False         # caught in Little Snir's web?
        self.struggle = 0           # Space presses left to break free

    # ── animation ────────────────────────────────────────────────────────--
    # The machinery is on `Entity` and shared with the monsters; a warrior only
    # has to say which pose wins. Hurt beats attack beats walk beats idle: being
    # hit mid-swing should read as being hit.
    @property
    def anim_state(self):
        # ⚠️ Being webbed outranks being hit. The web now drains health every
        # frame it holds you (§5), so `hurt_flash` is almost always up while
        # caught — and a flinch pose on top of a trapped one reads as neither.
        if self.webbed and "webbed" in self.frames:
            return "webbed"
        if self.hurt_flash > 0:
            return "hurt"
        if self.swing > 0:
            return "attack"
        stem = "walk" if self._moving else "idle"
        directional = f"{stem}_{self.facing_dir}"
        return directional if directional in self.frames else stem

    def _current_frame(self):
        state = self.anim_state
        if state == "webbed":
            # More struggle left means more silk: the strip runs from barely
            # caught to fully wrapped, so it is played *backwards* as the player
            # mashes free. Progress is the escape, not a clock.
            span = max(1, settings.WEB_STRUGGLE_HITS - 1)
            caught = (self.struggle - 1) / span
            return self.frame_for(state, 0.0, progress=min(1.0, max(0.0, caught)))
        return self.frame_for(state, self._walk_t)

    def _mirrors(self):
        """Should the sprite be flipped for leftward movement?

        ⚠️ Only views that are *sideways* may mirror. Flipping a front or back
        view swaps the sword into the wrong hand and the shield with it, for no
        gain — the character is symmetrical about the camera in those
        directions. Plain "idle" counts as a front view **once a character has
        directional art**; for one that has none it is the only pose there is,
        and mirroring it is the behaviour every warrior had before.
        """
        if self.facing >= 0:
            return False
        state = self.anim_state
        if state.endswith(("_up", "_down")) or state == "webbed":
            return False
        return not (state == "idle" and "walk_side" in self.frames)

    @property
    def alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health = max(0.0, self.health - amount)
        self._dmg_delay = settings.PLAYER_REGEN_DELAY
        self.hurt_flash = 0.3       # long enough for the hurt pose to register
        # Asked for, not played: the player has no reference to the audio
        # system, and every damage source would otherwise have to remember to
        # make a noise. PlayState drains this — see `_drain_sounds`.
        self.sound_request = "player_hurt"

    def drain(self, amount):
        """Lose health without the flinch — for damage-over-time.

        `take_damage` flashes the sprite, holds off regeneration and asks for a
        grunt, all of which are right for *a blow* and wrong sixty times a
        second. A drain still stops regeneration (or it would heal through the
        web) but stays quiet.
        """
        self.health = max(0.0, self.health - amount)
        self._dmg_delay = max(self._dmg_delay, settings.PLAYER_REGEN_DELAY)

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def spend_power(self):
        """Consume one charge of the active power. False if there are none."""
        if self.power_charges <= 0:
            return False
        self.power_charges -= 1
        return True

    @property
    def throws(self):
        return self.weapon == "knife"

    def can_attack(self):
        return self.attack_cd <= 0

    def start_swing(self):
        self.swing = settings.SWING_TIME
        self.attack_cd = self.cooldown

    def take_web(self):
        if self.webbed:
            return          # already stuck — a new web doesn't re-trap/replenish
        self.webbed = True
        self.struggle = settings.WEB_STRUGGLE_HITS
        self.sound_request = "web_stuck"

    def struggle_free(self):
        """One Space press worth of struggling. Returns True when freed."""
        if not self.webbed:
            return False
        self.struggle -= 1
        if self.struggle <= 0:
            self.webbed = False
            self.struggle = 0
            self.sound_request = "web_break"
            return True
        return False

    def _update_health(self, dt):
        if self.hurt_flash > 0:
            self.hurt_flash = max(0.0, self.hurt_flash - dt)
        if self._dmg_delay > 0:
            self._dmg_delay = max(0.0, self._dmg_delay - dt)
        elif self.health < self.max_health:
            self.health = min(
                self.max_health,
                self.health + settings.PLAYER_HEALTH_REGEN * self.regen * dt)

    def update(self, dt, inp=None, collider=None):
        if inp is None:
            super().update(dt)
            return

        if self.swing > 0:
            self.swing = max(0.0, self.swing - dt)
        if self.attack_cd > 0:
            self.attack_cd = max(0.0, self.attack_cd - dt)

        move = pygame.Vector2() if self.webbed else inp.move   # stuck in the web
        wants_sprint = inp.sprint and self.stamina > 0 and move.length_squared() > 0
        self.is_sprinting = wants_sprint
        # sprint scales the warrior's own pace, so the fast one stays the fast one
        speed = self.walk_speed
        if wants_sprint:
            speed *= settings.PLAYER_SPRINT / settings.PLAYER_WALK

        self.vel = move * speed
        if collider is None:
            self.pos += self.vel * dt
        else:
            self.move_and_collide(dt, collider)

        if move.x < 0:
            self.facing = -1
        elif move.x > 0:
            self.facing = 1
        if move.length_squared() > 0:
            # Which way the *art* faces, as opposed to `facing`, which is only
            # the horizontal mirror. Sideways wins ties: a diagonal reads better
            # as a profile than as a back, and it is the direction the mirror
            # can actually express.
            self.facing_dir = "side" if abs(move.x) >= abs(move.y) else (
                "up" if move.y < 0 else "down")
        self._moving = move.length_squared() > 0
        self._walk_t += dt if self._moving else 0

        self._update_stamina(dt, wants_sprint)
        self._update_health(dt)

    def draw(self, surface, camera):
        if not self.sprite:
            super().draw(surface, camera)
            return
        r = self.hitbox
        ox, oy = round(camera.offset.x), round(camera.offset.y)
        frame = self._current_frame()
        bob = -1 if self._moving and self._step_phase(self._walk_t) else 0
        img = pygame.transform.flip(frame, True, False) if self._mirrors() else frame
        lunge = self.facing * int(4 * (self.swing / settings.SWING_TIME)) if self.swing > 0 else 0
        sx = r.centerx - img.get_width() // 2 - ox + lunge
        sy = r.bottom - img.get_height() - oy + bob
        pygame.draw.ellipse(surface, (0, 0, 0),
                            pygame.Rect(r.centerx - 9 - ox, r.bottom - 4 - oy, 18, 6))
        surface.blit(img, (sx, sy))
        if self.swing > 0 and not self.throws:
            self._draw_swing(surface, r, ox, oy)
        # Painted silk beats drawn silk: the procedural strands are the fallback
        # for a checkout with no webbed art, not a layer on top of it.
        if self.webbed and "webbed" not in self.frames:
            self._draw_web(surface, r, ox, oy)

    def _draw_swing(self, surface, r, ox, oy):
        """A glint travelling along the blade's tip.

        ⚠️ This was **three stacked arcs** 48px across — a thick white crescent
        that covered the warrior swinging it and read as a magic spell rather
        than a sword. Now that the swing is a painted three-frame animation, the
        arc was doing the job twice and drowning the art doing it better. What is
        left is a short faint trail behind a single bright point: enough to say
        *where the edge is*, and no more.
        """
        progress = 1.0 - self.swing / settings.SWING_TIME     # 0 -> 1
        cx = r.centerx - ox + self.facing * 14
        cy = r.centery - oy - 2
        radius = 22
        # the tip sweeps through the same arc the blade does
        sweep = math.radians(90 - progress * 165) if self.facing >= 0 else \
            math.radians(90 + progress * 165)
        for i, (back, size, rgb) in enumerate((
                (0.30, 1, (120, 145, 190)),
                (0.15, 2, (185, 205, 235)),
                (0.00, 3, (255, 255, 255)))):
            a = sweep + (back if self.facing >= 0 else -back)
            tx = cx + math.cos(a) * radius
            ty = cy - math.sin(a) * radius
            pygame.draw.circle(surface, rgb, (int(tx), int(ty)), size)

    def _draw_web(self, surface, r, ox, oy):
        """Sticky web strands over the knight while entangled."""
        cx, cy = r.centerx - ox, r.centery - oy
        col = (225, 225, 235)
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            ex = cx + math.cos(a) * 16
            ey = cy + math.sin(a) * 18
            pygame.draw.line(surface, col, (cx, cy), (ex, ey), 1)
        pygame.draw.circle(surface, col, (int(cx), int(cy)), 10, 1)
        pygame.draw.circle(surface, col, (int(cx), int(cy)), 16, 1)

    def _update_stamina(self, dt, sprinting):
        if sprinting:
            self.stamina = max(0.0, self.stamina - dt)
            self._regen_delay = settings.STAMINA_REGEN_DELAY
        else:
            if self._regen_delay > 0:
                self._regen_delay = max(0.0, self._regen_delay - dt)
            else:
                self.stamina = min(settings.STAMINA_MAX,
                                   self.stamina + settings.STAMINA_REGEN * dt)
