"""Dead-zone follow camera with screen shake. See design doc §3.1.

The camera only scrolls when the target leaves a soft box in the middle of the
screen, so small movements don't jitter the whole view.
"""
import random
import pygame

import settings


class Camera:
    def __init__(self, view_size):
        self.view_w, self.view_h = view_size
        self.pos = pygame.Vector2(0, 0)     # top-left of the view in world space
        self._shake = 0.0                    # remaining shake time
        self._shake_mag = 0.0
        self.world_bounds = None             # optional pygame.Rect to clamp within

    def set_world_bounds(self, rect):
        self.world_bounds = rect

    def snap_to(self, target_center):
        self.pos.update(target_center[0] - self.view_w / 2,
                        target_center[1] - self.view_h / 2)
        self._clamp()

    def shake(self, magnitude, duration):
        self._shake = max(self._shake, duration)
        self._shake_mag = max(self._shake_mag, magnitude)

    def update(self, dt, target_center):
        tx, ty = target_center
        cx = self.pos.x + self.view_w / 2
        cy = self.pos.y + self.view_h / 2
        dzx, dzy = settings.CAMERA_DEADZONE

        if tx < cx - dzx:
            self.pos.x = tx + dzx - self.view_w / 2
        elif tx > cx + dzx:
            self.pos.x = tx - dzx - self.view_w / 2
        if ty < cy - dzy:
            self.pos.y = ty + dzy - self.view_h / 2
        elif ty > cy + dzy:
            self.pos.y = ty - dzy - self.view_h / 2

        if self._shake > 0:
            self._shake -= dt
            if self._shake <= 0:
                self._shake_mag = 0.0
        self._clamp()

    def _clamp(self):
        if self.world_bounds is None:
            return
        b = self.world_bounds
        self.pos.x = max(b.left, min(self.pos.x, b.right - self.view_w))
        self.pos.y = max(b.top, min(self.pos.y, b.bottom - self.view_h))

    @property
    def offset(self):
        """Subtract this from world coords to get screen coords."""
        ox, oy = self.pos.x, self.pos.y
        if self._shake > 0:
            ox += random.uniform(-self._shake_mag, self._shake_mag)
            oy += random.uniform(-self._shake_mag, self._shake_mag)
        return pygame.Vector2(round(ox), round(oy))

    def world_to_screen(self, world_pos):
        return pygame.Vector2(world_pos) - self.offset
