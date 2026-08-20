# Prompt pack — Phase 1: the map

Copy-paste prompts for generating the map art described in `ART_REQUESTS.md`.
Phase 1 is **floors, walls, doors and the three item icons** — the things that
make the school stop looking like coloured rectangles.

Use **§0 Style block** at the top of *every* request, then paste one sheet
prompt under it. The style block is what keeps sheet 4 looking like sheet 1.

> ⚠️ **This file is parsed, not just read.** `tools/art_request.py` sends these
> prompts to the image API directly, taking the `## §N Title` heading as the
> section id and **the blockquote under it as the prompt**. Two consequences for
> anyone editing: a prompt written as a plain paragraph is silently *not sent*,
> and a section holding two different requests will send only the first
> blockquote under a heading that promises both. Unquoted paragraphs are notes to
> us and are deliberately dropped — that is the right place for warnings like the
> one in §1. One runnable request per §.

**Phase 2 — animation** lives in `ART_PROMPTS_PHASE2.md`: walk cycles, attack
swings, monster cast wind-ups, Emri materialising, projectile loops. §5 below is
the seed it grew out of; the Phase 2 pack supersedes it for anything that moves.

**⚠️ `tools/art_request.py` parses this file.** A section is a `## §N Title`
heading and its prompt is the **blockquote** beneath it — prose outside the
quote is treated as commentary for us and is never sent to the model. Keep new
prompts inside `>` quotes, or the tool will cheerfully request nothing.

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
> cloth. Environment must stay **dark and low-contrast** — it is background.
> **Characters, monsters, projectiles and pickups are the exception — they stay
> bright and saturated**, because they have to stay legible against a dark floor
> at 640×360.
>
> **Lighting:** flat, even, ambient. No strong directional light, no baked drop
> shadows, no glow. Each object lit as if by dim overcast moonlight from directly
> above.
>
> **Characters:** the cast is **not drawn at one set of proportions**, and a
> sheet that restyles a character is unusable no matter how good it is — these
> are animations of characters already in the game, so each one has to match the
> art it will be intercut with, frame for frame.
>
> - **Monsters, teachers and the dog: chibi** — about three heads tall, large
>   round head, big eyes, short stubby body, simplified oversized hands and feet.
>   Adults among them are drawn this way too.
> - **Roni, the warrior princess: stylised** — about four heads tall. A large
>   head and big eyes, but a real body underneath, and her armour and cloak are
>   painted with proper weight and detail.
> - **Wallad, the knight: a realistically proportioned adult** — about six heads
>   tall, a bearded man in heavy plate. **He is not a chibi character.** Do not
>   give him a big round head or a child's body.
>
> Whichever it is, build the figure out of a few big shapes rather than fine
> detail: at final size a face is a handful of pixels, so the silhouette of the
> head, the hair and the gear is most of what the player will ever see.
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

## §R4–R6 The props — ✅ delivered

Sent, and the sheet arrived as `phase-1-rework.png`. All of it is extracted by
`tools/extract_props.py` and the classroom set is placed by `world/decor.py`.
Kept here as the size record, since a re-paint of any one piece has to match it.

| Sheet | Items | Final sizes | Minimum on the sheet |
|---|---|---|---|
| **R4a Classroom furniture** | student desk, chair, teacher's desk, bookshelf | 26×20, 12×12, 46×24, 40×26 | 104×80 … 184×104 |
| **R4b Classroom wall** | blackboard, wall clock, poster ×3 | 156×46, 14×14, 18×22 | **blackboard ≥ 624×184** |
| **R5 Corridor** | locker bank, notice board, trophy case, mop bucket, ceiling light, radiator | 90×34, 48×30, 40×34, 18×18, 28×12, 30×14 | ≥ 360×136 for the bank |
| **R6 Atmosphere** | cobweb corners ×3, window + moonlight, litter ×5 | 24×24, 48×40, 4×4 | ≥ 96×96, ≥ 192×160 |

⚠️ The blackboard came back at **2.5×**, not the 4× asked for — it is the one
prop in the game that is close to a 1:1 downscale. Everything else cleared 4×.

⚠️ The sheet arrived with **painted captions above every item** for the third
delivery running. `tools/extract_props.py` works around it by finding items in
bands *below* the known caption rows rather than by locating the biggest shape,
and asserts the column count per band so a merged crop fails loudly. It is a
workaround, not a fix — see the note under §R7.

---

## §R7 Return locker, open state

The one piece of §R4c that did not arrive. The locker was delivered **shut
only**, so a filled locker is currently signalled by a page edge painted on its
colour plate instead of a door standing open — which is a weaker read for the
single most important beat in the level (roadmap §5, §6).

Both views are asked for again together, because a shut locker painted in a
separate pass from the open one will not line up with it.

> Paint two views of the same battered school locker, seen from a slight
> three-quarter angle from above, side by side with a wide black gutter, at
> **exactly the same size, angle and position within its half of the frame**:
> (1) **shut** — a tall narrow steel door with vent slits near the top, a
> handle, a keyhole and a slot near the top, the green paint chipped;
> (2) **the same locker standing open** — the door swung aside on its hinges,
> one shelf inside, the interior in shadow, and a single closed book lying on
> the shelf.
>
> Leave a flat, undecorated rectangular panel across the upper front of the door
> in both views. The game paints the classroom's colour there, and it is how the
> player identifies which book belongs inside — so nothing may be drawn on it.
>
> Unlike the rest of the school furniture this one is a **destination, not
> background**: keep it brighter and higher-contrast than the walls around it, so
> it reads as somewhere to walk to from across a dark room.

⚠️ **The captions problem is worth solving at the source.** Three sheets in a
row have arrived with item names painted above each object, despite §0 and §R0
both forbidding it in the same words. Restating the ban a fourth time is
unlikely to work; `art_request.py`'s `check()` gate is the place to catch it,
since a caption row is cheap to detect — it is a thin horizontal band of
low-density content sitting directly above a tall dense one, which is exactly
the shape `extract_props.py` already profiles to *find* the items.

---

## §R8 Teacher monster — female

A new classroom-dwelling caster (roadmap §2.12). It takes over the *inside* of
the classrooms; Little Terror moves out into the corridors, where a fire caster
with a 250px range has room to kite.

⚠️ **The roster is chibi, and until this sheet no prompt file said so.** Snir,
Little Terror and Emri are big-headed cartoon children, roughly three heads
tall. The first two deliveries of this sheet came back at realistic adult
proportions — about seven heads — so at the 54px the game draws her at, she was
a thin grey stick with a six-pixel head standing beside three characters that
read instantly. The rule now lives in **§0**, not here, because it applies to
every character sheet either pack will ever ask for.

Three things about this sheet are set by the code, not by taste:

- **The four poses are the existing monster convention.** Every delivered
  monster sheet — Snir, Little Terror, Emri — carries MAIN / IDLE / WALK /
  ATTACK, and the extractors cut IDLE for `sprites/<name>.png` and MAIN for
  `sprites/<name>_menu.png`. Asking for the same four keeps one extractor
  shape for every monster in the game.
⚠️ **Both deliveries drew the ATTACK pose about a quarter smaller than the other
three**, despite the "one common ground line, whole body visible in every one of
the four" clause below — which was itself added after the *first* roll cropped it
at the waist. So the instruction moved the failure rather than fixing it. The
pose is extracted (`teacher_f_attack.png`) and cannot be used: at the sheet's own
scale the teacher visibly shrinks every time it casts. Fix it in the prompt on
the next roll, or add a per-pose scale correction to `extract_teacher.py`.

- **The in-game sprite is 54 pixels tall.** Not 54 wide — height is what
  `TARGET_H` normalises. Every readable thing about this character has to
  survive that, which is why the silhouette instructions below are specific
  and the facial ones are not.
- **One teacher per sheet.** Eight poses cannot all clear §R0's four-times-final
  floor on one 1536×1024 frame, and §R0 says split rather than shrink.

> Paint **one character in four poses**, left to right in a single row, each
> pose separated by a wide black gutter:
> **(1) MAIN** — standing square to the viewer, arms at her sides, the clearest
> full view of the design; **(2) IDLE** — the same character shifted slightly,
> weight on one foot, head tilted, as if drifting in place; **(3) WALK** — a
> mid-stride step, one leg forward, cardigan swinging; **(4) ATTACK** — both
> arms raised, a dark book floating open above her upturned palms.
>
> **All four figures must be the same height as each other** — at least **640
> pixels tall** — **standing on one common invisible ground line, with the whole
> body from the top of her head to the soles of her shoes visible in every one
> of the four.** No pose may be cropped, floated, tilted away from the viewer or
> drawn smaller than the others. Four full-length figures in a row, like a
> costume line-up. Reserve the room for the fourth pose before starting the
> first.
>
> **The character:** a schoolteacher who has been in this building far too long.
> Chibi proportions as §0 describes — a big round head on a small stooped body,
> which for her means a *long* cardigan and skirt reaching almost to the floor,
> so she still reads as the tall thin one of the pair. A buttoned cardigan over a
> straight below-the-knee skirt, flat shoes, a limp scarf. Her clothes are the school's
> own colours — chalk-grey, dusty charcoal, faded oatmeal — and they are creased,
> untucked, powdered with chalk dust and grimed at the hems. Her grey hair is
> pinned in a high bun that has half fallen out of itself. Her glasses are
> **broken**: heavy dark frames sitting crooked, one lens spidered with cracks,
> the other lens gone. She is greyed and hollow, with sunken eyes and a slack
> jaw — **stiff and vacant, like a sleepwalker, not a corpse.**
>
> **No blood, no wounds, no exposed bone, no rot, no green skin, no reaching
> claws.** The horror is that she is still trying to teach. Keep her in the
> register of a haunted-house cartoon ghost — the audience is children.
>
> **Ignore the palette block's instruction to stay dark for this character.**
> That rule is for walls and floors. She is a *character*, lit and painted like
> one: pitch her overall brightness at about that of a lit face in a dim room,
> clearly lighter than any wall behind her, with real light falling on the
> cardigan, the scarf, her hands and her face. Muted colour, yes — but **not
> dark**. If she would disappear against a near-black floor, she is wrong.
>
> **She must read at 54 pixels tall**, so build her out of a few large shapes:
> a narrow vertical silhouette, the wide skirt hem as her base, the tall tilted
> bun stacked on top of her big round head, and the broken glasses — drawn large,
> as chibi eyewear is — as the single bright glint on her face. She is an **actor, not scenery** — keep her
> lighter and higher in contrast than the dark, desaturated classroom behind
> her, especially the pale chalk-dusted cardigan.
>
> In the **bottom-right corner** of the sheet, in its own black space, well
> clear of the figures, paint **exactly one** extra item — no second version, no
> variations: **her projectile**, a small hardback book flying open, pages
> fanned, trailing ragged violet-black smoke and a few loose torn pages behind
> it. Seen from the side, travelling left to right, about 200 pixels wide.

---

## §R9 Teacher monster — male

The counterpart to §R8. Same sheet layout, same four poses, same rules.

⚠️ **The pair must differ by silhouette, not by face.** At 54 pixels tall a
face is about six pixels of it, so "one is a man, one is a woman" is invisible
in game — whatever separates them has to be visible in outline alone. She is a
tall narrow vertical with a wide hem; he is deliberately built as the opposite.
Do not soften that contrast in the name of matching them.

> Paint **one character in four poses**, left to right in a single row, each
> pose separated by a wide black gutter and each at least **640 pixels tall**:
> **(1) MAIN** — standing square to the viewer, arms at his sides, the clearest
> full view of the design; **(2) IDLE** — the same character shifted slightly,
> shoulders sagging, head lolling; **(3) WALK** — a heavy mid-stride step, one
> leg forward, jacket swinging open; **(4) ATTACK** — both arms raised, a dark
> book floating open above his upturned palms.
>
> **The character:** a schoolmaster who has been in this building far too long.
> Chibi proportions as §0 describes, and for him that means going the other way
> from §R8: a wide, heavy-shouldered body hunched forward from the neck, almost
> as broad as it is tall, in a boxy ill-fitting three-piece suit — square jacket, waistcoat, trousers pooling over
> his shoes. The suit is brown-grey and dust-caked, elbows worn shiny, one
> pocket hanging half off, his tie yanked loose and flung over one shoulder,
> his shirt untucked. He is balding, with a few long strands combed sideways
> across his scalp. His glasses are **broken**: round wire frames bent out of
> shape, one lens spidered with cracks, the other lens gone. He is greyed and
> hollow, with sunken eyes and a slack jaw — **stiff and vacant, like a
> sleepwalker, not a corpse.**
>
> **No blood, no wounds, no exposed bone, no rot, no green skin, no reaching
> claws.** The horror is that he is still trying to teach. Keep him in the
> register of a haunted-house cartoon ghost — the audience is children.
>
> **He must read at 54 pixels tall**, so build him out of a few large shapes:
> a squat, broad, top-heavy silhouette, the square shoulders of the jacket as
> his widest point, the bare domed scalp with its few combed strands, and the
> broken glasses — drawn large, as chibi eyewear is — as the single bright glint
> on his face. He is an
> **actor, not scenery** — keep him lighter and higher in contrast than the
> dark, desaturated classroom behind him, especially the pale shirt and collar.
>
> Do not paint a projectile on this sheet — his is the same flying book as §R8.
