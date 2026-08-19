"""Procedural key & book icons, drawn into a rect.

Drawn in code (no external art) so they scale to any size and can be tinted —
used both for world pickups and the HUD counters.
"""
import pygame


def draw_key(surface, rect, color=(240, 200, 80)):
    """A classic key: ring bow on the left, shaft, two teeth on the right."""
    r = pygame.Rect(rect)
    cy = r.centery
    ring_r = max(3, r.height // 3)
    ring_c = (r.left + ring_r, cy)
    outline = (30, 26, 12)
    # shaft
    shaft_x0 = ring_c[0] + ring_r - 1
    pygame.draw.line(surface, color, (shaft_x0, cy), (r.right - 2, cy), max(2, r.height // 6))
    # teeth
    th = max(3, r.height // 4)
    pygame.draw.line(surface, color, (r.right - 3, cy), (r.right - 3, cy + th), max(2, r.height // 8))
    pygame.draw.line(surface, color, (r.right - 8, cy), (r.right - 8, cy + th), max(2, r.height // 8))
    # ring (bow)
    pygame.draw.circle(surface, color, ring_c, ring_r)
    pygame.draw.circle(surface, outline, ring_c, ring_r, 1)
    pygame.draw.circle(surface, (20, 18, 22), ring_c, max(1, ring_r // 2))


def draw_bottle(surface, rect, color=(230, 70, 80)):
    """A little health potion: glass body with colored liquid, neck and cork."""
    r = pygame.Rect(rect)
    bw = max(6, r.width - 6)
    body = pygame.Rect(r.centerx - bw // 2, r.top + r.height // 3, bw, r.height - r.height // 3 - 1)
    neck = pygame.Rect(r.centerx - 2, r.top + 2, 4, r.height // 3)
    cork = pygame.Rect(r.centerx - 2, r.top, 4, 3)
    pygame.draw.rect(surface, (210, 225, 235), neck)                 # glass neck
    pygame.draw.rect(surface, (225, 235, 245), body, border_radius=2)  # glass body
    liquid = body.inflate(-2, -2)
    liquid.height = int(liquid.height * 0.7); liquid.bottom = body.bottom - 1
    pygame.draw.rect(surface, color, liquid, border_radius=2)         # potion
    pygame.draw.rect(surface, (150, 90, 60), cork)                    # cork
    pygame.draw.rect(surface, (30, 30, 36), body, 1, border_radius=2)


def draw_book(surface, rect, color=(120, 180, 240)):
    """A closed book: colored cover, darker spine, page edge."""
    r = pygame.Rect(rect).inflate(-2, 0)
    spine = pygame.Rect(r.left, r.top, max(3, r.width // 5), r.height)
    darker = tuple(max(0, c - 60) for c in color)
    lighter = (240, 240, 235)
    pygame.draw.rect(surface, color, r, border_radius=2)
    pygame.draw.rect(surface, darker, spine, border_radius=1)          # spine
    # page edge on the right
    page = pygame.Rect(r.right - 3, r.top + 2, 3, r.height - 4)
    pygame.draw.rect(surface, lighter, page)
    pygame.draw.rect(surface, (25, 25, 30), r, 1, border_radius=2)     # outline
