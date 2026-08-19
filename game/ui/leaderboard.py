"""Draw a 'top players' leaderboard panel. Shared by the victory/defeat screens."""
import pygame

from game.ui.hud import format_time

W_PANEL = 260


def draw_board(surface, font, title_font, entries, center_x, top_y, highlight=None):
    title = title_font.render("TOP PLAYERS", True, (255, 220, 120))
    surface.blit(title, (center_x - title.get_width() // 2, top_y))
    y = top_y + title.get_height() + 8

    if not entries:
        empty = font.render("no times yet — be the first!", True, (200, 200, 210))
        surface.blit(empty, (center_x - empty.get_width() // 2, y))
        return

    x = center_x - W_PANEL // 2
    for i, e in enumerate(entries):
        is_me = highlight is not None and e["name"].strip().lower() == highlight.strip().lower()
        color = (140, 240, 160) if is_me else (225, 225, 235)
        rank = font.render(f"{i + 1}.", True, color)
        name = font.render(e["name"], True, color)
        tm = font.render(format_time(e["time"]), True, color)
        surface.blit(rank, (x, y))
        surface.blit(name, (x + 26, y))
        surface.blit(tm, (x + W_PANEL - tm.get_width(), y))
        y += font.get_height() + 4
