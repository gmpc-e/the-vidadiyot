# Art requests — the school map

What to paint, in priority order. Everything here is for the *map*; characters
and menu art are already done — as **single poses**. The frames that would make
them move are a separate request: see `ART_PROMPTS_PHASE2.md`.

---

## How to hand art over

**Paint big, never small.** Every sprite in the game so far was painted at
~1500px and downscaled by a tool. Do not draw at the final pixel size — a 32px
hand-drawn tile cannot be re-used at any other scale, and downscaling from a big
painting is what makes the result look crisp.

**Flat black background.** `#000000`, no vignette, no scene behind the object.
This is what keys out cleanly. The one time art arrived on a painted scene
(`level-one.png`) it needed a special alpha curve to separate, and it still lost
some brightness.

**One sheet per group, laid out on a grid** with generous gaps — a few hundred
px of black between items. Items that touch get cropped together.

**No text labels inside the item cells.** Labels are welcome *outside* the grid
or in the filename. A label sitting next to an object gets picked up as part of
it; a painted pose banner once beat the knight himself for "largest blob" and a
tool cheerfully exported a 387px-wide ribbon instead of a character.

**File into the tree:** `~/Downloads/the-vidadiyot/tiles/`, `props/`, `items/`.
The extractors resolve art by filename across that tree, so folders are free to
reorganise.

---

## The rules the art has to live inside

| | |
|---|---|
| Tile size | **32 × 32** game px |
| Screen | 640 × 360, integer-scaled ×2 |
| Monster hitbox | **44 × 44 — larger than one tile** |
| Palette | environment **dark and desaturated**; actors and anything usable stay bright |

That monster hitbox is the constraint that keeps biting. A room furnished with
*solid* desks in rows is impassable for the thing that has to live in it, so
almost all furniture is floor-layer decoration you walk over. Anything meant to
be solid needs a ≥2-tile lane around it.

The palette rule is the other one: the creepiness belongs in the background.
If the floor art competes with a monster for attention, the monster wins the
fight and the player loses.

---

## Priority 1 — tiles

The whole map is currently **four flat-colour rectangles**. This is the single
biggest visual win available, and nothing else will look finished until it lands.

**Must tile seamlessly** — each one repeats edge-to-edge across a whole room, so
a strong directional highlight or an off-centre feature will read as a grid of
stamps. Test by tiling 3×3 before sending.

| # | Element | Notes |
|---|---|---|
| 1 | **Classroom floor** | Worn wooden boards or scuffed lino. Dark, low contrast. |
| 2 | **Corridor floor** | A *different material* — checkered vinyl, stone. It should be obvious you left a room. |
| 3 | **Wall** | Top-down-ish. Needs to read as solid at a glance; this is the "you cannot walk here" signal. |
| 4 | **Doorway threshold** | Walkable strip in a wall gap. |
| 5 | **Floor variants ×3** | Cracked, stained, water-damaged. Sprinkled in to break repetition. Same material as #1. |

## Priority 2 — items

These are drawn **procedurally in code** today (simple shapes) and are on screen
constantly, so real art shows immediately.

| # | Element | Game size | Notes |
|---|---|---|---|
| 6 | **Book** | ~16 × 16 | Paint **one** in neutral grey/white — the game tints it to the room's colour. Five separate colour versions also fine if you prefer control. |
| 7 | **Key** | ~16 × 16 | Same: one neutral, tinted in code. |
| 8 | **Health potion** | ~16 × 16 | The "hp liquid" — glass bottle, red liquid, cork. Should read at 16px. |

## Priority 3 — classroom props

All **non-solid** unless flagged. Roughly top-down / slight 3-quarter, matching
how the characters are drawn.

| # | Element | Game size | Notes |
|---|---|---|---|
| 9 | **Student desk** | ~26 × 20 | The workhorse — 16 of them per room. Needs to look fine repeated. |
| 10 | **Chair** | ~12 × 12 | Paired with the desk; a loose one for the "knocked over" look too. |
| 11 | **Teacher's desk** | ~46 × 24 | Bigger, facing the class. |
| 12 | **Blackboard** | ~156 × 46 | Wall-mounted. Leave a clear area for the room's colour swatch to be drawn on it. |
| 13 | **Locker (single)** | ~22 × 32 | ⚠️ **Will become the book-return point** (roadmap §5) — it needs to read as a *destination*, not background. |
| 14 | **Bookshelf** | ~40 × 26 | Where the books came from. |
| 15 | **Wall clock** | ~14 × 14 | Stopped at a sinister hour, ideally. |
| 16 | **Poster / chart** | ~18 × 22 | 2–3 variants: alphabet, map, periodic table. |
| 17 | **Litter** | ~4 × 4 | Scattered paper, chalk stubs. A handful of tiny variants. |

## Priority 4 — corridor props

| # | Element | Game size | Notes |
|---|---|---|---|
| 18 | **Locker bank** | ~90 × 34 | A run of lockers as one piece, for corridor walls. |
| 19 | **Notice board** | ~48 × 30 | Pinned paper, half torn off. |
| 20 | **Trophy case** | ~40 × 34 | Glass, dusty cups. |
| 21 | **Mop bucket** | ~18 × 18 | ✅ Fine as a **solid** obstacle. |
| 22 | **Ceiling light** | ~28 × 12 | Fluorescent tube — the flicker is done in code. |
| 23 | **Radiator** | ~30 × 14 | Under windows. |

## Priority 5 — doors and atmosphere

| # | Element | Game size | Notes |
|---|---|---|---|
| 24 | **Classroom door, closed** | 64 × 32 | Needs a flat area for the colour plate that says which book belongs inside. |
| 25 | **Classroom door, open** | 64 × 32 | Dark threshold, leaf swung aside. |
| 26 | **Cobweb corners** | ~24 × 24 | 2–3 rotations for room corners. |
| 27 | **Window + moonlight** | ~48 × 40 | The main atmosphere piece. |
| 28 | **Cracks / stains** | various | Decals scattered over floors and walls. |

---

## Two things worth deciding before painting

**Tinting vs. painting five.** Books and keys come in five room colours. One
neutral painting tinted in code guarantees they match the doors and classroom
tints exactly, and adding a sixth colour later costs nothing. Five hand-painted
versions look richer but can drift out of step with the palette. Recommend
neutral + tint.

**How much the floor should say.** A busy, detailed floor fights the monsters
for the player's eye at 640×360. Painted dark, low-contrast and slightly boring
is the correct answer for a tile that covers 80% of the screen — the interest
should come from the props sitting on it.
