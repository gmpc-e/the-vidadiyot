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
        self.facing = 1             # 1 = right, -1 = left (for sprite flip)
        self._walk_t = 0.0          # animation clock
        self._moving = False
        self.swing = 0.0            # sword-swing effect timer
        self.webbed = False         # caught in Little Snir's web?
        self.struggle = 0           # Space presses left to break free
        self.frames = {}            # state name -> Surface

    # ── animation ────────────────────────────────────────────────────────--
    def set_frames(self, idle, walk, attack, hurt):
        """Install the warrior's four poses and pre-build the walk squash."""
        self.frames = {"idle": idle, "walk": walk, "attack": attack, "hurt": hurt}
        self.sprite = idle          # Entity.draw fallback
        squash = pygame.transform.smoothscale(
            walk, (walk.get_width(), max(1, int(walk.get_height() * 0.94))))
        self._walk_cycle = (walk, squash)

    @property
    def anim_state(self):
        if self.hurt_flash > 0:
            return "hurt"
        if self.swing > 0:
            return "attack"
        return "walk" if self._moving else "idle"

    def _current_frame(self):
        state = self.anim_state
        if state == "walk" and getattr(self, "_walk_cycle", None):
            return self._walk_cycle[int(self._walk_t * 7) % 2]
        return self.frames.get(state) or self.sprite

    @property
    def alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health = max(0.0, self.health - amount)
        self._dmg_delay = settings.PLAYER_REGEN_DELAY
        self.hurt_flash = 0.3       # long enough for the hurt pose to register

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

    def struggle_free(self):
        """One Space press worth of struggling. Returns True when freed."""
        if not self.webbed:
            return False
        self.struggle -= 1
        if self.struggle <= 0:
            self.webbed = False
            self.struggle = 0
            return True
        return False

    def _update_health(self, dt):
        if self.hurt_flash > 0:
            self.hurt_flash = max(0.0, self.hurt_flash - dt)
        if self._dmg_delay > 0:
            self._dmg_delay = max(0.0, self._dmg_delay - dt)
        elif self.health < self.max_health:
            self.health = min(self.max_health,
                              self.health + settings.PLAYER_HEALTH_REGEN * dt)

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
        bob = -1 if self._moving and int(self._walk_t * 7) % 2 else 0
        img = pygame.transform.flip(frame, True, False) if self.facing < 0 else frame
        lunge = self.facing * int(4 * (self.swing / settings.SWING_TIME)) if self.swing > 0 else 0
        sx = r.centerx - img.get_width() // 2 - ox + lunge
        sy = r.bottom - img.get_height() - oy + bob
        pygame.draw.ellipse(surface, (0, 0, 0),
                            pygame.Rect(r.centerx - 9 - ox, r.bottom - 4 - oy, 18, 6))
        surface.blit(img, (sx, sy))
        if self.swing > 0 and not self.throws:
            self._draw_swing(surface, r, ox, oy)
        if self.webbed:
            self._draw_web(surface, r, ox, oy)

    def _draw_swing(self, surface, r, ox, oy):
        """A bright crescent slash sweeping in front of the warrior."""
        progress = 1.0 - self.swing / settings.SWING_TIME     # 0 -> 1
        cx = r.centerx - ox + self.facing * 14
        cy = r.centery - oy - 2
        radius = 24
        box = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
        span = math.radians(75)
        if self.facing >= 0:
            a0 = math.radians(90 - progress * 165)
            a1 = a0 + span
        else:
            a1 = math.radians(90 + progress * 165)
            a0 = a1 - span
        # layered arcs -> a thick, glowing slash
        pygame.draw.arc(surface, (150, 180, 230), box.inflate(4, 4), a0, a1, 3)
        pygame.draw.arc(surface, (255, 255, 255), box, a0, a1, 5)
        pygame.draw.arc(surface, (230, 245, 255), box.inflate(-8, -8), a0, a1, 3)
        # bright leading tip
        tip = a0 if self.facing >= 0 else a1
        tx = cx + math.cos(tip) * radius
        ty = cy - math.sin(tip) * radius
        pygame.draw.circle(surface, (255, 255, 255), (int(tx), int(ty)), 3)

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
