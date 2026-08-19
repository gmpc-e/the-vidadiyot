# Prompt pack — Phase 1: the map

Copy-paste prompts for generating the map art described in `ART_REQUESTS.md`.
Phase 1 is **floors, walls, doors and the three item icons** — the things that
make the school stop looking like coloured rectangles.

Use **§0 Style block** at the top of *every* request, then paste one sheet
prompt under it. The style block is what keeps sheet 4 looking like sheet 1.

**Phase 2 — animation** lives in `ART_PROMPTS_PHASE2.md`: walk cycles, attack
swings, monster cast wind-ups, Emri materialising, projectile loops. §5 below is
the seed it grew out of; the Phase 2 pack supersedes it for anything that moves.

---

## §0 Style block — paste this first, every time

> **Style:** Hand-painted 2D game art for a horror-lite cartoon game set in an
> abandoned school at night. Painterly illustration with clean dark outlines and
> chunky, readable shapes — the register of Luigi's Mansion or Costume Quest, not
> photoreal and not survival horror. Slightly grimy, dusty, decayed, but never
> gory and never frightening; the audience is children.
>
> **Palette:** desaturated cool greys, muted browns and deep blue-blacks for all
> environment surfaces. Accent language, used sparingly: brass and warm gold for
> metal, blood red and toxic slime green for damage and decay, deep purple for
> cloth. Environment must stay **dark and low-contrast** — it is background, and
> bright characters have to stand out against it.
>
> **Lighting:** flat, even, ambient. No strong directional light, no baked drop
> shadows, no glow. Each object lit as if by dim overcast moonlight from directly
> above.
>
> **Presentation:** every object isolated on a **pure black (#000000) background**.
> No scene, no vignette, no floor beneath the objects, no gradient, no border, no
> frame. **No text, no labels, no captions, no watermarks, no UI panels.**
> Output at 1536×1024.

Two of those lines exist because of specific accidents: an earlier sheet arrived
as a full UI mock-up with a rewards panel and buttons, and painted pose labels on
another sheet got mistaken for the character by the cutout tool. Keep the "no
text" and "no scene" clauses in.

---

## §1 Floor and wall tiles

⚠️ **Read this first.** Image models are poor at *truly* seamless tiles — the
edges rarely match. So do not ask for a 32×32 tile. Ask for a **large slab of
material** and let the tooling cut and blend tiles out of it. That plays to what
the model is good at (texture) and away from what it is bad at (edge registration).

> Paint four large square swatches of flooring and wall material, arranged in a
> 2×2 grid with a wide black gutter between them. Each swatch is a flat, evenly
> lit patch of material seen from directly overhead, filling its cell edge to
> edge with no border and no objects on it:
>
> 1. **Classroom floor** — old worn wooden parquet, scuffed and dull, boards in a
>    herringbone pattern, dust in the seams.
> 2. **Corridor floor** — institutional chequerboard vinyl in two near-identical
>    dark greys, cracked and lifting at the edges. Clearly a different material
>    from the classroom floor.
> 3. **Wall** — painted cinder block, the paint flaked away in patches to bare
>    grey concrete, a dado line low across it.
> 4. **Ceiling-lit stone** — dark flagstones, damp, for basement corridors.
>
> Texture must be uniform across each swatch: no focal point, no single large
> crack or stain, nothing that would look obviously repeated if the patch were
> tiled. Even, ambient light with no gradient from one side to the other.

That last paragraph is the whole game. A swatch with one big feature in the
middle becomes a wallpaper of that feature.

---

## §2 Floor damage decals

Overlays scattered on top of §1 so the floors don't read as wallpaper.

> Paint eight small floor-damage decals on a pure black background, arranged in
> two rows of four with wide black gaps between them. Seen from directly
> overhead, each one isolated with soft irregular edges that fade to nothing:
> a spider-web crack; a dark water stain; a patch of missing floorboards showing
> the boards beneath; a scorch mark; a puddle with a dull reflection; a scatter of
> plaster rubble; a long scrape; a spreading patch of green mould.
>
> Muted and dark. These sit on top of flooring, so nothing should be brighter
> than a mid grey.

---

## §3 Doors and thresholds

> Paint a set of school doors on a pure black background, arranged in one row
> with wide black gaps, all seen from directly overhead at the same scale, each
> twice as wide as it is tall:
>
> 1. A **closed** wooden classroom door with an iron lock plate and a handle.
>    Leave a **flat, undecorated rectangular panel in the upper middle** of the
>    door — a coloured plate is drawn there by the game.
> 2. The **same door standing open**, swung to one side, showing a dark empty
>    threshold behind it.
> 3. A **doorway threshold strip** — the bare walkable floor of a doorway with a
>    worn metal edging strip, no door.
>
> Old, scuffed, institutional. Dark wood and dull iron.

---

## §4 Item icons

These are drawn as crude code shapes today and are on screen constantly.

> Paint three game item icons on a pure black background, in one row with wide
> black gaps, all at the same scale, each viewed at a slight three-quarter angle
> and designed to stay readable when shrunk very small:
>
> 1. A **closed hardback book** — plain cover with no title or writing, visible
>    page edges, a ribbon bookmark. **Paint the cover in neutral light grey**, no
>    colour: the game tints it per classroom.
> 2. An **old iron key** with an ornate bow and two teeth. Neutral grey metal.
> 3. A **glass potion bottle** of thick red liquid with a cork stopper and a
>    highlight on the glass.
>
> Bold silhouettes, strong outlines, high contrast — unlike the environment, these
> must be **bright and saturated** so they stand out against a dark floor.

Note the deliberate contradiction with the style block: items and characters are
the exception to "dark and desaturated". Anything the player can pick up or be
killed by stays legible.

---

## §5 Animated strips

For anything that moves. **Registration is everything**: if the object shifts
between frames the animation jitters, and there is no fixing that afterwards.

> Paint an animation strip: **N frames in a single horizontal row**, evenly
> spaced, on a pure black background. **The object must be in exactly the same
> position and at exactly the same size in every frame** — identical framing,
> identical scale, identical camera. Only the named detail changes between
> frames. No text, no frame numbers, no borders between frames.

Then append one of:

- **Flickering ceiling light** (4 frames) — *a long fluorescent tube fixture seen
  from below, going from fully lit, to dim, to dark, to a bright flare.*
- **Dripping water** (4 frames) — *a droplet forming on a pipe, swelling,
  falling, and splashing.*
- **Candle flame** (4 frames) — *the flame leaning and guttering, the candle
  itself unmoving.*
- **Cobweb in a corner** (3 frames) — *the web sagging and swaying very slightly.*

Keep strips to 3–4 frames. The game plays them at about 6–8 fps and more frames
buys almost nothing at this size.

---

## Before you send a sheet back

- [ ] Background is **pure black**, not very dark grey
- [ ] **No text anywhere** in the image
- [ ] No UI panel, frame, border or background scene
- [ ] Objects well separated — big black gaps, nothing touching
- [ ] Environment pieces are dark and dull; items are bright
- [ ] Tile swatches have **no single dominant feature**
- [ ] Animation frames are identically framed and scaled
- [ ] Filed under `~/Downloads/the-vidadiyot/tiles/` (or `props/`, `items/`)

Anything that misses these is still usable — it just costs a retune in the
extractor, and sometimes brightness with it.

---

# Round 2 — what Phase 1 still needs

The first delivery (`~/Downloads/the-vidadiyot/map/`) was **exemplary in format**:
separate full-resolution crops, a `manifest.json`, pure-black key, and a README.
Ask for that same format again — it is the reason the tiles, items and doors
integrated in one pass.

A second sheet (`more-map-stuff-v1.png`) then arrived covering all 28 items in
`ART_REQUESTS.md` at once. It answers the right list, but it cannot be used as
production art for two reasons, and both are worth saying out loud in the
re-request:

1. **It has painted text labels above every item** — the exact failure this doc
   warns about in §0. Nothing automated can find an object on it; every crop has
   to be hand-boxed to dodge the caption.
2. **It is under-resolved.** 28 groups share one 1536×1024 sheet. Small props
   survive (a student desk is ~100px source for a 26px final, 4×), but the big
   ones do not: **the blackboard is ~205px wide for a 156px final — 1.3×**, which
   is effectively 1:1 and will look soft beside everything else in the game.

So the rule that fixes both, and belongs at the top of every round-2 request:

## §R0 Delivery format — paste this with every sheet

> **Deliver as one sheet per group, six items maximum per sheet.** Every item
> must be at least **four times its final in-game size** in each dimension —
> those sizes are given per item below, so a 156×46 blackboard needs to be at
> least 624×184 pixels on the sheet. If six items cannot all meet that on one
> 1536×1024 sheet, split the group across two sheets rather than shrinking them.
>
> **No text anywhere inside the image** — no titles, no item names, no numbers,
> no captions. Labels belong in the *filename* or in a separate list, never
> painted on the sheet.
>
> Pure black (#000000) background, wide black gutters, nothing touching. Same
> style block as always.

---

## §R1 Wall material — re-do

⚠️ The wall slab that arrived is an **elevation**: a wall seen face-on with a
dado rail across it and a skirting strip along the bottom. Both are strong
horizontal features, so tiling it produces stripes. Only the plain cinderblock
above the rail is currently usable, and it is a small window.

> Paint one large square swatch of wall material, filling the frame edge to edge
> with no border: **painted cinder block, the paint flaked away in patches to
> bare grey concrete.** Seen flat and face-on.
>
> **The entire swatch must be the same uniform material.** No dado rail, no
> skirting board, no floor strip along the bottom, no pipes, no fittings, no
> edge to the wall — nothing that runs across the image in a line, and no single
> large stain or crack. Every part of the swatch must be interchangeable with
> every other part, because it will be cut into 32×32 tiles and repeated across
> whole rooms. Even, ambient light with no gradient from one side to the other.
>
> Dark and desaturated — this is background.

## §R2 Doorway threshold — re-do

⚠️ Both deliveries returned a **door frame seen in perspective** with a dark
opening behind it. What the game needs is the *floor* of a doorway: a walkable
strip seen from directly overhead, which is the one tile a player stands on
while passing between rooms.

> Paint one small rectangular patch of floor, **twice as wide as it is tall**,
> seen from **directly overhead, looking straight down** — no perspective, no
> walls, no door, no frame, no opening, no darkness behind it. It is a piece of
> ground: worn boards or stone with a **scuffed brass edging strip running across
> the short axis**, the kind set into a doorway where two floor materials meet.
> Fills the frame edge to edge. Dark, dull, low contrast.

## §R3 Floor variants ×3 — re-do

⚠️ The three variants that arrived are **straight horizontal planks**, but the
classroom floor they have to sit inside is **herringbone parquet**. Sprinkled
into a herringbone room they read as three patches of a different floor rather
than as damage to this one.

> Paint three large square swatches of the **same herringbone parquet flooring**,
> arranged in one row with wide black gutters, seen from directly overhead and
> filling each cell edge to edge. All three must be **unmistakably the same wood,
> the same herringbone pattern, the same colour and the same plank size** — they
> differ only in what has happened to them:
>
> 1. **Cracked** — the boards split and lifted, gaps opening between them.
> 2. **Water-stained** — a dark damp bloom soaked into the wood, the grain still
>    visible through it.
> 3. **Rotted** — green-black mould creeping along the seams, a few boards gone
>    soft and dark.
>
> The damage must be spread evenly across each swatch with **no single dominant
> feature** — these are cut into 32×32 tiles and scattered through a floor of the
> clean version, so anything centred becomes an obviously repeated stamp.

---

## §R4–R6 The props, at proper resolution

The contact sheet answered priorities 3–5 of `ART_REQUESTS.md`. Re-request them
in groups, with §R0 attached, at these minimum sheet sizes:

| Sheet | Items | Final sizes | Minimum on the sheet |
|---|---|---|---|
| **R4a Classroom furniture** | student desk, chair, teacher's desk, bookshelf | 26×20, 12×12, 46×24, 40×26 | 104×80 … 184×104 |
| **R4b Classroom wall** | blackboard, wall clock, poster ×3 | 156×46, 14×14, 18×22 | **blackboard ≥ 624×184** |
| **R4c The locker** ⭐ | single locker, closed **and** standing open with a shelf | 22×32 each | ≥ 88×128 each |
| **R5 Corridor** | locker bank, notice board, trophy case, mop bucket, ceiling light, radiator | 90×34, 48×30, 40×34, 18×18, 28×12, 30×14 | ≥ 360×136 for the bank |
| **R6 Atmosphere** | cobweb corners ×3, window + moonlight, litter ×5 | 24×24, 48×40, 4×4 | ≥ 96×96, ≥ 192×160 |

⭐ **R4c is the one to send first.** The locker is the book-return point
(roadmap §5) — the destination the player fights their way to — so it is the
only prop in this list that is a *game object* rather than scenery, and it needs
two states:

> Paint two views of the same battered school locker, seen from a slight
> three-quarter angle from above, side by side with a wide black gutter, at
> exactly the same size and angle: **(1) shut**, a tall narrow steel door with
> vent slits near the top, a handle and a keyhole, the paint chipped;
> **(2) the same locker standing open**, the door swung aside, a single shelf
> inside and the interior in shadow.
>
> Leave a **flat, undecorated rectangular panel across the upper front of the
> door** in both views — the game paints the classroom's colour there, and it is
> how the player identifies which book belongs inside.
>
> Unlike the rest of the furniture, this one is a **destination, not background**:
> keep it a shade brighter and higher-contrast than the walls around it so it
> reads as somewhere to walk to from across a dark room.
