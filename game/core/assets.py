"""AssetManager: lazy-load and cache images, sounds, and fonts.

Everything is loaded on first request and cached by key, so systems can ask for
an asset without worrying about load order or double-loading.
"""
import os
import sys
import pygame

# Base dir for bundled read-only resources. When frozen by PyInstaller the files
# are extracted next to the app (sys._MEIPASS); otherwise use the project root.
if getattr(sys, "frozen", False):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "assets")


# The UI face. pygame's built-in font is very cramped at these sizes and falls
# apart badly with antialiasing off — thin, patchy, broken-looking glyphs. A
# wide, open face survives the hard edge; Verdana is the best of what ships on
# the target machines, with the built-in as the fallback elsewhere.
UI_FONT = "verdana"
# Verdana runs larger than the built-in for the same nominal size. This factor
# matches their *widths*, so every existing layout — centered rows, wrapped
# paragraphs, the menu fit — keeps working without retuning each call site.
UI_FONT_SCALE = 0.68


class CrispFont:
    """A pygame Font that never antialiases, in a face that survives it.

    Everything is drawn to a 640x360 surface and then integer-scaled up, so a
    glyph blurred by antialiasing gets its blur magnified along with it — text
    ends up soft and muddy next to the hard-edged pixel art. Forcing antialias
    off here rather than at ~30 call sites means no render site can reintroduce
    it by passing `True`, which is exactly what they all used to do.
    """

    def __init__(self, path, size):
        if path is None:
            self._font = self._ui_font(size)
        else:
            self._font = pygame.font.Font(path, size)

    @staticmethod
    def _ui_font(size):
        scaled = max(8, round(size * UI_FONT_SCALE))
        try:
            if pygame.font.match_font(UI_FONT):
                return pygame.font.SysFont(UI_FONT, scaled)
        except Exception:
            pass
        return pygame.font.Font(None, size)

    def render(self, text, antialias=True, color=(255, 255, 255), *args, **kwargs):
        return self._font.render(text, False, color, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._font, name)


_SHARED = {}


def load(rel_path):
    """Module-level cached image load, or None if the file isn't there.

    `AssetManager` is the normal route, but drawing code deep in entities and UI
    has no handle on one — passing an asset manager down to `Door.draw` just to
    fetch one sprite is worse than a module cache. Missing returns None so every
    caller can keep its procedural drawing as a fallback: the painted art lives
    in ~/Downloads and is *regenerated* into `assets/`, so a checkout that has
    never run the tools still has to render something.
    """
    if rel_path not in _SHARED:
        path = os.path.join(ASSETS, rel_path)
        try:
            _SHARED[rel_path] = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            _SHARED[rel_path] = None
    return _SHARED[rel_path]


class AssetManager:
    def __init__(self):
        self._images = {}
        self._sounds = {}
        self._fonts = {}

    def image(self, rel_path):
        if rel_path not in self._images:
            path = os.path.join(ASSETS, rel_path)
            self._images[rel_path] = pygame.image.load(path).convert_alpha()
        return self._images[rel_path]

    def sound(self, rel_path):
        if rel_path not in self._sounds:
            path = os.path.join(ASSETS, rel_path)
            self._sounds[rel_path] = pygame.mixer.Sound(path)
        return self._sounds[rel_path]

    def font(self, rel_path, size):
        key = (rel_path, size)
        if key not in self._fonts:
            path = os.path.join(ASSETS, rel_path) if rel_path else None
            self._fonts[key] = CrispFont(path, size)
        return self._fonts[key]
