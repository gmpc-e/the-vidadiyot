"""Title menu + How-to-play + Leaderboard screens.

Keyboard-driven (Up/Down to move, Left/Right to change difficulty, Enter to
select, Esc to quit). The painted title art is the hero (see `tools/make_title.py`);
the knight faces off against both Vidadiyot at the edges while the funky loop plays.
"""
import math
import pygame

import settings
from game.core.state import State
from game.systems import difficulty, scores
from game.entities import warriors
from game.ui.leaderboard import draw_board

W, H = settings.INTERNAL_RES
ITEMS = ["play", "warrior", "difficulty", "howto", "leaderboard", "quit"]
LABELS = {"play": "Play", "howto": "How to Play",
          "leaderboard": "Leaderboard", "quit": "Quit"}

# Title block layout. The art is 460x184 + a 310x32 mace-bar rule under it,
# leaving the bottom ~135px for the six menu rows and the key tip. The rows are
# tight against the tip line, so nudging any of these means re-checking the fit.
TITLE_Y     = 2
RULE_GAP    = 2
MENU_TOP    = 224
MENU_STEP   = 20

# Selected row: a crimson plate behind bright text, picking up the title art's
# blood palette. This replaces the old "> " caret and the "< Normal >" arrows —
# one highlight says "you are here" for every row, including difficulty.
SEL_TEXT    = (255, 226, 150)
ROW_TEXT    = (198, 198, 214)
SEL_PLATE   = (122, 18, 24, 190)
SEL_EDGE    = (198, 52, 46)
SEL_PAD     = (14, 3)          # x, y padding around the row text

# Warrior-select art box: portraits are fitted into this, never drawn larger.
PORTRAIT_BOX = (196, 200)
PORTRAIT_CX = 108


class MenuState(State):
    def enter(self):
        self.game.audio.play_music("menu")   # the title screen's own theme
        self.sel = 0
        self.t = 0.0
        self.font_big = self.game.assets.font(None, 40)
        self.font = self.game.assets.font(None, 20)
        self.small = self.game.assets.font(None, 14)
        # menu-size crops off the original sheets: the old 48px game sprites
        # had to be scaled *up* here, which read as mush
        self.snir = self.game.assets.image("sprites/snir_menu.png")
        self.terror = self.game.assets.image("sprites/terror_menu.png")
        self.emri = self.game.assets.image("sprites/emri_menu.png")
        self.title = self.game.assets.image("ui/title.png")
        self.title_rule = self.game.assets.image("ui/title_rule.png")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.sel = (self.sel + 1) % len(ITEMS)
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.sel = (self.sel - 1) % len(ITEMS)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._nudge_difficulty(-1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self._nudge_difficulty(1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate()
        elif event.key in (pygame.K_ESCAPE, pygame.K_q):
            self.game.running = False

    def _nudge_difficulty(self, d):
        """Left/Right adjusts whichever row is active, without entering it.

        The warrior row can be flipped in place as well as opened — most of the
        time you already know who you want, and opening a page to press Right
        once and back out is three keys too many.
        """
        row = ITEMS[self.sel]
        if row == "difficulty":
            self.game.difficulty = difficulty.cycle(self.game.difficulty, d)
        elif row == "warrior":
            ids = [w["id"] for w in warriors.WARRIORS]
            i = ids.index(self._warrior["id"])
            self.game.warrior = ids[(i + d) % len(ids)]

    def _activate(self):
        choice = ITEMS[self.sel]
        if choice == "play":
            from game.core.play_state import PlayState
            self.game.switch(PlayState(self.game))
        elif choice == "warrior":
            self.game.push(WarriorSelectState(self.game))
        elif choice == "difficulty":
            self._nudge_difficulty(1)
        elif choice == "howto":
            self.game.push(HowToState(self.game))
        elif choice == "leaderboard":
            self.game.push(LeaderboardState(self.game))
        elif choice == "quit":
            self.game.running = False

    @property
    def _warrior(self):
        return warriors.get(getattr(self.game, "warrior", warriors.DEFAULT_ID))

    def update(self, dt, inp):
        self.t += dt

    def draw(self, surface):
        surface.fill((16, 16, 22))
        self._draw_grid(surface)
        self._draw_duel(surface)
        self._draw_title(surface)

        y = MENU_TOP
        for i, key in enumerate(ITEMS):
            if key == "difficulty":
                label = f"Difficulty:  {self.game.difficulty}"
            elif key == "warrior":
                label = f"Select your Warrior:  {self._warrior['name']}"
            else:
                label = LABELS[key]
            selected = i == self.sel
            text = self.font.render(label, True, SEL_TEXT if selected else ROW_TEXT)
            x = (W - text.get_width()) // 2
            if selected:
                self._draw_selection(surface, text.get_rect(topleft=(x, y)))
            surface.blit(text, (x, y))
            y += MENU_STEP

        # Difficulty lost its "< >" arrows to the highlight, so the tip line
        # carries the left/right affordance while that row is the active one.
        row = ITEMS[self.sel]
        if row == "difficulty":
            hint = "Left / Right: change difficulty   Enter: select   Q: quit"
        elif row == "warrior":
            hint = "Left / Right: switch warrior   Enter: see details   Q: quit"
        else:
            hint = "Arrows: move   Enter: select   Q / Esc: quit"
        tip = self.small.render(hint, True, (130, 130, 145))
        surface.blit(tip, ((W - tip.get_width()) // 2, H - 14))

    def _draw_selection(self, surface, text_rect):
        """Crimson plate behind the active row — the only selection cue."""
        plate = text_rect.inflate(SEL_PAD[0] * 2, SEL_PAD[1] * 2)
        fill = pygame.Surface(plate.size, pygame.SRCALPHA)
        pygame.draw.rect(fill, SEL_PLATE, fill.get_rect(), border_radius=3)
        surface.blit(fill, plate.topleft)
        pygame.draw.rect(surface, SEL_EDGE, plate, 1, border_radius=3)

    def _draw_title(self, surface):
        surface.blit(self.title, ((W - self.title.get_width()) // 2, TITLE_Y))
        y = TITLE_Y + self.title.get_height() + RULE_GAP
        surface.blit(self.title_rule, ((W - self.title_rule.get_width()) // 2, y))

    def _draw_grid(self, surface):
        for x in range(0, W, settings.TILE):
            pygame.draw.line(surface, (24, 24, 32), (x, 0), (x, H))
        for y in range(0, H, settings.TILE):
            pygame.draw.line(surface, (24, 24, 32), (0, y), (W, y))

    def _draw_duel(self, surface):
        """The two warriors face off against all three Vidadiyot.

        Everyone bobs on their own phase offset, so the two sides read as a row
        of individuals rather than one rigid block sliding up and down. The
        currently-chosen warrior stands forward and slightly larger.
        """
        chosen = self._warrior["id"]
        heroes = []
        for w in warriors.WARRIORS:
            # ⚠️ Named, not derived from the id. It *was* f"{w['id']}_menu.png",
            # which quietly made the warrior's id part of an asset path — so
            # renaming the character broke the select screen.
            img = self.game.assets.image(f"sprites/{w['menu']}.png")
            heroes.append((img, 76 if w["id"] == chosen else 62))

        x = 12
        for i, (img, height) in enumerate(heroes):
            scaled = self._scaled(img, height)
            surface.blit(scaled, (x, H - 30 - scaled.get_height() + self._bob(i)))
            x += scaled.get_width() + 4

        monsters = [(self.terror, 70), (self.snir, 68), (self.emri, 74)]
        drawn = [self._scaled(img, h) for img, h in monsters]
        x = W - 12 - sum(m.get_width() + 4 for m in drawn)
        for i, m in enumerate(drawn):
            surface.blit(pygame.transform.flip(m, True, False),
                         (x, H - 30 - m.get_height() + self._bob(i + len(heroes))))
            x += m.get_width() + 4

    def _bob(self, i):
        """Per-character bob, offset in phase so nobody moves in lockstep."""
        return math.sin(self.t * 2.6 + i * 1.7) * 3

    @staticmethod
    def _scaled(img, height):
        """Smooth downscale — these sources are larger than the slot, and
        nearest-neighbour on painted art is exactly what looked pixelated."""
        w = max(1, round(img.get_width() * height / img.get_height()))
        return pygame.transform.smoothscale(img, (w, height))


class _BackScreen(State):
    """Shared: a pushed sub-screen dismissed with Esc/Enter."""
    draw_below = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.game.pop()

    def update(self, dt, inp):
        pass

    def _header(self, surface, title, tip="Esc / Enter: back"):
        surface.fill((16, 16, 22))
        t = self.game.assets.font(None, 30).render(title, True, (255, 220, 120))
        surface.blit(t, ((W - t.get_width()) // 2, 20))
        if tip:
            surf = self.game.assets.font(None, 14).render(tip, True, (140, 140, 155))
            surface.blit(surf, ((W - surf.get_width()) // 2, H - 20))


class HowToState(_BackScreen):
    LINES = [
        "Goal:  return every book to its matching-color classroom.",
        "",
        "Move ...... WASD / Arrow keys      Sprint .... Shift (stamina)",
        "Interact .. E  (unlock doors, return books)",
        "Attack .... Space  (Wallad swings, Roni throws knives)",
        "Power ..... Z  (Roni only: send Zina - 3 bites, kills outright)",
        "Mute ...... M      Pause ..... Esc      Quit ...... Q",
        "",
        "Pick your warrior in the menu (Left/Right on that row):",
        "Wallad hits for two pips and takes more punishment.",
        "Roni is faster and fights at range, but one pip a knife.",
        "",
        "Keys unlock the colored classroom doors. Little Terror throws",
        "fireballs, Little Snir throws sticky webs - if webbed, MASH SPACE!",
        "A monster guards each book: kill it to free the book, then carry",
        "the book to the matching classroom. Grab potions to heal.",
    ]

    def draw(self, surface):
        self._header(surface, "HOW TO PLAY")
        font = self.game.assets.font(None, 15)
        y = 56
        for line in self.LINES:
            surface.blit(font.render(line, True, (215, 215, 228)), (30, y))
            y += 18


class LeaderboardState(_BackScreen):
    def draw(self, surface):
        surface.fill((16, 16, 22))
        draw_board(surface, self.game.assets.font(None, 18),
                   self.game.assets.font(None, 24), scores.top(10), W // 2, 40)
        tip = self.game.assets.font(None, 14).render("Esc / Enter: back", True, (140, 140, 155))
        surface.blit(tip, ((W - tip.get_width()) // 2, H - 20))


class WarriorSelectState(_BackScreen):
    """Pick who goes into the school. Left/Right to flip, Enter to take them.

    One warrior per page rather than a row of cards: at 640x360 a card carrying a
    portrait, a blurb, a stat block *and* a power description does not survive
    being shrunk to a third of the screen.
    """
    def enter(self):
        ids = [w["id"] for w in warriors.WARRIORS]
        current = getattr(self.game, "warrior", warriors.DEFAULT_ID)
        self.i = ids.index(current) if current in ids else 0
        self.t = 0.0

    @property
    def warrior(self):
        return warriors.WARRIORS[self.i]

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.i = (self.i - 1) % len(warriors.WARRIORS)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.i = (self.i + 1) % len(warriors.WARRIORS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            self.game.warrior = self.warrior["id"]      # Esc confirms too: the
            self.game.pop()                              # page always shows one

    def update(self, dt, inp):
        self.t += dt

    def draw(self, surface):
        w = self.warrior
        surface.fill((16, 16, 22))
        self._header(surface, "SELECT YOUR WARRIOR", tip=None)
        self._draw_portrait(surface, w)
        self._draw_details(surface, w)
        self._draw_arrows(surface)

    def _draw_portrait(self, surface, w):
        """Full-size painted art, drawn 1:1.

        Blowing the 48px game sprite up to portrait size was nearest-neighbour
        mush; each warrior gets its own crop off the original sheet instead.
        """
        img = self.game.assets.image(f"sprites/{w['portrait']}.png")
        # fit inside the art box rather than trusting the crop's aspect: a wide
        # portrait would otherwise slide off the left edge and cover the arrow
        fit = min(PORTRAIT_BOX[0] / img.get_width(), PORTRAIT_BOX[1] / img.get_height(), 1.0)
        if fit < 1.0:
            img = pygame.transform.smoothscale(
                img, (max(1, int(img.get_width() * fit)), max(1, int(img.get_height() * fit))))
        x = PORTRAIT_CX - img.get_width() // 2
        y = 274 - img.get_height() + int(math.sin(self.t * 2.6) * 2)
        surface.blit(img, (x, y))

    def _draw_details(self, surface, w):
        font = self.game.assets.font(None, 22)
        small = self.game.assets.font(None, 15)
        tiny = self.game.assets.font(None, 14)
        x, y = 226, 56
        surface.blit(font.render(w["name"].upper(), True, (255, 226, 150)), (x, y))
        y += 22
        surface.blit(small.render(w["title"], True, (198, 160, 235)), (x, y))
        y += 22
        for line in w["blurb"]:
            surface.blit(tiny.render(line, True, (206, 206, 220)), (x, y))
            y += 16
        y += 8
        for key in ("HP", "ATK", "DEF", "SPD"):
            surface.blit(tiny.render(key, True, (150, 150, 168)), (x, y))
            surface.blit(tiny.render(str(w["card"][key]), True, (235, 235, 246)), (x + 34, y))
            y += 15
        # Power block, sized to its own text: Roni's now names two abilities and
        # a fixed-height panel simply spilled the last line out of the box.
        y = 210
        lines = self._wrap(w["power_help"], tiny, 388)
        box_h = 24 + len(lines) * 15
        pygame.draw.rect(surface, (44, 22, 58), (x - 6, y - 4, 402, box_h), border_radius=3)
        pygame.draw.rect(surface, (128, 74, 168), (x - 6, y - 4, 402, box_h), 1,
                         border_radius=3)
        surface.blit(small.render(w["power_name"], True, (222, 176, 255)), (x, y))
        y += 20
        for line in lines:
            surface.blit(tiny.render(line, True, (214, 210, 224)), (x, y))
            y += 15

    def _draw_arrows(self, surface):
        font = self.game.assets.font(None, 24)
        pulse = 190 + int(60 * math.sin(self.t * 5))
        for text, x in (("<", 8), (">", W - 22)):
            surface.blit(font.render(text, True, (pulse, pulse, 210)), (x, 150))
        tip = self.game.assets.font(None, 14).render(
            f"Left / Right: choose   Enter: take {self.warrior['name']} in   Esc: back",
            True, (140, 140, 155))
        surface.blit(tip, ((W - tip.get_width()) // 2, H - 20))

    @staticmethod
    def _wrap(text, font, width):
        lines, line = [], ""
        for word in text.split():
            trial = f"{line} {word}".strip()
            if font.size(trial)[0] <= width:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines
