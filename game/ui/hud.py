"""HUD: key/book counters (with icons), health, stamina, inventory, timer, hint.

Reads live state passed in each frame. Drawn at the 640x360 internal resolution.
"""
import pygame

import settings
from game.entities.pickup import item_color
from game.ui.icons import draw_key, draw_book


def format_time(seconds):
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:01d}:{s:02d}"


class HUD:
    def __init__(self, assets, quests, inventory):
        self.font = assets.font(None, 14)
        self.big = assets.font(None, 18)
        self.quests = quests
        self.inv = inventory

    def draw(self, surface, player, counters, hint=None, elapsed=0.0, flashes=None):
        """`flashes` maps an icon name to a 0..1 intensity (see roadmap §6)."""
        self._draw_counters(surface, counters, flashes or {})
        self._draw_health(surface, player)
        self._draw_stamina(surface, player)
        self._draw_inventory(surface)
        self._draw_timer(surface, elapsed)
        self._draw_power(surface, player)
        if hint:
            self._draw_hint(surface, hint)

    def _draw_counters(self, surface, counters, flashes):
        """counters: list of (icon_name, progress, required)."""
        x, y = 8, 8
        for icon_name, progress, required in counters:
            flash = max(0.0, min(1.0, flashes.get(icon_name, 0.0)))
            rect = pygame.Rect(x, y, 18, 18)
            if flash:
                self._draw_counter_glow(surface, rect, flash)
            if icon_name == "key":
                draw_key(surface, rect)
            else:
                draw_book(surface, rect)
            done = progress >= required
            color = (140, 220, 150) if done else (235, 235, 245)
            if flash:      # wash the counter toward a bright gold as it pulses
                color = tuple(int(c + (g - c) * flash)
                              for c, g in zip(color, (255, 240, 170)))
            self._shadow_text(surface, self.big, f"{progress}/{required}",
                              (x + 24, y - 1), color)
            x += 78

    def _draw_counter_glow(self, surface, icon_rect, flash):
        """A soft halo that expands and fades behind a counter that just ticked."""
        pad = int(3 + 7 * flash)
        area = icon_rect.inflate(pad * 2 + 44, pad * 2)
        glow = pygame.Surface(area.size, pygame.SRCALPHA)
        pygame.draw.rect(glow, (255, 225, 130, int(90 * flash)),
                         glow.get_rect(), border_radius=6)
        surface.blit(glow, area.topleft)

    def _draw_health(self, surface, player):
        w, h = 120, 9
        x, y = 8, settings.INTERNAL_RES[1] - 30
        pct = max(0.0, player.health / player.max_health)
        col = (90, 210, 110) if pct > 0.5 else (230, 200, 70) if pct > 0.25 else (230, 80, 80)
        pygame.draw.rect(surface, (40, 30, 32), (x, y, w, h))
        pygame.draw.rect(surface, col, (x, y, int(w * pct), h))
        pygame.draw.rect(surface, (80, 70, 74), (x, y, w, h), 1)
        heart = self.font.render("HP", True, (230, 210, 210))
        surface.blit(heart, (x + w + 4, y - 2))

    def _draw_stamina(self, surface, player):
        w, h = 120, 5
        x, y = 8, settings.INTERNAL_RES[1] - 16
        pct = player.stamina / settings.STAMINA_MAX
        pygame.draw.rect(surface, (30, 34, 38), (x, y, w, h))
        pygame.draw.rect(surface, (120, 200, 220), (x, y, int(w * pct), h))

    def _draw_inventory(self, surface):
        slot, gap = 20, 4
        total = self.inv.capacity * slot + (self.inv.capacity - 1) * gap
        x = settings.INTERNAL_RES[0] - total - 8
        y = settings.INTERNAL_RES[1] - slot - 8
        for i in range(self.inv.capacity):
            rect = pygame.Rect(x + i * (slot + gap), y, slot, slot)
            pygame.draw.rect(surface, (30, 30, 38), rect)
            pygame.draw.rect(surface, (70, 70, 82), rect, 1)
            if i < len(self.inv.items):
                item_type, variant = self.inv.items[i]
                inner = rect.inflate(-4, -4)
                if item_type == "key":
                    draw_key(surface, inner, item_color(item_type, variant))
                elif item_type == "book":
                    draw_book(surface, inner, item_color(item_type, variant))
                else:
                    pygame.draw.rect(surface, item_color(item_type, variant), inner)

    def _draw_power(self, surface, player):
        """Charges of the warrior's active power, as pips beside the stamina bar.

        Only drawn for warriors that have one — Wallad's row would be permanently
        empty, which reads as a bug rather than as "he has no power".
        """
        if not player.power:
            return
        x, y = 136, settings.INTERNAL_RES[1] - 17
        label = self.font.render("Z", True, (225, 205, 245))
        surface.blit(label, (x, y - 2))
        x += label.get_width() + 4
        for i in range(settings.ZINA_CHARGES):
            rect = pygame.Rect(x + i * 9, y, 7, 7)
            if i < player.power_charges:
                pygame.draw.rect(surface, (205, 130, 235), rect)
                pygame.draw.rect(surface, (245, 220, 255), rect, 1)
            else:
                pygame.draw.rect(surface, (58, 48, 66), rect, 1)

    def _draw_timer(self, surface, elapsed):
        text = format_time(elapsed)
        surf = self.big.render(text, True, (235, 235, 245))
        x = settings.INTERNAL_RES[0] - surf.get_width() - 8
        surface.blit(self.big.render(text, True, (0, 0, 0)), (x + 1, 9))
        surface.blit(surf, (x, 8))

    def _draw_hint(self, surface, hint):
        w = settings.INTERNAL_RES[0]
        surf = self.font.render(hint, True, (245, 245, 250))
        x = (w - surf.get_width()) // 2
        y = settings.INTERNAL_RES[1] - 46
        bg = pygame.Rect(x - 6, y - 3, surf.get_width() + 12, surf.get_height() + 6)
        panel = pygame.Surface(bg.size, pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        surface.blit(panel, bg.topleft)
        surface.blit(surf, (x, y))

    def _shadow_text(self, surface, font, text, pos, color):
        x, y = pos
        surface.blit(font.render(text, True, (0, 0, 0)), (x + 1, y + 1))
        surface.blit(font.render(text, True, color), (x, y))
