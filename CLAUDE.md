# Working on The Vidadiyot

A 2D top-down horror-lite pygame game. `README.md` is the player/developer
front door; `docs/ROADMAP.md` is why things are the way they are.

---

## Keep the docs current — this is part of the task, not a follow-up

Whenever you finish a piece of work, **before reporting it done**:

1. **`docs/ROADMAP.md`** — update the section you touched. Move the status
   (⬜ → 🔶 → ✅), record *what shipped and why*, and add any new ⬜ items the
   work revealed. If you hit a trap, write it down as a ⚠️ note — the roadmap's
   value is the reasoning, not the checklist.
2. **`README.md`** — only if player-facing behaviour changed: controls, the
   warriors, the monsters, how to run or test. A README that describes a monster
   that no longer exists is worse than no README.
3. **The header block of `docs/ROADMAP.md`** — "Current state" and "Next up"
   drift fastest. Re-read them whenever you finish something sizeable.

Both docs have gone stale before: the README described a green melee monster
that had been removed, a hunter-respawn rule that no longer existed, and a
sprite generator no longer used. Assume drift and check.

## Committing

The user pushes with **GitHub Desktop** and plans to branch later. Make changes
in the working tree and **leave committing and pushing to them** unless they ask.
`venv/ build/ dist/ .idea/ .claude/` are gitignored — never suggest committing
them (~117MB of build output against ~1.5MB of source).

## Testing

```bash
./venv/bin/python -m pytest        # 330 tests, ~10s, headless
```

Run the suite before reporting work complete. Two conventions worth knowing:

- **`tests/test_balance.py` asserts relationships, not values** — "a projectile
  must outrun a walk but not a sprint", "melee must out-damage range but by under
  2×". These stay quiet when you retune and speak up when a tweak breaks
  something elsewhere. Add to it when you add a tuning dial.
- **Fixtures draw every frame**, because a real share of defects here are
  draw-only. A test that only calls `update()` misses them.

## Invariants that keep biting

- **Edge intents must be latched.** `Input.poll()` runs per render frame; the sim
  steps at 60Hz. A press can land on a frame that runs no step (dropped) or two
  (doubled). `Game.run` parks each press until exactly one step takes it. **Any
  new edge intent must go in `InputState.EDGE_FIELDS`.**
- **A monster hitbox is 44×44 against a 32px tile.** Room decoration is
  floor-layer and **non-solid**, or the room becomes impassable for the thing
  that lives in it. Solid clusters need a ≥2-tile lane.
- **Environment dark and desaturated; actors and interactables bright.** The
  creepiness lives in the background. Anything that can kill you or that you can
  use stays legible at 640×360.
- **Every weapon needs a cooldown.** An unpaced weapon is worth whatever the
  player's mashing speed happens to be, not its stats.
- **Card stats are flavour; play stats drive the game.** `warriors.py` carries a
  painted `card` (HP/ATK/DEF/SPD) *and* real `speed`/`damage`/`reach`/`cooldown`.
  Keep them consistent in spirit or the select screen lies.
- **Nothing respawns.** The roster is fixed so a cleared room stays cleared.
- **`EventBus` outlives a state.** It lives on `Game`, so anything subscribing
  must unsubscribe in `exit()` or a restart doubles every handler.

## Art pipeline

Source art lives under `~/Downloads/the-vidadiyot/`. `spritelib.source(name)`
resolves a **filename** across that tree, so art can be refiled freely.
`tools/*.py` regenerate every derived asset in `assets/` — nothing in `assets/`
is precious, and every tool must stay re-runnable.

Painted art arrives on flat black and is keyed by one of two strategies
(`MODE_FILL` for lit subjects, `MODE_RAMP` for subjects made of shadow). See
`tools/spritelib.py`, and `docs/ART_REQUESTS.md` / `docs/ART_PROMPTS.md` for what
to ask for and how.

## Style

Match the surrounding code: comments explain *why*, not what. Constants live in
`settings.py` with a comment saying what breaks if you change them.
