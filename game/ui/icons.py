"""Item icons — painted art where it exists, drawn in code where it doesn't.

Used in two places at once: world pickups and the HUD counters. That is why the
painted sprite is fetched *here* rather than in either caller — one swap, and
the book on the floor and the book in the counter stay the same object.

The procedural versions are kept, not as dead code but as the fallback: the
painted art is regenerated into `assets/` by `tools/extract_map_art.py` from
source that lives outside the repo, so a checkout that has never run the tools
still draws a readable key.

Only the **book** is tinted. It was painted deliberately neutral so the game can
colour it per classroom (§2.8); the key and the potion arrived already coloured,
and multiplying a room colour into them would just dirty them.
"""
import pygame

from game.core.assets import load

ITEM_SPRITES = {"key": "sprites/item_key.png",
                "book": "sprites/item_book.png",
                "bottle": "sprites/item_potion.png"}


TINT_STRENGTH = 0.62      # 0 = untinted, 1 = the raw room colour


def _soften(rgb):
    """Pull a room colour toward white before using it as a multiply.

    A straight multiply by a saturated colour is destructive: blue is
    (90, 140, 240), so the red channel of every pixel is scaled to 0.35 and the
    painted book's highlights, page edges and ribbon collapse into one blue
    blob. Lifting the colour toward white first keeps the painting's own shading
    and still reads unmistakably as "the blue book".
    """
    return tuple(int(c + (255 - c) * (1.0 - TINT_STRENGTH)) for c in rgb)


def _blit_item(surface, rect, name, tint=None):
    """Draw the painted item into `rect`, keeping its aspect. False if missing."""
    img = load(ITEM_SPRITES[name])
    if img is None:
        return False
    r = pygame.Rect(rect)
    scale = min(r.width / img.get_width(), r.height / img.get_height())
    size = (max(1, round(img.get_width() * scale)), max(1, round(img.get_height() * scale)))
    if size != img.get_size():
        img = pygame.transform.smoothscale(img, size)
    if tint:
        img = img.copy()
        img.fill((*_soften(tint), 255), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(img, (r.centerx - size[0] // 2, r.centery - size[1] // 2))
    return True


def draw_key(surface, rect, color=(240, 200, 80)):
    """A classic key: ring bow on the left, shaft, two teeth on the right."""
    if _blit_item(surface, rect, "key"):
        return
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
    if _blit_item(surface, rect, "bottle"):
        return
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
    if _blit_item(surface, rect, "book", tint=color):
        return
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
