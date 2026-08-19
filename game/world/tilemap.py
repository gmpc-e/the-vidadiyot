"""TileMap: load a Tiled .tmx via pytmx, build a collision grid, draw it.

Collision is data-driven: any tile whose tileset entry has a `solid=true`
property is added to `self.solid` (a set of (tx, ty) tile coords). Gameplay code
asks for the solid tile rects overlapping a hitbox and resolves against them.
"""
import pygame
from pytmx.util_pygame import load_pygame


class TileMap:
    def __init__(self, path):
        self.tmx = load_pygame(path)
        self.tw = self.tmx.tilewidth
        self.th = self.tmx.tileheight
        self.cols = self.tmx.width
        self.rows = self.tmx.height
        self.px_w = self.cols * self.tw
        self.px_h = self.rows * self.th

        # only real tile layers (skip object groups / image layers)
        self._tile_layers = [l for l in self.tmx.layers if hasattr(l, "data")]
        self.solid = self._build_solid()

    # ── collision ──────────────────────────────────────────────────────────
    def _build_solid(self):
        solid = set()
        for layer in self._tile_layers:
            for y in range(self.rows):
                row = layer.data[y]
                for x in range(self.cols):
                    gid = row[x]
                    if gid == 0:
                        solid.add((x, y))          # empty tile = out of bounds
                        continue
                    props = self.tmx.get_tile_properties_by_gid(gid)
                    if props and props.get("solid"):
                        solid.add((x, y))
        return solid

    def solid_rects(self, rect):
        """Solid tile rects overlapping `rect`, for axis-separated resolution."""
        x0 = max(0, rect.left // self.tw)
        x1 = min(self.cols - 1, (rect.right - 1) // self.tw)
        y0 = max(0, rect.top // self.th)
        y1 = min(self.rows - 1, (rect.bottom - 1) // self.th)
        out = []
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if (tx, ty) in self.solid:
                    out.append(pygame.Rect(tx * self.tw, ty * self.th, self.tw, self.th))
        return out

    # ── objects ──────────────────────────────────────────────────────────--
    def objects(self):
        """Yield every object across all object groups."""
        for layer in self.tmx.layers:
            if hasattr(layer, "data"):   # tile layer, not an object group
                continue
            yield from layer

    def object_by_name(self, name):
        for obj in self.objects():
            if getattr(obj, "name", None) == name:
                return obj
        return None

    # ── rendering ──────────────────────────────────────────────────────────
    def draw(self, surface, camera):
        off = camera.offset
        sw, sh = surface.get_size()
        start_x = max(0, int(off.x) // self.tw)
        start_y = max(0, int(off.y) // self.th)
        end_x = min(self.cols, int(off.x + sw) // self.tw + 1)
        end_y = min(self.rows, int(off.y + sh) // self.th + 1)

        get_image = self.tmx.get_tile_image_by_gid
        for layer in self._tile_layers:
            for y in range(start_y, end_y):
                row = layer.data[y]
                for x in range(start_x, end_x):
                    gid = row[x]
                    if gid == 0:
                        continue
                    img = get_image(gid)
                    if img:
                        surface.blit(img, (x * self.tw - off.x, y * self.th - off.y))
