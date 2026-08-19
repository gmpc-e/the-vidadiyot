# The Vidadiyot and the Banished
### *הווידאדיות והמנודים* — 2D Python Game Design & Architecture Document

---

## PART 1 — TRANSLATED CONCEPT

### Title
**The Vidadiyot and the Banished**

- **Vidadiyot** (ווידאדיות) — an invented word, kept transliterated. Treat it as a proper noun/creature species name.
- **The Banished** (המנודים) — from the Hebrew root *nidui* (excommunication/banishment). These are the ones cast out of the school.

### Story

A group of kids sneaks into an old school that was abandoned years ago. They say that at night the **Vidadiyot** and the **Banished** appear there — mysterious creatures that guard the place. To escape, you have to complete a set of tasks before the monsters catch everyone.

### Chapter 1 — The School

| # | Task | Detail |
|---|------|--------|
| 1 | 🔑 **Find 10 keys** | Each key unlocks one of the locked classrooms. |
| 2 | 📚 **Find 10 textbooks** | Return each book to its matching classroom. |
| 3 | 💡 **Restore power** | Find 6 fuses → insert them into the electrical panel → switch the power on. |
| — | 🚨 **When power returns…** | An alarm sounds and **all monsters become faster.** |
| 4 | 🧪 **Find 5 staff ID cards** | They open the principal's office, which holds the final key to the school. |
| 5 | 📻 **Activate the PA system** | It broadcasts a rescue message. |
| 6 | 🚪 **Open the main gate and escape** | Get out before the monsters reach you. |

### Map Areas

🏫 Main entrance · 🏃 Long corridor · 📚 10 classrooms · 🔬 Science lab · 💻 Computer room · 🎨 Art room · 🎵 Music room · 📖 Library · 🍽️ Cafeteria · 🏀 Gymnasium · 🩺 Nurse's office · 👨‍🏫 Teachers' lounge · 👔 Principal's office · ⚡ Electrical room · 🚻 Bathrooms · 🧹 Supply closet · 🌳 Schoolyard · 🚪 Exit gate

### Random Events

Different events fire in every playthrough:

- ⚡ Power outage
- 🌫️ Fog in the corridors
- 🔔 The school bell rings
- 🚪 Certain doors re-lock themselves
- 📢 Mysterious announcements over the PA
- 💨 A strong gust of wind slams doors shut

---

## PART 2 — DESIGN DECISIONS (read this before coding)

These are the choices that shape the whole codebase. Lock them in first.

### 2.1 Genre & camera
**Top-down 2D, tile-based, single continuous map.** Not room-by-room scene loading. A chase is only scary if it can follow you through a doorway — loading screens kill tension. Camera follows the player with a soft dead-zone.

### 2.2 Tile size: 32×32 px
The whole school at 32px fits comfortably in a ~180×140 tile map. Player sprite is 24×32 (slightly narrower than a tile so doorways feel forgiving). Internal render resolution **640×360**, scaled up integer-wise to the window — this gives crisp pixel art and makes the "dark school" lighting cheap to compute.

### 2.3 Two monster types, deliberately different
The title names two creatures, so they must *play* differently. This is the single biggest gameplay win available.

| | **Vidadiyot** | **The Banished** |
|---|---|---|
| Sense | **Sight** — vision cone, blocked by walls | **Sound** — hears sprinting, dropped items, doors, the PA |
| Movement | Fast bursts, then pauses to "scan" | Slow, relentless, never stops |
| Counter | Break line of sight; hide in lockers/under desks | Walk (don't sprint); move away from noise |
| Behavior | Roams a wing, patrols corridors | Wanders toward the last noise it heard |
| Count | 2 (3 after the alarm) | 1 (2 after the alarm) |

Because their counters are opposite (hide vs. keep moving quietly), rooms with both create real decisions.

### 2.4 Getting caught — no death
The player is a kid; so, probably, is the audience. Recommended:

> Getting caught = you're dragged to the **nurse's office**, you **drop 2 random carried items** back where you were caught, and the monsters get a 10-second "confused" cooldown.

You lose *time and progress*, never the run. Add a `HARD_MODE` flag in settings that turns 3 catches into a game over, for when you want stakes.

### 2.5 The lighting hook
Before power is restored, the school is **dark**: the player has a weak flashlight cone plus a small ambient radius. After Task 3, lights come on — the school becomes fully visible, *but* the alarm makes everything faster and the Vidadiyot's vision range increases.

This is the central risk/reward of the whole game: **you trade safety for visibility.** Make sure Tasks 4–6 are all designed around a bright, fast, dangerous school.

### 2.6 Task pacing — gate, don't serialize
Tasks 1 and 2 should be **simultaneously active**, not sequential. Keys unlock classrooms; books need to go *into* those classrooms. Forcing all 10 keys before touching a book means 10 boring minutes of the same activity.

Recommended gating:

```
Tasks 1 + 2  →  active from the start, interleaved
Task 3       →  fuses spawn from the start; the panel needs all 6
                (the electrical room door needs Key #7, so Task 1 gates it naturally)
Task 4       →  ID cards only spawn AFTER power is on (they're in lit rooms)
Task 5       →  needs the principal's office (Task 4)
Task 6       →  needs the final key + the PA broadcast
```

### 2.7 Run length
Target **20–30 minutes** for a full playthrough. 10 keys + 10 books + 6 fuses + 5 cards = 31 collectibles. At ~35 seconds of average travel/search each, that's the right ballpark. Tune by adjusting spawn spread, not counts.

### 2.8 Book return — color/symbol matching (decided 2026-08-17)
Task 2 as originally written ("return each book to its *matching* classroom")
risks tedium for kids: it demands memorization or trial-and-error backtracking,
which is punishing when the sound-based Banished penalizes movement.

**Fix:** each classroom door shows a colored **symbol** (e.g. red star, blue
moon, green leaf). Each book carries the *same* symbol on its spine and on its
HUD inventory icon. Returning a book is a pure visual match — no memory, no
guessing. A classroom only accepts the book whose symbol matches; a wrong book
is politely rejected (no penalty). This keeps the "deliver to the right place"
design intent while staying readable for young players.

### 2.9 Visible noise (decided 2026-08-17)
The Banished (sound-based) is only fair if players can *see* that they're making
noise. Every noise emitter draws a brief **expanding ring** at its world
position, whose max radius equals the actual hearing radius used by
`noise.py` (`BAN_HEAR_WALK` / `_SPRINT` / `_DOOR`). Sprinting footsteps, doors,
dropped items, and the PA all show this ring. When a Banished registers a noise,
it shows a small **"!"** so cause and effect are legible. Build this into the
noise system from the start — it is not polish, it is the tutorialization of the
whole second monster.

### 2.10 Vertical slice v0 — build this first (decided 2026-08-17)
Before pursuing the full 18-area Chapter 1, ship a tight, polished slice that
proves the core loop and the central power hook. If the slice isn't fun, the
full game won't be either — and we learn that in days, not weeks.

**Slice contents:**

| Element | Full game | Slice v0 |
|---|---|---|
| Spaces | 18 areas | entrance + corridor + 3 classrooms + electrical room |
| Keys | 10 | 3 |
| Books | 10 | 2 (color-matched, per §2.8) |
| Fuses | 6 | 2 |
| ID cards / PA / principal | yes | cut from slice |
| Monsters | Vidadiyot ×2 + Banished ×1 | **1 Vidadiya** (sight/chase only) |
| Central hook | dark→power→alarm | **kept in full** |
| Win condition | escape main gate | escape exit once power is on |

The Banished + noise system come immediately after the slice proves fun — but
noise is designed visibly *now* (§2.9) so it slots in cleanly. Language for the
slice: **Hebrew-first with an English toggle**; `strings_he.json` and
`strings_en.json` are both first-class from day one, He is the shipping default.

### 2.11 DIRECTION PIVOT — combat, not stealth (decided 2026-08-17)
The build has committed to a **combat** monster model over the original stealth
design. This **supersedes §2.3 (sight/sound asymmetry) and §2.5's "getting caught
isn't death"** for now:

- Monsters **guard objectives** (e.g. a book) and **chase** the player within an
  aggro radius. The player **fights** them with a melee attack (Enter). Each
  monster has a **strength = number of hits to kill**, shown as pips.
- The `vision.py` / `noise.py` sensing systems and the hide-in-lockers counters
  are **shelved** (not deleted from the doc — they remain the fallback if we ever
  revisit stealth). The `INVESTIGATE/SEARCH` AI states are not needed; the slice
  AI is just **IDLE(guard) → CHASE**.
- Implication for later milestones: **M4 becomes "combat chase & tuning"** rather
  than the sight-cone chase. Player health / stakes on losing a fight are still
  TBD (currently contact is non-lethal). Monster *variety* now means different
  strength / speed / behavior, not different senses.

Everything else in the doc (data-driven quests, EventBus, lighting hook, run
pacing, color-matched books, vertical slice) stands unchanged.

---

## PART 3 — ARCHITECTURE

### 3.1 Stack

| Concern | Choice | Why |
|---|---|---|
| Engine | **pygame-ce** (`pip install pygame-ce`) | Actively maintained fork; better performance, same API |
| Map editing | **Tiled** + **pytmx** | Do *not* hand-code an 18-area school in Python. Draw it in Tiled, load the `.tmx`. |
| Pathfinding | Hand-rolled A* on the tile grid | ~80 lines, no dependency, fully controllable |
| Data | Plain JSON in `data/` | Quests, spawns, strings, tuning — all editable without touching code |
| Hebrew text | `python-bidi` | pygame renders Hebrew left-to-right otherwise. See §3.9. |

### 3.2 File structure

```
vidadiyot/
├── main.py                    # entry point only: init, create Game, run
├── requirements.txt
├── settings.py                # ALL tuning constants, no logic
│
├── game/
│   ├── core/
│   │   ├── game.py            # main loop, state stack, fixed timestep
│   │   ├── state.py           # State base + MenuState, PlayState, PauseState, EndState
│   │   ├── camera.py          # dead-zone follow + screen shake
│   │   ├── assets.py          # AssetManager: lazy load + cache images/sounds/fonts
│   │   └── input.py           # keyboard/gamepad → intent ("move", "interact", "sprint")
│   │
│   ├── world/
│   │   ├── tilemap.py         # pytmx load, collision grid, room-region lookup
│   │   ├── room.py            # Room dataclass: name, rect, type, is_locked, key_id
│   │   ├── doors.py           # Door entity: locked/unlocked/open, needs_key
│   │   ├── spawner.py         # randomized placement of keys/books/fuses/cards
│   │   └── pathfinding.py     # A* + walkable-neighbor cache
│   │
│   ├── entities/
│   │   ├── entity.py          # base: pos, vel, hitbox, sprite, update(), draw()
│   │   ├── player.py          # movement, sprint+stamina, interact ray, carry slots
│   │   ├── monster.py         # Monster base + Vidadiya + Banished subclasses
│   │   ├── ai.py              # state machine: PATROL / INVESTIGATE / CHASE / SEARCH / STUNNED
│   │   ├── pickup.py          # Key, Book, Fuse, IDCard
│   │   └── interactable.py    # FusePanel, PAConsole, MainGate, Locker (hiding), Desk
│   │
│   ├── systems/
│   │   ├── quests.py          # QuestManager: objectives, gating, completion events
│   │   ├── inventory.py       # carried items, capacity limit, drop-on-catch
│   │   ├── events.py          # EventDirector: the 6 random events, weighted timers
│   │   ├── lighting.py        # darkness surface, flashlight cone, BLEND_MULT
│   │   ├── vision.py          # monster sight cone + line-of-sight raycast
│   │   ├── noise.py           # noise emitters → Banished hearing
│   │   ├── audio.py           # music layers, SFX bus, alarm stinger
│   │   └── eventbus.py        # pub/sub — the glue. See §3.4.
│   │
│   └── ui/
│       ├── hud.py             # objective tracker, inventory bar, stamina, fear meter
│       ├── menus.py           # title, pause, settings, win/lose
│       └── text.py            # bidi-safe text rendering wrapper
│
├── data/
│   ├── rooms.json             # 18 areas: name, type, key_id, valid spawn tags
│   ├── quests.json            # objective definitions + gating rules
│   ├── monsters.json          # per-type tuning
│   ├── events.json            # random event weights/cooldowns
│   ├── strings_en.json
│   └── strings_he.json
│
└── assets/
    ├── maps/school.tmx
    ├── tilesets/
    ├── sprites/
    ├── sfx/
    └── music/
```

### 3.3 Main loop — fixed timestep

Use a fixed physics step so monster AI and chases behave identically on every machine:

```python
FIXED_DT = 1 / 60

accumulator += clock.tick(120) / 1000.0
while accumulator >= FIXED_DT:
    self.state_stack[-1].update(FIXED_DT)
    accumulator -= FIXED_DT
self.state_stack[-1].draw(self.render_surface)
pygame.transform.scale(self.render_surface, window.get_size(), window)
```

### 3.4 The EventBus — the most important system

Almost every feature in this game is "X happens → three unrelated things react." Restoring power touches lighting, monster speed, audio, quests, and event weights. Wire that with direct references and the code becomes unmaintainable by week two.

```python
class EventBus:
    def __init__(self):
        self._subs = defaultdict(list)
    def on(self, event_name, callback):
        self._subs[event_name].append(callback)
    def emit(self, event_name, **payload):
        for cb in self._subs[event_name]:
            cb(**payload)
```

**Canonical event list** — define these as constants early:

```
item_collected        book_returned         door_unlocked
fuse_inserted         power_restored        alarm_triggered
noise_made            player_spotted        player_caught
player_hidden         quest_started         quest_completed
pa_activated          gate_opened           random_event_fired
```

Then `power_restored` is subscribed to by lighting (lights on), monsters (×1.35 speed), audio (alarm stinger + music layer change), quests (unlock Task 4 spawns), and the EventDirector (raise blackout weight). None of those systems knows the others exist.

### 3.5 Monster AI state machine

```
        ┌──────────┐  lost track / timer  ┌────────┐
   ┌───▶│  PATROL  │◀─────────────────────│ SEARCH │
   │    └────┬─────┘                      └────▲───┘
   │         │ noise heard / glimpse           │ target lost
   │         ▼                                 │
   │   ┌─────────────┐   confirms sight   ┌────┴───┐
   │   │ INVESTIGATE │───────────────────▶│ CHASE  │
   │   └─────────────┘                    └────┬───┘
   │         │ nothing found                   │ touches player
   └─────────┘                                 ▼
                                          ┌─────────┐
                                          │ STUNNED │ (10s after a catch)
                                          └─────────┘
```

- **PATROL** — follow a waypoint loop within an assigned wing. Recompute A* only on waypoint arrival.
- **INVESTIGATE** — move to a specific point (last noise / last seen tile), then look around for 3s.
- **CHASE** — A* recomputed every 0.4s, not every frame. Move at chase speed.
- **SEARCH** — target lost: check 3 nearby rooms, then decay back to PATROL after ~15s.

Vidadiyot only enter CHASE via `vision.py`; the Banished only via `noise.py`. Same state machine, different transition triggers — implement once, subclass the sensing.

### 3.6 Quest system, data-driven

```json
{
  "find_keys": {
    "title_en": "Find the classroom keys",
    "type": "collect",
    "item": "key",
    "required": 10,
    "unlocked_by": null
  },
  "return_books": {
    "title_en": "Return each book to its classroom",
    "type": "deliver",
    "item": "book",
    "required": 10,
    "unlocked_by": null
  },
  "restore_power": {
    "title_en": "Restore power to the school",
    "type": "multi_step",
    "steps": [
      {"type": "collect", "item": "fuse", "required": 6},
      {"type": "interact", "target": "fuse_panel", "count": 6},
      {"type": "interact", "target": "main_breaker"}
    ],
    "on_complete": ["power_restored", "alarm_triggered"]
  },
  "find_id_cards": {
    "title_en": "Find 5 staff ID cards",
    "type": "collect",
    "item": "id_card",
    "required": 5,
    "unlocked_by": "restore_power"
  }
}
```

`QuestManager` subscribes to `item_collected` / `book_returned` / `door_unlocked`, increments counters, and emits `quest_completed`. The HUD subscribes to the QuestManager. Adding Chapter 2 later means adding JSON, not code.

### 3.7 Randomized spawning

Every collectible gets a **spawn tag** so randomization stays sensible — a fuse in the art room's paint cupboard is fine, a fuse inside the locked principal's office is a softlock.

In Tiled, place an object layer of `spawn_point` objects, each with a `tags` property:

```
tags: "classroom, low"      → books, keys
tags: "utility, hidden"     → fuses
tags: "staff"               → ID cards
```

`spawner.py` rules:
1. Never spawn an item behind a door that its own quest unlocks.
2. Spread across regions — no more than 2 of the same item type per room.
3. At least 3 keys in the "easy ring" (entrance, corridor, first two classrooms) so the opening isn't a dead end.
4. Seed the RNG per-run and **print the seed** — you'll want it for bug reports.

### 3.8 Random events — the EventDirector

```python
EVENTS = {
  "blackout":     {"weight": 3, "cooldown": 90, "duration": 25, "requires_power": True},
  "fog":          {"weight": 2, "cooldown": 120, "duration": 40},
  "school_bell":  {"weight": 4, "cooldown": 60,  "duration": 4},
  "doors_relock": {"weight": 2, "cooldown": 150, "count": 3},
  "pa_whisper":   {"weight": 3, "cooldown": 100, "duration": 8},
  "wind_slam":    {"weight": 3, "cooldown": 75,  "count": 5},
}
```

Director logic: every 45–75 seconds, pick a weighted random event that's off cooldown and whose conditions are met. **Never fire an event while the player is in CHASE** — the game is already at peak tension; adding fog is noise, not drama.

Mechanical effects (each one should actually *matter*, not just be a visual):

| Event | Effect |
|---|---|
| ⚡ Blackout | Lights out for 25s even after power restored. Vidadiyot vision drops, Banished unaffected — so it's a *safe window* against one type and neutral against the other. |
| 🌫️ Fog | Player view radius halved. Monsters unaffected. Pure penalty — keep it short. |
| 🔔 Bell | Massive noise event at a random room. Pulls **all** Banished toward it. Free distraction if you're clever about where you are. |
| 🚪 Doors re-lock | 3 random unlocked doors re-lock. Their keys are still in inventory — it costs time, not progress. |
| 📢 PA whisper | Atmosphere + a spoken hint about where an item is. Rewards listening. |
| 💨 Wind slam | 5 doors slam. Each slam is a noise emitter → Banished scatter toward false positives. |

### 3.9 Hebrew text rendering (do this before you write any UI)

pygame does not handle RTL. Hebrew will render backwards and unshaped. Fix it once, in `ui/text.py`:

```python
from bidi.algorithm import get_display

def render_text(font, text, color, rtl=False):
    if rtl:
        text = get_display(text)
    return font.render(text, True, color)
```

Also: pick a font with real Hebrew coverage (Noto Sans Hebrew, Rubik, Heebo) and bundle the `.ttf` in `assets/fonts/`. The default pygame font has no Hebrew glyphs. Since your source concept is Hebrew and your kids are the likely playtesters, keep `strings_he.json` a first-class citizen from day one rather than retrofitting it.

### 3.10 Tuning constants (starting values — put all of these in `settings.py`)

```python
TILE = 32
INTERNAL_RES = (640, 360)

PLAYER_WALK       = 130    # px/sec
PLAYER_SPRINT     = 200
STAMINA_MAX       = 4.0    # seconds of sprint
STAMINA_REGEN     = 1.0    # per second, after 1.5s delay
CARRY_CAPACITY    = 4      # forces return trips — this is a feature
INTERACT_RANGE    = 40

VID_PATROL        = 85
VID_CHASE         = 145
VID_SIGHT_RANGE   = 220    # → 300 after power restored
VID_SIGHT_ARC     = 90     # degrees

BAN_PATROL        = 60
BAN_CHASE         = 105
BAN_HEAR_WALK     = 70     # px radius
BAN_HEAR_SPRINT   = 190
BAN_HEAR_DOOR     = 260

ALARM_SPEED_MULT  = 1.35
CATCH_STUN_TIME   = 10.0
CATCH_ITEMS_LOST  = 2

DARK_VIEW_RADIUS  = 110
FLASHLIGHT_RANGE  = 190
FLASHLIGHT_ARC    = 60
```

`CARRY_CAPACITY = 4` is doing real design work: it means you can't hoover up all 10 books in one loop, which creates repeated exposure to the corridors, which is where the monsters live.

---

## PART 4 — BUILD ORDER

Ship something playable at every milestone. Don't build systems you can't test yet.

| Milestone | Goal | Done when |
|---|---|---|
| **M0** | Window, fixed loop, state stack, a rectangle you can move | You can walk a box around a grey screen |
| **M1** | Tiled map loads, collision, camera follow | You can walk the real school and can't walk through walls |
| **M2** | Pickups + inventory + HUD + one quest (10 keys) | You can collect all 10 keys and see the counter fill |
| **M3** | Doors + unlocking + books returning to correct rooms | Tasks 1 and 2 fully playable, no monsters yet |
| **M4** | One Vidadiya: patrol, vision cone, chase, catch | The game is finally *scary*. Tune speeds here — spend real time on this. |
| **M5** | Darkness + flashlight + fuses + panel + power restore + alarm | The central hook works end to end |
| **M6** | The Banished + noise system | Both creatures live; the title is earned |
| **M7** | ID cards, principal's office, PA, main gate, win screen | Full loop completable |
| **M8** | EventDirector + all 6 random events | Every run feels different |
| **M9** | Audio, menus, Hebrew localization, settings, seed display | Shippable to your kids |

**Spend the most time on M4.** Chase tuning is the difference between "tense" and "unfair," and no amount of content fixes a bad chase.

---

## PART 5 — PROMPT SEED FOR YOUR OTHER IDE

Paste this at the start of the session over there:

> I'm building a 2D top-down horror-lite game in Python with pygame-ce, called *The Vidadiyot and the Banished*. Kids explore an abandoned school at night, completing 6 objectives (find 10 keys, return 10 books, restore power via 6 fuses, find 5 ID cards, activate the PA, escape through the main gate) while avoiding two monster types: **Vidadiyot** (sight-based, fast, countered by breaking line of sight) and **the Banished** (sound-based, slow, countered by moving quietly). Restoring power lights the school but triggers an alarm that makes all monsters 35% faster.
>
> Architecture: internal render surface 640×360 scaled up, 32px tiles, fixed 1/60s timestep, Tiled `.tmx` maps via pytmx, A* pathfinding on the tile grid, and a central pub/sub EventBus that all systems communicate through. Quests, spawns, monster tuning, and random events are all data-driven from JSON in `data/`. Getting caught is not death — you're moved to the nurse's office and drop 2 items.
>
> Start with milestone M1: load a Tiled map, build the collision grid, and implement a dead-zone-follow camera.

---

## PART 6 — WORTH CONSIDERING LATER

- **Fear meter** — rises near monsters and in the dark, drops in lit/safe rooms. At high fear the screen breathes and footsteps get louder, which *makes noise*. A pressure system that feeds back into the mechanics.
- **Hiding spots** — lockers and under-desks. Vidadiyot lose you; the Banished still hear your breathing after ~8 seconds. Reinforces the asymmetry.
- **The other kids** — the story says "a group of kids." Scattered NPC kids you rescue, each granting a small perk (one carries 2 extra items, one spots fuses on the minimap). Gives the ending real stakes: escape alone, or with everyone.
- **Chapter 2** — the story explicitly says "Chapter 1 – The School." The schoolyard and the area past the gate are a natural sequel. Build the quest system data-driven now and Chapter 2 costs you a JSON file plus a map.
