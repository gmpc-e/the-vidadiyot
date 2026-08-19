# The Vidadiyot

A 2D top-down horror-lite game in Python / pygame-ce. Kids sneak into an
abandoned school at night, fight the Vidadiyot, and return every book to its
classroom.

Pick a warrior — **Elad the Knight** (longsword, two pips a swing) or **Roni the
Warrior Princess** (thrown knives, plus Zina the dog) — then clear the guards,
collect the keys, and get the books home before the monsters get you.

- `docs/vidadiyot_game_design.md` — original concept & architecture
- `docs/ROADMAP.md` — what is built, what is next, and why
- `docs/ART_REQUESTS.md` / `docs/ART_PROMPTS.md` — the art pipeline

## Setup (fresh clone)

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt -r requirements-dev.txt
```

The `venv/` is deliberately not committed — recreate it per machine.

## Run

```bash
./venv/bin/python main.py
```

The game opens on a **title menu**: Play · Select your Warrior · Difficulty ·
How to Play · Leaderboard · Quit. Left/Right switches warrior or difficulty in
place; Enter on the warrior row opens the full character page.

Controls: **WASD / arrows** move · **Shift** sprint (uses stamina) · **E**
interact (unlock doors, return books) · **Space** attack · **Z** warrior power ·
**M** mute music · **Esc** pause · **Q** quit.

**Goal:** collect keys → unlock the colour-coded doors → kill each book's guard
to free it → carry every book to its matching classroom. All three books home
wins the level.

### The warriors

| | Attack | Plays like |
|---|---|---|
| **Elad — The Knight** | Longsword, **2 pips** a swing, reach 52 | Sturdier and hits harder, but has to close in |
| **Roni — The Warrior Princess** | Thrown knives, **0.85 pips** each, range 250, unlimited | Faster and fights from safety — and **[Z] sends Zina**, whose bite kills outright, 3 per level |

Both are paced by a cooldown, so mashing buys nothing — the choice is reach
versus throughput, not who can hit the key faster.

### The monsters

**Little Terror** throws Purple Chaos fireballs; **Little Snir** throws sticky
webs — caught in one, **mash Space** to break free. Bumping a monster is
harmless; only their casts hurt, so closing in is safe if you can take the shots.

The roster is **fixed** — one guard per book plus one resident per classroom, and
**nothing respawns**, so a room you clear stays clear. Difficulty scales monster
damage only (Easy = half, Hard = more).

**Emri, the disappearing monster** is built but does not spawn in level 1: it
blinks in at arm's length, strikes with a lightbolt and vanishes, and is only
hittable while visible. It is waiting on the boss level (roadmap §9).

Grab **health potions** to recover. Lose all HP → **YOU LOST!!!**. Return every
book → the **LEVEL ONE / COMPLETED** celebration, then name entry (unique names)
for the persistent **leaderboard**. A timer tracks your run.

Audio: every sound is a named entry in `audio.SYNTHS` with a synthesized
fallback, and any file dropped in `assets/sfx/` overrides it automatically —
`monster.wav`, `success.wav`, `zina_bark.wav`, `zina_bite.wav`,
`level_done.wav`. Giving a new character a voice is one synth plus one line.

Music is a procedurally synthesized funky chiptune loop (`game/systems/audio.py`) —
generated at runtime, not shipped as a file, since reliable MIDI playback needs a
soundfont that isn't guaranteed on macOS.

## Tests

```bash
./venv/bin/python -m pytest        # 330 tests, ~10 seconds
```

They run headless (dummy SDL video and audio drivers, set in `tests/conftest.py`)
so no window opens, and the leaderboard is redirected to a temp file for every
test — running the suite never touches your real scores.

Layout:

| File | Covers |
|---|---|
| `test_systems.py` | EventBus, Inventory, QuestManager, difficulty, scores |
| `test_input.py` | intents, and the edge-latching contract across the fixed timestep |
| `test_entities.py` | Entity/collision, Player, Pickup, Door, projectiles |
| `test_monsters.py` | Monster, the casters, Emri's blink cycle |
| `test_warriors_and_zina.py` | the roster as data, and Roni's dog |
| `test_play_state.py` | the gameplay loop end to end |
| `test_states_and_ui.py` | state stack, menus, HUD, camera, effects, audio |
| `test_world_and_assets.py` | tilemap, spawner, palette, decor, assets, outcome screens |
| `test_balance.py` | tuning *relationships* that must hold between constants |

`test_balance.py` is the unusual one: it asserts relationships rather than
values, so it stays quiet when you retune and speaks up when a tweak breaks
something elsewhere — a projectile that can no longer catch a walking player, a
monster that outruns a sprint, a telegraph too short to swing inside of.

## Build a standalone macOS app

Package the game into a double-clickable `.app` that needs **no Python** — for
sharing with other user profiles / other Macs:

```bash
./tools/build_mac.sh          # -> dist/Vidadiyot.app
```

Notes:
- Built for the machine's architecture (currently **Apple Silicon / arm64**).
  An Intel Mac needs its own build (or a universal2 Python).
- The app is **unsigned**, so the first time another user opens it macOS
  Gatekeeper may block it: **right-click the app → Open → Open**, or run
  `xattr -dr com.apple.quarantine /path/to/Vidadiyot.app`.
- Each user profile keeps its **own leaderboard** at
  `~/Library/Application Support/Vidadiyot/scores.json`.

## Regenerate the map

The slice map (`assets/maps/school_slice.tmx` + `assets/tilesets/school.png`) is
generated, not hand-drawn. To change the layout, edit `tools/gen_map.py` and run:

```bash
SDL_VIDEODRIVER=dummy ./venv/bin/python tools/gen_map.py
```

## Architecture

Internal render surface 640×360, integer-scaled to the window. Fixed 1/60s
timestep. A central pub/sub `EventBus` (`game/systems/eventbus.py`) is the glue
between systems. Tuning constants live in `settings.py`; quests are JSON in
`data/`; the playable roster is data in `game/entities/warriors.py`.

⚠️ **Key presses are latched across the fixed timestep.** `Input.poll()` runs per
render frame but the sim steps at 60Hz, so a press could land on a frame that ran
no step (dropped) or one that ran two (doubled). `Game.run` parks each press
until exactly one step takes it — any new edge intent must be added to
`InputState.EDGE_FIELDS` or it inherits that bug.

```
main.py            entry point
settings.py        all tuning constants
game/core/         game loop, states, camera, input, assets
game/world/        tilemap, palette, spawner, classroom decor
game/entities/     warriors, player, monsters, pickups, projectiles, Zina
game/systems/      eventbus, quests, inventory, audio, effects, scores
game/ui/           hud, icons, leaderboard
tools/             asset extractors — regenerate everything in assets/
tests/             pytest suite (headless)
```

## Build milestones

- [x] **M0** — window, fixed loop, state stack, movable box on a grey field
- [x] **M1** — Tiled map load, collision grid, dead-zone camera on the real map
- [x] **M2** — pickups + inventory + HUD + first quest (collect 3 keys)
- [x] **M3** — doors, unlocking (spend a key), returning color-matched books
- [x] **combat game (on request, replaces stealth — doc §2.11):** ranged guardian
      monsters that wander/search/chase; player health + regen; run timer; key/book
      counters; win on all books returned; Victory + name entry + persistent
      leaderboard; defeat screen; colour-tinted classrooms
- [x] **painted art pass** — title screen, warrior select, animated Elad & Roni,
      level-complete sequence, furnished classrooms
- [x] **warriors & weapons** — pick your character; melee vs. thrown, both paced
- [x] **tests** — 330 headless pytest cases incl. tuning-invariant checks
- [ ] **next: real map tiles** — see `docs/ART_REQUESTS.md` and `ART_PROMPTS.md`
- [ ] **M4** — first Vidadiya: patrol, vision cone, chase, catch *(tune hard)*
- [ ] **M5** — darkness, flashlight, fuses, power restore, alarm
- [ ] **M6** — the Banished + noise system
- [ ] **M7** — ID cards, principal's office, PA, gate, win screen
- [ ] **M8** — EventDirector + 6 random events
- [ ] **M9** — audio, menus, Hebrew localization, settings, seed display
