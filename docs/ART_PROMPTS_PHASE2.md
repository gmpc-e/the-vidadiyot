# Prompt pack — Phase 2: things that move

Phase 1 (`ART_PROMPTS.md`) was the map: floors, walls, doors, item icons. Phase 2
is **animation** — the frames the game has never had.

**Where this actually stands.** When the pack was written nothing in the game was
animated at all: four *single* painted poses per warrior, one frame per monster,
and a walk cycle faked in code. That is no longer true. Both warriors and both
classroom monsters now run on real painted strips, turn to face where they walk,
and flinch when they are hit; the projectiles and effects that were code
primitives are painted.

What is left is the boss, the teachers' attack, two back-facing walks and two
effect strips — listed below.

**⚠️ `tools/art_request.py` parses this file** — `## Sheet N — Title` headings,
prompt in the **blockquote** beneath. Prose outside the quote is not sent.

---

## What is outstanding — read this first

| # | sheet | what it is | why |
|---|---|---|---|
| 1 | **§S8 Emri** | six rows: three walks, materialise, strike, hurt | the boss, and the worst-animated thing in the game — one sprite faded in and out |
| 2 | **§S11 the teachers** | wind-up + hurt, one sheet each | the enemy the player meets most. Their attack pose is extracted and **unusable**: both §R8/§R9 sheets drew it a quarter smaller than its siblings, so the teachers currently attack without moving |
| 3 | **back walks** for Little Terror¹ and Little Snir | one row each, three frames | they turn toward the camera and sideways but never away |
| 4 | §S7 defeat puff | one shared 3-frame strip | killing something is the core verb and has no visual |
| 5 | §S9 projectiles | three strips | the fireball and the web are painted now; the **lightbolt** is still a code primitive |

¹ Little Terror's back walk is *done* — this is Snir's.

**Everything else in this pack is delivered.** ✅ §S1 Wallad, §S2 Roni,
§S5 Little Terror, §S6 Little Snir, Priority 3b effects, three of five Priority 4
ambience rows. ❌ §S10 is cancelled.

### The five rules that have actually cost re-rolls

1. **One sheet per character, one animation per row** — separate images drift in
   scale against each other and the character changes size when it stops walking.
2. **Three frames a row**, evenly spaced, with black gutters wide enough to cut
   between. Told "four", the model reliably draws three.
3. **Nothing may leave the character's outline** — a sword held out sideways, a
   trailing cloak, a beam, a projectile in flight. It reaches into the next frame
   and welds the two together, and the row cannot be cut apart.
4. **Every frame in a row stands on one ground line, at one size.** A floating or
   shrunken frame makes the animation jump and there is no fixing it afterwards.
5. **Describe the character that is already in the game.** Open
   `assets/sprites/<name>_menu.png` first. Two prompts in this pack once asked
   for characters the game does not have and bought perfectly good drawings of
   the wrong people.

⚠️ **A HURT row is required on every character sheet.** See §A — it is the most
frequent thing that happens to anything in this game, and until it had art the
entire response was a white tint over the sprite.

---

## §0 Style block — paste this first, every time

Unchanged from Phase 1, and it still matters more than the sheet prompt: it is
what keeps sheet 9 looking like sheet 1.

> **Style:** Hand-painted 2D game art for a horror-lite cartoon game set in an
> abandoned school at night. Painterly illustration with clean dark outlines and
> chunky, readable shapes — the register of Luigi's Mansion or Costume Quest, not
> photoreal and not survival horror. Slightly grimy, dusty, decayed, but never
> gory and never frightening; the audience is children.
>
> **Palette:** desaturated cool greys, muted browns and deep blue-blacks for all
> environment surfaces. Accent language, used sparingly: brass and warm gold for
> metal, blood red and toxic slime green for damage and decay, deep purple for
> cloth. **Characters, monsters, projectiles and pickups are the exception — they
> stay bright and saturated**, because they have to stay legible against a dark
> floor at 640×360.
>
> **Lighting:** flat, even, ambient. No strong directional light, no baked drop
> shadows, no glow. Lit as if by dim overcast moonlight from directly above.
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
> - **Wallad, the knight: a realistically proportioned adult** — a lean, upright
>   man in heavy plate whose **head is about one sixth of his total height**.
>   Measure it: six of his heads stacked up equal his full standing height.
>   **He is not a chibi character and not a dwarf.** Do not give him a big round
>   head, a short stocky body, or a child's proportions. If in doubt, draw him
>   taller and thinner than feels natural for a game sprite.
>
> Whichever it is, build the figure out of a few big shapes rather than fine
> detail: at final size a face is a handful of pixels, so the silhouette of the
> head, the hair and the gear is most of what the player will ever see.
>
> **Presentation:** pure black (#000000) background. No scene, no vignette, no
> floor beneath the subject, no gradient, no border, no frame. **No text, no
> labels, no captions, no frame numbers, no watermarks, no UI panels.**
> Output at 1536×1024, landscape.

---

## §A The animation rules — read once, they apply to every sheet below

**Registration is the whole game.** If the subject shifts or changes size between
frames the animation jitters when played, and there is no fixing it afterwards —
not in the extractor, not in code. Every request below repeats the registration
clause on purpose. Do not trim it out to save space.

⚠️ **Ask for one sheet per character, with one animation per row.** This pack
originally asked for one strip per image and that was wrong. A hand-made grid —
walk on the top row, attack on the next, hurt below that — is *better* on every
axis: one request means one consistent character across every animation, where
separate requests drift, and the extractor reads a named row out of a grid with
a row scan. The best sheet this project has received
(`champions/elad-the-knight/elad-knight-sheet-v2.png`) is exactly this shape,
and it registered to **0–1px** where the best single strip managed 4px.

⚠️ **A sheet that restyles the character is a failed sheet.** These animate
characters already in the game and get intercut with their existing poses, so
the proportions in §0 are not a suggestion. Nine rolls were spent on Wallad's walk
because §0 once said "every character is chibi" — a rule true of the *monsters*
and wrongly applied to the whole cast, which produced perfectly good drawings of
a man who is not in this game. **Open `assets/sprites/<name>_idle.png` and
describe what is actually there** before writing a word.

⚠️ **Do not ask for poses the game has no mechanic for.** Two delivered sheets
carried a beautiful lightning-sword attack. Wallad's `power` is `None` in
`game/entities/warriors.py` — he has no special ability — so a third of each
sheet was art for something that does not exist. Worse, the beam crossed between
frames and welded them into one uncuttable blob. **An effect that leaves the
character's outline breaks the sheet as well as wasting it.**

### Paste this with every request

> **Layout:** a grid on a pure black background. **Each row is one animation and
> holds exactly three frames**, side by side, evenly spaced. Three per row — not
> two, not four. Count them before you finish.
>
> **Nothing may touch anything.** Leave a band of pure black between neighbouring
> frames **at least half as wide as the subject**, the same between rows, and the
> same as a margin around the whole image. The frames are cut apart by finding
> the black between them, so two frames touching anywhere are read as one and the
> row is thrown away. Draw the subject smaller if that is what it takes.
>
> **Keep everything inside the character's own outline.** A sword held out
> sideways, a trailing cloak, an outstretched arm or a spell effect reaches
> across the gap and joins two frames together — **this is the single most
> common way these sheets fail.** Angle a blade downward beside the leg or
> upright against the shoulder. Never draw a beam, a projectile or a shockwave
> leaving the character.
>
> **Draw one ground line per row and put every frame's feet on it.** Imagine a
> horizontal line running the width of the row; the soles of the subject's shoes
> touch that same line in every frame of that row. A frame drawn floating, or
> drawn smaller than its neighbours, makes the animation jump when it plays. This
> is the most important instruction on this page.
>
> **The subject is the same size, in the same position within its frame, from the
> same camera angle, in every frame** — identical framing, identical scale,
> identical distance. Only the named detail changes. If a pose reaches upward it
> gets *taller*; it is not moved up and it is not scaled down to fit. Leave
> headroom for it.
>
> No text, no numbers, no labels, no borders, no separating lines, no grid lines.

### ⚠️ Every character sheet must carry a HURT row

**Non-negotiable, on every monster and every champion, forever.** Being hit is
the most frequent thing that happens to anything in this game, and until
2026-08-20 the entire response was a **white tint over the sprite** — the monster
flashed into a white box, which reads as a rendering glitch rather than as pain.
The tint is still there as the fallback for a character with no hurt art, and
that is all it is now.

Three frames, and they are always the same three:

1. **the impact** — head snapped back, body recoiling, arms flung out
2. **the stagger** — doubled over, a half step back
3. **the recovery** — straightening up, ready again

⚠️ **Do not paint an impact effect into the frame.** Sparks, stars, red rays: the
game already flashes and shakes on a hit, and a painted one fires alongside it.
Wallad's delivered hurt row has red rays in it and they fight the code's own flash.

The game plays this in step with `MONSTER_HURT_TIME` (monsters) or `hurt_flash`
(warriors), so all three frames get seen — it is a performance, not a tint.

### Four rules the code imposes

| Rule | Why |
|---|---|
| **Three frames per row** | Enough to read, few enough to register. A three-frame walk is contact / passing / contact, and the game plays it **ping-pong** (1-2-3-2) for a four-beat loop out of three drawings — `Entity.PINGPONG`. A one-shot like a swing plays straight through and must *not* bounce, or it runs its wind-up backwards after the strike. |
| **One sheet per character, one animation per row** | ⚠️ This said "one strip per image". Separate images drift in scale and detail against each other and then the character changes size when it stops walking. One sheet fixes that by construction, and `tools/extract_phase2.py` picks rows out of it by index. |
| **Everything faces the viewer** | ⚠️ This said "faces screen-right" and it was wrong for the warriors, which cost a roll each. Wallad and Roni are painted **front-on** in `assets/sprites/*_idle.png`, and a side-on walk under a front-on idle turns the character 90° the instant it moves. Paint characters in a **three-quarter front view, angled slightly to screen-right** — that mirrors cleanly (`player.py` flips the sprite for leftward movement, and a mirrored three-quarter is the opposite three-quarter). Monsters were always painted facing the viewer. |
| **Paint big, downscale in the tool** | Same as Phase 1. Never draw at final pixel size. |

### Make the movement bigger than feels right

⚠️ Wallad's delivered walk registers perfectly and is **too subtle to read at
48px** — the legs move, but it looks like a shuffle rather than a stride. At
final size a character is about as tall as this line of text. Exaggerate:

- **Lift the front knee high** and land the foot clearly ahead of the body.
- **Bob the whole body** — noticeably lower on the two contact frames, at its
  highest on the passing frame. That vertical bounce is most of what sells a
  front-facing walk, because the legs are foreshortened from the front.
- **Swing the arms** in opposition, far enough to change the silhouette.
- On an attack, make frame 1 wind up **behind** the body and frame 3 finish
  **fully extended**. Half-measures vanish at this size.

# Priority 1 — the warriors

## ⚠️ Facing: the thing these sheets have to solve

The player walks in four directions and the sprite currently **faces the viewer
in all of them**. Here is exactly what the game does today:

| walking | what is drawn |
|---|---|
| right | the painted frame, as-is |
| left | the same frame, **mirrored** |
| up / down | the same frame, unchanged |

So left/right *is* already handled in code — `Player.facing` is ±1 and
`player.draw` flips the sprite. It reads as "always staring at you" for two
reasons: the delivered art is very nearly **square-on front**, so mirroring it
produces almost the same picture; and **up and down have no art at all**.

**This cannot be fixed in code. It needs a back view.** A character walking away
from the camera shows its back, and no amount of flipping a front view produces
one. The three directions each need their own row:

- **walk toward** — front three-quarter, the view we have
- **walk away** — from behind: back of the head, cape, shield seen from behind
- **walk sideways** — a true side profile, facing screen-right, which the code
  then mirrors for leftward movement

A **strong three-quarter** on the toward/away rows matters more than it sounds:
the more the character is turned, the more the mirror actually changes, and the
less the sprite reads as looking at the camera.

⚠️ **The v3 sheet already delivered has all three.**
`champions/elad-the-knight/elad-knight-sheet-v3.png` was set aside as "better
sheet, worse fit" because the engine only mirrors one facing — that judgement was
made before this came up, and it is now the *reason to want it*. If a directional
Wallad is wanted, most of that art exists; it needs re-cutting into rows and a
four-way `facing` on the player (small: track the dominant axis of movement and
pick the row).

**Ask for the directions as their own sheet**, separate from the combat rows —
five rows of three on one 1536×1024 leaves each figure under 200px tall, which
is below the 4×-final-size floor. Two sheets per character:

1. **the walks** — toward / away / sideways, three rows
2. **the combat** — attack / hurt, two rows

---

One sheet each. Three rows, three frames a row: **walk**, **attack**, **hurt**.

The game already has a single painted pose for each of those four states plus
idle, and a sheet replaces the three that move. Idle stays a single frame — a
breathing loop is a nice-to-have and the state a player stares at longest is the
one where a bad frame is most obvious.

---

## Sheet 1 — Wallad, the knight — ✅ delivered

✅ `elad-knight-sheet-v2.png` gave the **attack** (row 2, 0px baseline spread).
✅ `elad-knight-sheet-v3.png` — set aside as "better sheet, worse fit", then
wanted after all — gave the three **directional walks**: side (row 1, cells
1–3), away (row 3, cells 2–4) and toward (row 4, cells 1–3). Wallad now turns to
face where he is going. ⚠️ Its rows are drawn at different sizes, which does not
matter because each is normalised to the same 48px output, but is worth avoiding
in a new sheet: **draw every row at the same scale.**
❌ Its third row was a lightning-sword power Wallad does not have; the beam bridged
all three frames and could not be cut apart either. Skipped — see §A.
✅ `elad-hurt-bottom-left.png` row 3 gave the **hurt**: struck / braced /
recovered. ⚠️ Its first cell has painted red impact rays; the game already
flashes on damage, so **leave hit effects to the game** on any future hurt row.

> Paint **Wallad, a grown man in his fifties** with grey hair and a full white
> beard, of ordinary adult proportions — **not a child, not big-headed**. He
> wears dark battered plate armour over a **deep blue tunic bearing a gold
> rampant lion**, brown leather boots and belt, a ragged blue cape. He carries a
> longsword and a **round wooden shield with an iron rim and the same gold lion**
> — the shield is a large, obvious part of his silhouette and must be visible in
> every frame. Seen **from the front, turned very slightly toward screen-right**.
>
> **Row 1 — walk.** Walking on the spot toward the viewer. Frame 1 the left leg
> forward with the knee lifted high and the body at its lowest; frame 2 the legs
> passing close together and the whole body lifted to its highest; frame 3 the
> right leg forward, knee high, body low again, opposite arm swung forward.
> **Exaggerate the knee lift and the body bob** — from the front the legs are
> foreshortened, so the bounce is what makes it read as walking.
>
> **Row 2 — sword swing.** Standing on the spot. Frame 1 the wind-up, sword drawn
> right back behind the shoulder, weight on the back foot; frame 2 the blade at
> the top of its arc; frame 3 the strike, blade swept fully forward and down
> across the body, weight thrown onto the front foot. Keep the blade angled
> across his own body, never straight out to the side.
>
> **Row 3 — hurt.** Standing on the spot, taking a blow. Frame 1 the impact — the
> head snapped back, the body recoiling, the shield arm flung up; frame 2 doubled
> over and staggering back a half step; frame 3 straightening again, shield
> raised, ready. His feet stay on the same line throughout.

---

## Sheet 2 — Roni, the warrior princess — ✅ delivered

`roni-sheet-v2.png` gave all three rows — walk, knife throw and hurt — at 2, 2
and 9px baseline spread, first try. The prompt below is the one that produced it;
keep it as the template for any character sheet from here.

✅ `roni-directional.png` then gave the **directional walks** — four rows at 2,
2, 1 and 0px spread. Only three are used: front, side-right and back. ⚠️ The
fourth is side-*left* and is deliberately skipped, because `player.draw` mirrors
the side view and a painted left-facing row can only disagree with it. **Do not
ask for a left-facing row.**

> Paint **Roni, a young warrior princess**: a girl of about ten with long wavy
> auburn hair and **a small pointed gold crown**, in ornate gold-trimmed plate
> armour over **a white skirt**, with a **deep purple cloak** down her back and
> brown boots. She is stylised — a large head and big eyes on a real body, about
> four heads tall — **not a hooded rogue and not blonde**. She carries throwing
> knives, not a sword. Seen **from the front, turned very slightly toward
> screen-right**.
>
> **Row 1 — walk.** Walking on the spot toward the viewer. Frame 1 the left leg
> forward with the knee lifted high and the body at its lowest; frame 2 the legs
> passing close together and the whole body lifted to its highest; frame 3 the
> right leg forward, knee high, body low again, opposite arm swung forward. The
> cloak sways behind her, trailing the step. **Exaggerate the knee lift and the
> body bob.**
>
> **Row 2 — knife throw.** Standing on the spot. Frame 1 the throwing arm cocked
> right back beside her head, knife held ready, body coiled; frame 2 the arm
> coming over, knife still in hand; frame 3 the arm snapped fully forward and
> down, hand open and empty, body leaning into the throw. **Do not paint the
> knife in flight** — the game draws the projectile, and anything leaving her
> outline welds the frames together.
>
> **Row 3 — hurt.** Standing on the spot, taking a blow. Frame 1 the impact — the
> head snapped back, the body recoiling, one arm flung up; frame 2 doubled over
> and staggering back a half step; frame 3 straightening again, ready. Her feet
> stay on the same line throughout.
>
> The gold, the crown and the white skirt are the bright elements; the cloak and
> armour stay deep and muted.

---

# Priority 2 — the monsters

Same grid rules. These face the viewer square-on and never mirror.

## Sheet 5 — Little Terror — ✅ delivered

✅ `little_terror_sheet_v3.png` (a superset of v2) gave walk, fireball wind-up,
hurt and side views of all three, plus her painted fireball and impact burst.
`little-terror-back-face-sheet.png` then gave the back walk — three frames taken
from OPTION A at frames 0, 2 and 4, a quarter-cycle apart. She is the first
monster with the player's full facing.

⚠️ **The fire and impact rows had to be cut by gutter, not by even division.**
Their items are a catalogue of wildly different widths — an ember is 52px and a
comet 156 — so equal cells sliced straight through the fireball and shipped two
half-moons. Even division is only ever right for evenly *spaced* frames.

⚠️ **Glows need a harder key than characters do.** They have a soft falloff into
the black, and at a character's luma cut the falloff stays opaque — the impact
burst shipped with a visible dark rectangle round it, which is what "a box shows
up when something is hit" turned out to be.

⚠️ **This prompt used to describe a different monster** — "a squat imp-like
creature with a round body and stubby arms" — and would have bought a good
drawing of something that is not in the game, exactly as §S2 did before it was
rewritten. The description below is taken from `assets/sprites/terror_menu.png`.
Check it against that file before changing a word.

> Paint **Little Terror**, a small imp girl: a **chibi** figure about three heads
> tall with a large round head, huge angry eyes and a scowl, wild dark hair, a
> pair of **curved yellow-cream horns** sweeping up from her head, **gold hoop
> earrings**, and warm orange-tan skin. She wears a ragged off-white sleeveless
> top. Barefoot, with stubby hands and feet. Seen **from the front, facing the
> viewer** — she never turns.
>
> **Row 1 — walk.** Walking on the spot toward the viewer, arms swinging. Frame 1
> the left leg forward with the knee lifted high and the body at its lowest;
> frame 2 the legs passing together and the whole body lifted to its highest;
> frame 3 the right leg forward, body low again. **Exaggerate the bob** — the
> legs are foreshortened from the front, so the bounce carries the walk.
>
> **Row 2 — winding up a fireball.** Standing on the spot. Frame 1 arms down at
> her sides, eyes dim, **no fire anywhere**. Frame 2 she hunches, both hands
> drawn in toward her chest, a small ember of purple-and-orange fire igniting
> between her palms, eyes brightening. Frame 3 the ember swollen into a fierce
> fireball at full size held between her hands, her body leaning back, eyes
> blazing, horns catching the light. **Do not paint the fireball travelling
> away** — the game draws the projectile, and frame 3 is the instant before it
> leaves. Anything that leaves her outline welds the frames together.
>
> **Row 3 — hurt.** Frame 1 the impact — head snapped back, body recoiling, arms
> flung out; frame 2 doubled over, staggering back a half step; frame 3
> straightening up again, scowling. Her feet stay on the same line throughout.
>
> The fire is the bright element; her body stays warm but muted so it does not
> compete with it.

---

## Sheet 6 — Little Snir — ✅ delivered

✅ **Both v2 and v3 were needed and neither is a superset**: v2 is entirely
front-facing and v3 entirely side-facing, each with the same three rows. Little
Terror's v3 happened to contain her v2; Snir's do not, so taking "the newer one"
would have thrown her front views away.

⚠️ **v3 is drawn facing *left*** and the convention is right — every directional
sprite is painted facing screen-right and mirrored for leftward movement, so a
left-facing row disagrees with the mirror on every frame. Flipped on the way in.

⬜ **Neither monster has a back-facing walk yet.** Little Terror got one on its
own sheet; Snir turns toward the camera and sideways but never away. That is the
one refinement left on her.

⚠️ **This prompt used to ask for a spider** — "a round dark-bodied creature with
too many thin legs and pale glassy eyes". Little Snir is a girl. The description
below is taken from `assets/sprites/snir_menu.png`.

> Paint **Little Snir**, a small forest-child creature: a **chibi** figure about
> three heads tall with a large round head, big dark eyes, **long pointed elf
> ears**, and long dark tangled hair falling past her shoulders. She wears a
> ragged pale cream shift dress and is barefoot, with pale-tan skin. She is
> sad-looking rather than fierce. Seen **from the front, facing the viewer** —
> she never turns.
>
> **Row 1 — walk.** Walking on the spot toward the viewer. Frame 1 the left leg
> forward with the knee lifted high and the body at its lowest; frame 2 the legs
> passing together and the whole body lifted to its highest; frame 3 the right
> leg forward, body low again. **Exaggerate the bob.**
>
> **Row 2 — winding up a web.** Standing on the spot. Frame 1 arms down at her
> sides, **no silk anywhere**. Frame 2 she raises both hands in front of her
> chest and pale silk gathers into a small loose tangle between them, drawn out
> of her own hair. Frame 3 the tangle swollen into a dense pale ball of web at
> full size held between her hands, her body arched back. **Do not paint the web
> travelling away** — frame 3 is the instant before it leaves.
>
> **Row 3 — hurt.** Frame 1 the impact — head snapped back, body recoiling;
> frame 2 doubled over, staggering back a half step; frame 3 straightening up
> again. Her feet stay on the same line throughout.
>
> The silk is the bright element; her dress is pale but muted and her hair stays
> near-black.

---

## Sheet 11 — The teachers — ⬜ their attack pose is currently unusable

Two sheets, one per teacher. They already have a walk, cut from the §R8/§R9
character sheets — but **their ATTACK pose is extracted and cannot be used**:
both sheets drew it about a quarter smaller than its siblings, so wiring it makes
the teacher visibly shrink every time it casts. They are the enemy the player
meets most and they currently attack without moving at all.

Take the character description straight from `docs/ART_PROMPTS.md` §R8 (the
female teacher) or §R9 (the schoolmaster) — those are accurate and produced the
art that is in the game — and ask for these rows:

> **Row 1 — winding up a book.** Standing on the spot, facing the viewer. Frame 1
> arms down at their sides, **no book anywhere**. Frame 2 both hands raised in
> front of the chest, a hardback book opening between them, faint violet-black
> smoke starting to leak from its pages. Frame 3 the book held high overhead,
> fully open, pages fanned, smoke pouring off it. **Do not paint the book flying
> away** — the game draws the projectile, and frame 3 is the instant before it
> leaves.
>
> **Row 2 — hurt.** Frame 1 the impact — head snapped back, body recoiling, arms
> flung out; frame 2 doubled over, staggering back a half step; frame 3
> straightening up again. Feet on the same line throughout.

⚠️ **All three frames of a row must be the same size.** This is the specific
thing both earlier teacher sheets got wrong. See §A.

---

# Priority 3 — the beats that currently have no art at all

## Sheet 7 — Monster defeat puff (3 frames)

Killing something is the core verb and it currently has no visual. One neutral
strip covers every monster: the game tints and scales it.

> A three-frame dissipation effect on a pure black background, no creature in it —
> only the smoke. Frame 1 a small tight puff of pale grey dust just beginning to
> bloom; frame 2 the cloud expanded to full size, ragged and billowing, with a
> few dark specks flung outward; frame 3 the cloud thinning and spreading wider,
> broken into the last torn wisps, almost transparent. The cloud stays centred in
> exactly the same spot in every frame and only grows and fades. Neutral pale grey and off-white so it can be recoloured.

## Sheet 8 — Emri, the boss — ⬜ **the last character sheet the game needs**

Emri is the only fight in the game with phases, and it is animated worse than
anything else in it: one sprite, faded in and out on alpha. It drifts, it blinks
in at arm's length, it takes eight hits, it vanishes at 75/50/25% and comes back
— and none of that is visible in the art.

**Deliver this as one sheet, in the grid format §A describes, with these rows.**
Take the character from `assets/sprites/emri_menu.png`: it is already painted and
in the game, and the description below is written from it.

> Paint **Emri, the disappearing monster**: a **chibi** child-shaped creature
> about three heads tall, made largely of shadow — a big round head under a
> tangled dark mane of hair that spills past its shoulders, pointed ears, thin
> dark limbs, and **pale burning yellow-white eyes** that are the brightest thing
> on it by a long way. Its body is near-black, ragged at the edges as if it is
> coming apart into smoke. It is a *lost child* rather than a demon — unsettling,
> not gory. The audience is children.
>
> Emri is **taller than the other monsters** — it is the boss — so draw it a
> little above the height of the imp and the forest child on their own sheets.

### Row 1 — walk, toward the viewer (3 frames)

> Walking on the spot toward the camera. Frame 1 the left leg forward with the
> knee lifted and the body at its lowest; frame 2 the legs passing together and
> the whole body lifted to its highest; frame 3 the right leg forward, body low
> again, opposite arm swung forward. **Exaggerate the bob** — from the front the
> legs are foreshortened and the bounce is what makes it read as walking. Its
> hair and the ragged edges of its body trail behind the movement.

### Row 2 — walk, away from the viewer (3 frames)

> The same three-step walk seen **from behind**: the back of the head, the mane
> of hair filling most of the silhouette, no face and no eyes visible at all.

⚠️ Neither of the other two monsters has this row and both are worse for it —
they turn toward the camera and sideways but never away. **A back view cannot be
derived from a front view**, and this is the row that always gets forgotten.

### Row 3 — walk, in profile (3 frames)

> The same three-step walk seen **from the side, facing screen-right**. One eye
> visible, the mane trailing behind it.

### Row 4 — materialising (3 frames)

The blink is the whole fight, and the code plays this row *forwards* to arrive
and *backwards* to leave — so it must read both ways.

> Frame 1 barely there: a faint vertical smear of darker air and two dim points
> of light where the eyes will be. Frame 2 half-formed, the silhouette readable
> but ragged and smoking at its edges, streaming upward. Frame 3 fully present,
> solid and sharp, eyes at their brightest.
>
> ⚠️ **The figure is in exactly the same position, at exactly the same height, in
> all three frames.** It does not rise, grow, drift or change pose — it only
> *condenses*. Played backwards this same row has to read as vanishing, which it
> only does if nothing but density and edge ever changes.

### Row 5 — the lightbolt strike (3 frames)

> Standing on the spot, throwing a bolt of pale blue-white lightning. Frame 1 the
> wind-up: arms drawn in, body coiled, eyes flaring, a small knot of white energy
> gathering at its hands. Frame 2 the energy grown to full size between its
> palms, body leaning back. Frame 3 the release: arms snapped forward, hands open
> and empty, body driven forward by it.
>
> ⚠️ **Do not paint the bolt travelling away** — the game draws the projectile,
> and frame 3 is the instant after it leaves. Anything that reaches outside the
> character's own outline welds two frames together and the row cannot be cut.

### Row 6 — hurt (3 frames)

> Frame 1 the impact: head snapped back, body recoiling, thin arms flung out,
> the ragged edges of its body blown outward like smoke off a candle. Frame 2
> doubled over, staggering back a half step, eyes screwed shut. Frame 3
> straightening up again, eyes reopening bright.
>
> ⚠️ No sparks, stars or impact rays painted into the frame — the game already
> flashes and shakes on a hit, and a painted one fires alongside it.

## Sheet 9 — Projectiles in flight (3 frames, one strip each)

Three separate images, one per projectile. All three are code primitives today.

> **Fireball** — a three-frame loop of a flying ball of purple and orange flame
> travelling screen right, seen from the side. The flame licks and churns and the
> trailing tail whips, but the ball's centre stays in exactly the same spot in
> every frame at exactly the same size. Bright, saturated, hot core.

> **Web ball** — a three-frame loop of a flying tangled ball of white spider silk,
> loose strands trailing behind it. The strands writhe between frames; the ball's
> centre and size never move. Bright pale silk against black.

> **Lightning bolt** — a three-frame loop of a jagged bolt of pale blue-white
> energy travelling screen right, crackling. The bolt's overall length, angle and
> position stay identical in every frame; only the branching forks change.

## Sheet 10 — ~~The book coming home~~ — ❌ **do not request**

⚠️ **Cancelled 2026-08-20.** The book-return burst was removed from the game at
the user's request: a shower of coloured light over a rising icon read as a
mobile game's reward animation in a dark school at night, the same mistake the
victory screen made with confetti. The beat is now the chime, the camera shake
and the HUD counter, and `systems/effects.py` was deleted with it.

The prompt is kept only so nobody re-derives it from the §6 roadmap entry and
requests art for a thing that was deliberately taken out.

> A four-frame burst effect on a pure black background: a ring of light expanding
> outward. Frame 1 a small bright point with a tight ring just forming; frame 2
> the ring expanded and thick, with radiating spokes of light and a scatter of
> star-shaped sparks; frame 3 the ring wider, thinner and dimmer, the sparks
> flung further out; frame 4 the last faint ring and a few drifting motes. The
> burst stays centred on exactly the same point in every frame. Paint it in
> **neutral white and pale gold** — the game recolours it to the classroom's
> colour.

---

# Priority 3b — effects and states — 🔶 delivered by hand, 2026-08-20

Not requested through this pack: hand-made sheets that arrived as **option
boards** (a weapon card, a grid of splash choices) rather than strips. They are
cut by `tools/extract_effects.py` with **measured crops**, because a card's
layout is not something a row scan can reason about.

✅ **Roni's throwing knife** — the "DETAIL VIEW" panel. ⚠️ Sized by *width*: the
old sprite was 34px wide and the note was that it looked too big, and this blade
is longer and thinner, so matching heights would have made it wider still.

✅ **Little Snir's web** — one of twelve painted flight webs, rotated to its
travel direction in `WebProjectile.draw`. ⚠️ The painted web is drawn head-forward
with its trail behind, so unlike the drawn version — which was radially
symmetrical — it has to be *turned to face where it is going*.

✅ **Zina's bite splash** — the radial burst from the option row: symmetrical, so
it needs no rotation, and it reads at 30px where the directional spatters do not.

✅ **Both warriors trapped in a web**, replacing the drawn strands. ⚠️ Two traps
in these two sheets: their frames are **joined by trailing silk**, so gutter
detection reads a whole row as one item and `slice_strip(cells=N)` divides the
span evenly instead; and they arrive **much darker than the idle they cut
against** (luma 31 and 52 against 74 and 88), which breaks "actors stay bright"
the instant the player is caught.

⚠️ **Do not ask for painted captions.** Every one of these sheets has them
("TRAPPED (WEB)", "IMPACT SPLASH OPTIONS"). They happen to sit above their rows
so a band scan misses them — that is luck, not design, and §0 forbids them.

---

# Priority 4 — ambience — 🔶 three of five rows delivered

✅ `map/props/phase2-p9.png` gave the **flickering fluorescent tube**, the
**dripping pipe** and **five cobwebs**, all on clean black. They are cut by
`tools/extract_ambience.py` and placed by `game/world/ambience.py` — in every
room, including the corridor and the entrance, which `decor.py` has never
furnished at all.

❌ **Two of its five rows are unusable and were rejected at the sheet.** The
corner-cobweb row is painted on a wall panel and the light-shaft row on a room
interior — opaque rectangles of scene where §0 asks for pure black. There is no
keying a subject off a painted background; the panel would arrive in game as a
visible rectangle around the web. If those two are wanted, re-request them **on
black**, and note the game has no windows for light shafts to come through.

⚠️ **Thin bright line art does not survive a big downscale.** A cobweb is 1px
strands of pale silk; averaged from 200px down to 24px the strands blend with the
black around them and land at **luma 12–17** — dark smudges. The shape is intact
in the alpha the whole time, so `spritelib.flatten_color` throws the averaged
colour away and repaints the mask a constant. ⚠️ And repaint it *dim*: the same
averaging spreads each strand, so at full strength a web becomes a solid pale
sheet and the brightest thing on a screen whose rule is "environment dark,
actors bright".



Four short loops that make rooms feel inhabited. Same §A rules; 3–4 frames each,
one strip per image.

- **Flickering fluorescent tube** (4) — *a long ceiling light fixture seen from
  below: fully lit, dim, dark, then a too-bright flare.*
- **Cobweb in a corner** (3) — *a corner web sagging and swaying very slightly;
  the anchor points do not move.*
- **Dripping water** (4) — *a droplet forming on a pipe, swelling, falling, and
  splashing.*
- **Dust motes in moonlight** (4) — *a soft shaft of pale light with specks
  drifting through it; the shaft itself never moves.*

---

## Delivery checklist

Same as Phase 1, plus the animation-specific ones:

- [ ] Background is **pure black**, not very dark grey
- [ ] **No text anywhere** — especially no frame numbers
- [ ] One strip per image, single horizontal row
- [ ] **Every frame identically framed, identically scaled, feet on one baseline**
- [ ] Characters face **screen right**; monsters face the viewer
- [ ] Four frames maximum
- [ ] Projectile strips contain **only** the projectile; caster strips contain
      **only** the caster
- [ ] Effect strips (defeat puff, book burst) painted **neutral** for tinting
- [ ] Filed under `~/Downloads/the-vidadiyot/anim/`

A sheet that misses these is still usable — it costs a retune in the extractor,
and a registration miss costs a hand-nudge per frame.

---

## What lands on the code side when these arrive

Worth knowing that the art is the larger half but not the only half.

**✅ Done 2026-08-20 — the animation *system*, ahead of the art.** The state
machine that was only on `Player` now lives on `Entity` and both the player and
the monsters use it: `set_frames(idle=…, walk=…)`, an overridable `anim_state`,
and `frame_for(state, clock)`. The teachers animate today off the WALK pose that
came on their own §R8/§R9 sheets — no Phase 2 art involved.

- ⚠️ **A missing pose degrades, it does not crash.** `assets.load` returns None
  for a file that was never generated and `set_frames` drops it, so a monster
  with no extra art keeps one sprite and never changes stance — exactly what
  every monster did before. That property is what lets these sheets land one at
  a time instead of all at once.
- ⚠️ **The squash is pre-built at install, not per frame.** Doing it in `draw`
  is a `smoothscale` per entity per frame, resampling a 54px sprite on a 640x360
  surface that is then integer-scaled — the same mistake the victory banner made.
- ⚠️ **The ATTACK pose is extracted but unusable.** Both teacher sheets drew it
  about a quarter smaller than the other three poses despite §R8 asking for one
  common ground line, so cutting it at the sheet's own scale makes the teacher
  visibly *shrink* every time it casts. It needs a re-roll or a per-pose scale
  correction in `extract_teacher.py` before an "attack" state can be wired.

**Still to do when the strips arrive:**

- **`set_frames` takes one Surface per state** and fakes the walk from it. Real
  4-frame strips need a frame-*list* animator, and `spritelib` needs to slice a
  strip into frames on an even grid.
- **Casting frames need hooking to the existing cast timer** so the wind-up
  lines up with the shot, which is the entire point of sheet 5.
- **Projectiles and effects draw with primitives**, so each one becomes a sprite
  swap plus a frame clock.
- **`Blinker`'s appear/vanish is an alpha ramp** over the retuned 1.30s telegraph;
  sheet 8 replaces the ramp with real frames.

None of it is large, but it is the difference between the sheets sitting in
`~/Downloads` and the game moving.
