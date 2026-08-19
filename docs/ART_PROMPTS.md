# Prompt pack — Phase 1: the map

Copy-paste prompts for generating the map art described in `ART_REQUESTS.md`.
Phase 1 is **floors, walls, doors and the three item icons** — the things that
make the school stop looking like coloured rectangles.

Use **§0 Style block** at the top of *every* request, then paste one sheet
prompt under it. The style block is what keeps sheet 4 looking like sheet 1.

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
