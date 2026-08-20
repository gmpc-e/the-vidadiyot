"""Zina — Roni's dog, thrown at a monster and recalled (the "Royal Bond" power).

She is not a projectile that happens to be a dog: she picks a *target*, runs it
down even as it moves, latches on, and then trots home to Roni. That round trip
is the cost of the power — while Zina is out, Roni has nothing to send, and she
is deliberately slow enough to watch.

Sound follows the `cast_request` pattern used by the casters: she never touches
the audio system, she just raises `sound_request` and PlayState plays it.

A bite kills outright, so the balancing lives in `settings.ZINA_*`: a hard charge
count per level, a leash range, and the time the trip takes.
"""
import math
import pygame

import settings
from game.entities.entity import Entity

FUR = (176, 132, 74)
FUR_DARK = (74, 54, 34)
ARMOR = (150, 152, 162)


class Zina(Entity):
    """States: out -> bite -> back -> done (`self.done` tells PlayState to drop her)."""

    OUT, BITE, BACK = "out", "bite", "back"

    def __init__(self, owner, target, sprite=None, painted_bite=False):
        w, h = settings.ZINA_SIZE
        super().__init__(owner.pos.x, owner.pos.y, w, h)
        self.owner = owner
        self.target = target
        self.sprite = sprite
        # True when PlayState has a painted bite splash to show instead of the
        # drawn white star — see `_draw_bite`.
        self.painted_bite = painted_bite
        self.state = self.OUT
        self.timer = 0.0
        self.done = False
        self.facing = 1
        self.killed = None          # the monster she bit, handed back to PlayState
        self.sound_request = None   # a sound name for PlayState to play, once
        self._bark_t = 0.0

    def update(self, dt):
        self._bark(dt)
        if self.state == self.OUT:
            self._run_to(dt, self._target_pos())
            if self.target is None or self.target.dead:
                self.state = self.BACK          # target died first — just come home
            elif self.pos.distance_to(self.target.pos) <= 20:
                self.state, self.timer = self.BITE, settings.ZINA_BITE_TIME
                self.killed = self.target
                self.sound_request = "zina_bite"
        elif self.state == self.BITE:
            self.pos.update(self._target_pos())   # ride the monster while latched
            self.timer -= dt
            if self.timer <= 0:
                self.state = self.BACK
        else:
            self._run_to(dt, self.owner.pos)
            if self.pos.distance_to(self.owner.pos) <= 16:
                self.done = True

    def _bark(self, dt):
        """Bark on the way out and on the way home — not while her mouth is full."""
        if self.state == self.BITE:
            return
        self._bark_t -= dt
        if self._bark_t <= 0:
            self.sound_request = self.sound_request or "zina_bark"
            self._bark_t = settings.ZINA_BARK_EVERY

    def _target_pos(self):
        return self.target.pos if self.target else self.owner.pos

    def _run_to(self, dt, point):
        d = pygame.Vector2(point) - self.pos
        if d.length() > 1:
            self.facing = 1 if d.x >= 0 else -1
            self.pos += d.normalize() * settings.ZINA_SPEED * dt

    # ── draw ─────────────────────────────────────────────────────────────--
    def draw(self, surface, camera):
        r = self.hitbox
        ox, oy = round(camera.offset.x), round(camera.offset.y)
        cx, cy = r.centerx - ox, r.centery - oy
        if self.sprite:
            img = self.sprite if self.facing >= 0 else pygame.transform.flip(
                self.sprite, True, False)
            surface.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))
        else:
            pygame.draw.ellipse(surface, FUR, (cx - 12, cy - 7, 24, 14))
            pygame.draw.circle(surface, FUR_DARK, (int(cx + 9 * self.facing), int(cy - 4)), 5)
        if self.state == self.BITE:
            if not self.painted_bite:
                self._draw_bite(surface, cx, cy)
        else:
            self._draw_dust(surface, cx, cy)

    def _draw_bite(self, surface, cx, cy):
        """A white impact star — the **fallback**, for a checkout with no art.

        ⚠️ This used to draw on every bite, and once `bite_splash.png` landed it
        was a second effect on top of the painted one: a white spoked star over a
        red burst, which read as a glitch rather than as a kill. `painted_bite`
        is set by PlayState when the art is installed.
        """
        for i in range(8):
            a = i * math.tau / 8 + self.timer * 8
            r0, r1 = 8, 17
            pygame.draw.line(surface, (255, 250, 235),
                             (cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                             (cx + math.cos(a) * r1, cy + math.sin(a) * r1), 2)

    def _draw_dust(self, surface, cx, cy):
        pygame.draw.circle(surface, ARMOR, (int(cx - 11 * self.facing), int(cy + 5)), 2)
