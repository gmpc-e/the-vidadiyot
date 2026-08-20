# The Vidadiyot

A 2D top-down horror-lite game in Python / pygame-ce. Kids sneak into an
abandoned school at night, fight the Vidadiyot, and return every book to its
classroom.

Pick a warrior — **Wallad the Knight** (longsword, two pips a swing) or **Roni the
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
interact (unlock doors, drop books in the locker) · **Space** attack · **Z** warrior power ·
**M** mute music · **Esc** pause · **Q** quit.

**Goal:** kill anything to earn a **key** → unlock a colour-coded door → **kill
the teacher inside** → pick up the book it drops → put it in that classroom's
**return locker**. All three books home wins the level.

Nothing is lying on the floor waiting for you. The first three kills **drop** a
key where the monster fell, and each book is carried by the teacher who holds its
classroom — it hits the floor **shining** where that teacher dies. Every objective is produced
by the fight that gates it.

**Getting hit looks like getting hit.** A monster with a painted flinch plays it
— Little Terror recoils, staggers and straightens up. Anything without one still
falls back to the old white flash.

**Casters warn you.** A monster about to throw stops moving and grows a charge in
its hands — and it locks its aim when it starts, so stepping sideways actually
works. Break its line of sight and it gives up.

Caught in a web, you now **lose health until you mash free**, so being stuck
while a teacher lines up a shot is a real trap rather than a pause. Monsters are
solid: you bump into them rather than walking through.

The locker is the one lit thing on a dark classroom wall, and it only opens once
**every monster in that room is dead** — so each delivery is a fight you finish,
not a room you walk through. If the drop refuses, the hint says which it is:
*"Clear the room first!"* or *"Wrong classroom for this book"*.

**The school is not still.** Fluorescent tubes flicker overhead, a pipe drips,
cobwebs hang in the corners — in the corridor and entrance as well as the
classrooms.

**The furniture is solid.** Desks, the teacher's desk and the bookshelf stop
you, so a classroom is somewhere to move around rather than a flat floor with
pictures on it. The aisles are sized for the 44px monster that lives there —
which is why the desks sit further apart than they look like they should.

### The warriors

| | Attack | Plays like |
|---|---|---|
| **Wallad — The Knight** | Longsword, **2 pips** a swing, reach 52 | Sturdier and hits harder, but has to close in and swings slower |
| **Roni — The Warrior Princess** | Thrown knives, **0.85 pips** each, range 250, unlimited | Faster and fights from safety — and **[Z] sends Zina**, whose bite kills outright, 3 per level |

Both warriors are fully animated — idle, attack, a real flinch when hit, and
**they turn to face where they walk**: toward you, away from you, or in profile.
Stop walking and they keep facing that way rather than spinning back to you.

Both are paced by a cooldown, so mashing buys nothing — the choice is reach
versus throughput, not who can hit the key faster.

### The monsters

**The teachers** hold the classrooms — a stooped grey woman and a squat balding
schoolmaster, both long past retirement, who shuffle around the room they died
in and fling a smoking book at anyone who walks in. They are slow and short-
ranged, which is what makes them a fight a classroom can actually contain.

Out in the corridors: **Little Terror** throws Purple Chaos fireballs and
**Little Snir** throws sticky webs — caught in one, **mash Space** to break free.
Those two reach much further and back away when you close, so the hallways are
where they are dangerous and a classroom is where they were merely annoying.

Bumping a monster is harmless; only their casts hurt, so closing in is safe if
you can take the shots.

The roster is **fixed** — one guard per book plus one resident per classroom, and
**nothing respawns**, so a room you clear stays clear.

**Difficulty changes three things**, not one: how hard monsters hit, how much
punishment they *take*, and how fast you heal. It used to scale incoming damage
alone — so a monster died in the same number of swings whichever you picked, and
the level was the same length on Hard as on Easy.

**Emri, the disappearing monster** is the boss. Twice during the fight it
vanishes and sends two of the school's own after you; it only comes back when
they are down, and it will not leave again straight away. Zina's bite kills anything else outright — against Emri it is a
heavy wound, so all three charges are a real answer to the fight.

Clearing the level does not end the run — it seals you into a classroom with
Emri, which blinks in at arm's length, strikes with a lightbolt and vanishes, and
is only hittable while visible. The clock keeps running, so the leaderboard
measures the whole thing.

Grab **health potions** to recover. Lose all HP → **YOU LOST!!!**. Return every
book → the **LEVEL ONE / COMPLETED** celebration, then name entry (unique names)
for the persistent **leaderboard**. A timer tracks your run.

The level has a soundtrack, seventeen sound effects, and **voices for both
teachers** — they notice you, they grunt when hit, and they die out loud. Six
more effects are wired but silent until the files land; see [Audio](#audio).

## Tests

```bash
./venv/bin/python -m pytest        # 478 tests, ~10 seconds
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
| `test_states_and_ui.py` | state stack, menus, HUD, camera, audio |
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

## Audio

Music is streamed from `assets/music/<track>.ogg` and chosen by whichever state
is on screen — `menu` on the title, `level_one` in play. Sound effects come from
`assets/sfx/<name>.(wav|ogg)` if the file is there and from a built-in synth if
it isn't, so the game is never silent on a fresh checkout. **M** mutes.

Generated audio is delivered to `~/Downloads/the-vidadiyot/audio/` as WAV and
brought in with:

```bash
./venv/bin/python tools/import_audio.py --list   # show what maps where
./venv/bin/python tools/import_audio.py          # transcode into assets/
```

That step is not optional: the menu track is 40MB as a WAV and 2.9MB as Ogg,
against ~1.5MB for the whole rest of the source. What to ask for, and the
technical rules the audio has to meet, are in `docs/AUDIO_BOOK.md`.

**Monsters can have a voice.** A character ships a pack of four —
`<voice>_spotplayer`, `_throw`, `_hit`, `_die` — and `play_voiced` uses it in
place of the generic effect, falling back when a character has no pack or no
take for that event. Both teachers have one. A voice never plays over itself, so
a long take just means the character says less.

**A sound may be silent, but only on purpose.** Call sites are written before
the audio for them exists, and `play()` ignores a name it cannot resolve rather
than crashing. So that this stays a decision rather than an accident, every
still-silent name is listed in `tests/test_systems.py::PENDING_AUDIO`, and a
test fails if the code and that list disagree in either direction. Today it is
`tome_hit`, `web_hit`, `web_stuck`, `web_break`, `locker_open` and the unused
`tome_cast` fallback. All five music tracks are in.

## Regenerate the map

The slice map (`assets/maps/school_slice.tmx` + `assets/tilesets/school.png`) is
generated, not hand-drawn. To change the layout, edit `tools/gen_map.py` and run:

```bash
SDL_VIDEODRIVER=dummy ./venv/bin/python tools/gen_map.py
```

That builds the tileset *and* the map in one go, which matters: the `.tmx`
hard-codes how many tiles there are and which of them are solid, so a tileset
built separately is how you get a map with invisible walls.

The tiles themselves are cut from painted material slabs under
`~/Downloads/the-vidadiyot/map/` by `tools/extract_map_art.py`, which also
extracts the door and item sprites. New source art can be requested without
leaving the repo — `tools/art_request.py --list` shows the prompt pack, and
`--dry-run` prints exactly what would be sent before anything is billed. Run it with `--preview` to write a 3×3
repeat of every tile to `assets/previews/` — the only honest way to spot a bad
seam. Without the source art it falls back to flat colours, so the map still
generates on a checkout that has never seen the paintings.

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
- [x] **painted art pass** — title screen, warrior select, animated Wallad & Roni,
      level-complete sequence, furnished classrooms
- [x] **map art (Phase 1)** — real parquet, corridor vinyl, cinderblock and
      stone in place of four flat colours; painted book, key, potion and doors;
      painted classroom props (desks, boards, lockers, litter) in place of the
      code-drawn rectangles
- [x] **§5 return lockers** — every book goes into its classroom's locker, and
      only once that room is cleared
- [x] **warriors & weapons** — pick your character; melee vs. thrown, both paced
- [x] **tests** — 374 headless pytest cases incl. tuning-invariant checks
- [ ] **next: the Emri boss duel** (§9) — behaviour is built and tested, the
      hidden classroom is not
- [ ] **M4** — first Vidadiya: patrol, vision cone, chase, catch *(tune hard)*
- [ ] **M5** — darkness, flashlight, fuses, power restore, alarm
- [ ] **M6** — the Banished + noise system
- [ ] **M7** — ID cards, principal's office, PA, gate, win screen
- [ ] **M8** — EventDirector + 6 random events
- [ ] **M9** — audio, menus, Hebrew localization, settings, seed display
