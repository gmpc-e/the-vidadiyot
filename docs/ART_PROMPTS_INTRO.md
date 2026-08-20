# Prompt pack — the intro

The seven painted plates and one run cycle that `INTRO_SCRIPT.md` needs. Read
the script first: several prompts here exist to satisfy a specific line of
dialogue, and painting them "better" in a way that breaks the line is worse than
painting them plainly.

> ⚠️ **This file is parsed, not just read.** `tools/art_request.py --phase 3`
> takes each `## §N Title` heading as a section id and **the blockquote under it
> as the prompt**. Prose outside the quote — like this paragraph — is notes to
> us and is never sent. A prompt written as a plain paragraph is silently *not
> requested*. One runnable request per §.

```bash
./venv/bin/python tools/art_request.py --phase 3 --list
./venv/bin/python tools/art_request.py --phase 3 I1 --dry-run
./venv/bin/python tools/art_request.py --phase 3 I1 --out intro/forest.png
```

**§0 rides on every request and so does §I0.** The tool prepends both. §0 keeps
this pack looking like the game; §I0 is the delivery format that makes a plate
usable by the camera.

---

## ⚠️ This pack breaks the pipeline's oldest rule, on purpose

Every other sheet this project has ever asked for arrives as **objects isolated
on flat black**. Most of this pack is the exact opposite: **full-bleed painted
scenes**, edge to edge, with no black anywhere.

That is not sloppiness, it is what a cutscene plate *is* — and it means the
acceptance gates need saying out loud:

| Section | What it is | Gate | Chosen how |
|---|---|---|---|
| §I1 §I2 §I4 §I7 | full-bleed scene | scene | declared in `SCENE_SECTIONS` |
| §I5 §I6 §I8 §I3B | objects on black | the default object gate | — |
| §I3 | a four-frame run cycle | strip | declared in `STRIP_SECTIONS` |

All three are picked automatically from the section id, so the normal run needs
no flag. `--scene`, `--strip` and `--material` exist for re-checking a file by
hand (`--check FILE`).

⚠️ **A plate must not be judged by the object gate**, and the reason is not the
one you would guess. The obvious failure is loud — "only 8% of the sheet is
near-black" — but the quiet one is worse: **a night plate painted dark enough
passes it**, and nothing then says the wrong gate ran. That is exactly why the
sections are a declared list rather than "whatever the default rejects".

⚠️ **`--material` is not the answer either.** That gate measures whether the
image is *one uniform material*; a painted scene has a focal point by
definition, so it fails on composition — the thing a plate is supposed to have.

The scene gate checks the two things a plate can actually get wrong: **that the
painting reaches all four edges** (a letterboxed picture puts a black bar into
shot the moment the camera moves) and **that no text is painted into it**.

---

## §0 Style block — paste this first, every time

> **Style:** Hand-painted 2D game art for a horror-lite cartoon game set in an
> abandoned school at night. Painterly illustration with clean dark outlines and
> chunky, readable shapes — the register of Luigi's Mansion or Costume Quest,
> not photoreal and not survival horror. Slightly grimy, dusty, decayed, but
> never gory and never frightening; the audience is children.
>
> **Palette:** desaturated cool greys, muted browns and deep blue-blacks for all
> environment surfaces. Accent language, used sparingly: brass and warm gold for
> metal, blood red and toxic slime green for damage and decay, deep purple for
> cloth. The environment is dark and low-contrast. Any single warm light in a
> scene is the brightest thing in it, and there is never more than one.
>
> **Lighting:** cold moonlight from above, flat and even. No lens flare, no god
> rays, no glow bloom, no coloured rim light.
>
> **Presentation:** **No text of any kind. No captions, no titles, no speech
> bubbles, no signage with readable letters, no watermarks, no borders, no
> panel frames, no UI.** Output at 1536×1024.

Two of those clauses exist because of specific accidents: a sheet once arrived
as a full UI mock-up with buttons, and painted pose labels on another were
mistaken for the character by the cutout tool. The "no signage" clause is new
and is for this pack — a model asked for a school gate will paint a school name
on it, and a readable word in a plate is a caption the gate will catch.

---

## §I0 Plate delivery format — paste this with every intro sheet

> **This is a wide cinematic plate for a game cutscene, not an object study.**
> Paint the scene edge to edge, filling the entire frame. No black background,
> no border, no vignette frame, no letterbox bars — the painting reaches all
> four corners.
>
> **Composition and safe area.** The frame is 1536×1024, but only a 16:9 band
> across the middle is ever shown: everything that matters must sit inside the
> central 1370×770 region, and the outer margin exists purely as bleed for a
> slow camera move. Nothing important — no face, no key object, no horizon
> detail — in the outer 80 pixels on any side.
>
> **Depth in three layers**, because the camera pushes slowly into this image: a
> dark foreground framing element low in the frame, a clearly lit middle ground
> holding the subject, and a dim far background. Avoid a single flat wall of
> detail.
>
> **Leave the middle of the lower third quiet** — dim, uncluttered, low
> contrast. Subtitles and a character portrait are drawn over it in the game,
> and a busy area there makes the words unreadable.
>
> **No characters, no people, no creatures anywhere in the painting** unless
> this specific sheet asks for one. The cast is composited in from the game's
> own sprites, and a painted figure would be a second, differently-drawn version
> of a character the player already knows.

⚠️ The "no characters" clause is the one that will be violated. A model asked
for a moonlit path to an abandoned school wants to put a child on it. Every
plate in beats 1–4 has the warriors walking across it *as sprites*, and a
painted kid in the plate is a second Roni standing next to the real one.

⚠️ **The cast is composited at double game scale, and the plate has to leave room
for that.** Proven on the first delivered plate (2026-08-21): the game's walk
cycles are 48px tall, and 48px against a 360px frame is 13% of the screen — on a
plate whose foreground trees fill the height, the heroes read as insects. Intro
poses are cut at **~96px** from the same source paintings (see
`INTRO_SCRIPT.md`), so **the walkable foreground band across the bottom third
must stay clear for figures about a quarter of the frame's height**. Do not fill
it with logs, boulders or ferns.

⚠️ **It is judged at 640×360, not at 1536×1024.** The first roll came back
photoreal, and its leaf litter, twigs and bark detail turned to grey noise the
moment it was scaled down — detail finer than about six source pixels does not
survive. Build the plate from a few big readable shapes with the texture living
inside them, the same rule §0 applies to characters.

⚠️ The safe-area numbers are not decorative. 1536×1024 is 3:2 and the game
renders 16:9, so the top and bottom **are** cropped: 1536×864 is the whole of
what can ever be seen, and the push-in eats a further 11%. Content painted in
the corners is content painted for nobody.

---

## §I1 The woods behind the school

Beat 1. Sixteen seconds, and for the first six of them this is all there is —
so it has to be worth looking at without anything happening in it.

> Paint a wide night-time view of a narrow dirt path winding through a dense
> forest, seen from a low three-quarter angle slightly behind and above the
> path, as though following someone along it.
>
> The path runs from the bottom-left of the frame toward a gap in the trees in
> the upper right, where the woods thin out and a faint cold glow suggests a
> clearing beyond. Bare, crooked trees crowd both sides with their branches
> interlocking overhead; thick undergrowth, ferns, fallen leaves and a rotting
> log in the dark foreground. A low ground mist lies in the hollows, knee deep,
> catching the moonlight.
>
> Cold blue-grey moonlight from above filters through the branches in soft
> patches on the path. The scene is dark and desaturated — deep blue-blacks,
> cold greys, dead brown leaves — with no warm colour anywhere in the frame.
>
> Quiet and lonely rather than threatening: nothing is hiding in this forest and
> nothing menacing is visible. The path is clear and walkable along its whole
> length, empty, with the ground beside it left dim and simple.
>
> Painted illustration with visible brush shapes and clean chunky forms — a
> hand-painted animation background, not a photograph and not a 3D render. No
> photoreal bark detail, no fine twig networks, no depth-of-field blur, no
> lens effects. Keep the nearest strip along the bottom of the frame open and
> uncluttered: characters walk across it.

---

## §I2 The school, from the gate

Beat 2, held through beats 3 and 4, returned to in beat 8 — **the plate the
intro spends 48 of its 120 seconds on.** It carries the most weight of anything
in this pack.

⚠️ **The single lit window is a script dependency.** Roni's line is "Then who
left a light on?". One window, warm, and nothing else in the frame lit.

> Paint a wide night-time view of an abandoned two-storey school building seen
> from the overgrown yard in front of it, from ground level, looking slightly
> up at the facade.
>
> An old iron gate stands open and crooked in the middle distance, one hinge
> broken, and a cracked path leads from it to the school's dark main doorway. The
> building is grim institutional brick and concrete: rows of tall dark windows,
> several broken or boarded, a sagging gutter, weeds pushing through the
> paving, a dead tree to one side, a rusted bicycle rack. Long grass, scattered
> leaves and litter in the yard.
>
> **Exactly one window on the upper floor is lit from inside with a dim,
> sickly warm yellow glow.** It is the only warm colour in the entire painting
> and the only lit window — every other window is dark. Do not light the
> doorway, the path, the gate or any other window.
>
> Everything else is cold moonlight and deep blue-grey shadow, dark and
> low-contrast. The yard in the lower middle of the frame is left open, dim and
> uncluttered. Empty — no people, no animals, no creatures.

---

## §I3 The messenger — run cycle (4 frames)

Beat 4. She runs across the plate, so she is a **game sprite**, not a painting —
same size, same style, same three-heads-tall chibi proportions as the monsters,
because she stands next to them in the player's memory.

⚠️ **The frame count lives in the heading, not in a table here.** `art_request.py`
reads "(4 frames" out of it and fails the sheet if four frames did not come back
with their feet on one line — the first strip this project ever received came
back with three and passed every other check.

> A four-frame side-view run cycle of a single character, drawn as four separate
> poses in one horizontal row on a pure black background, with a wide black gap
> between each pose and nothing touching.
>
> The character is a small girl of about eight, drawn chibi — roughly three
> heads tall, with a large round head, big frightened eyes, a short stubby body
> and simplified oversized hands and feet. Dark hair loose and flying back from
> running, a plain dark-red dress torn at the hem, bare knees, scuffed shoes.
> She is dusty and dishevelled, as though she has been hiding somewhere dirty,
> but not injured and not bloodied. She is frightened and running hard, arms
> pumping, looking back over nothing.
>
> She faces to the right and runs to the right in all four frames. The four
> poses are: contact with the right foot forward, passing with the left leg
> lifted under the body, contact with the left foot forward, passing with the
> right leg lifted.
>
> Registration is critical: draw all four at exactly the same size, with the
> feet touching one common horizontal ground line across the whole row, and the
> head at the same height in every frame. Keep her bright and saturated against
> the black — she must stay legible when shrunk very small.
>
> Flat even lighting, no shadow under the feet, no motion blur, no speed lines,
> no ground, no scenery, no text.

---

## §I3B The messenger — portrait bust

Her face carries twelve of the sixteen dialogue cards. Requested separately from
the run cycle **because a bust and a run cycle want different framing**, and a
sheet asked for both gives you a small version of each.

⚠️ Object gate (the default). Keep it on black.

> Paint a single character portrait bust — head, shoulders and upper chest only
> — of a small frightened girl of about eight, isolated on a pure black
> background with nothing else in the frame.
>
> She is drawn chibi, matching a three-heads-tall game character: large round
> head, very large dark eyes, small nose and mouth. Dark hair, loose and messy,
> falling over one eye. A plain dark-red dress, dusty and torn at the collar.
> A smudge of dirt on one cheek. Her expression is urgent and pleading — wide
> eyes, brows raised in the middle, mouth open mid-word — frightened but brave,
> not crying and not screaming.
>
> She faces slightly to the right of the viewer, as though speaking to someone
> just off-frame. Bright and saturated so she reads against a dark background.
> Flat even lighting, clean dark outlines, no glow, no scene, no shadow, no
> border, no text.

---

## §I4 Queen Maya, taken

Beat 5. Sixteen seconds of a girl who never moves and never speaks, so the
painting has to do all of it. **She is not being hurt** — the register is a
storybook princess in a tower, not a hostage.

> Paint a dark interior scene: a small, high-ceilinged room deep inside an
> abandoned school, seen from the far side of the room.
>
> In the middle distance, a young girl in a simple crown and a long deep-purple
> dress sits on the floor with her back against a stack of old wooden crates and
> broken school furniture, her knees drawn up, perfectly still, head lowered.
> She is unharmed, not bound, not caged and not distressed — she looks asleep,
> or enchanted. She is small in the frame, seen at a distance.
>
> A single shaft of pale cold moonlight from a high barred window falls on her,
> and everything outside that shaft falls away into deep blue-black shadow.
> Dust hangs in the light. Around her in the dark: stacked chairs, a toppled
> blackboard, rolled maps, a wall clock lying face down on the floor with its
> glass cracked.
>
> She and her crown are the only saturated colour in the painting — deep purple
> and a dull gold — and everything else is desaturated grey-blue. Still, sad and
> quiet rather than frightening. No other figures, no monsters, no text.

---

## §I5 TikTak

Beat 6, four seconds, no dialogue and no movement. He needs to be readable in a
single glance and then remembered for the rest of the campaign.

**He is a clock.** His name is the sound a clock makes, the duel track (§M5) is
already built on a ticking rhythm, and `props/clock.png` is already "stopped at a
sinister hour". Painted on black so this sheet also becomes his bestiary
portrait and, eventually, his menu art — one request, three uses.

> Paint a single full-body character, standing and facing the viewer, isolated
> on a pure black background with nothing else in the frame.
>
> He is a tall, thin, stooping figure in a long moth-eaten schoolmaster's coat
> of faded black wool, far too long in the sleeve, worn over a high stiff collar.
> His hands are bare, pale and much too large, with long thin fingers. He is
> gaunt and angular, all elbows and knees, and he leans forward slightly as
> though about to take a step.
>
> **In place of a head he has an old round school wall clock** — a battered
> brass-rimmed clock face with a cracked glass, yellowed white dial and plain
> black numerals, mounted on his neck and tipped very slightly to one side. Its
> two hands are stopped at an odd, wrong hour and are the only sharp black
> shapes on the face. He has no eyes and no mouth: the dial is the whole face,
> and it is somehow still watching. In one hand he holds a long, thin brass
> clock hand, taller than a person, like a walking cane or a spear.
>
> Sinister but comic rather than gory — a storybook villain a child would find
> creepy and want to draw, not something horrifying. No blood, no wounds, no
> teeth. Bright enough against the black to stay readable when shrunk small:
> the dial pale, the coat deep near-black with visible fabric texture, the brass
> warm.
>
> Standing straight on, whole body visible, feet included, one clean silhouette.
> Flat even lighting, no shadow beneath him, no scene, no ground, no glow, no
> text.

---

## §I6 The three friends, changing

Beat 6's payoff and the emotional centre of the whole intro: three children
becoming the three monsters the player is about to fight.

⚠️ **Left to right must be Snir, Tirosh, Emri** — the order the girl names them,
each landing on a clock tick, each with the real game sprite fading in over it.
Getting the order wrong desynchronises the one moment in the intro that actually
teaches something.

> Paint three separate full-body silhouette figures in one horizontal row on a
> pure black background, with a wide black gap between each and nothing
> touching. All three are the same height, standing on one common ground line,
> centred at the same height in the frame.
>
> Each is a child of about eight, mid-transformation into a small monster, drawn
> chibi at roughly three heads tall — large round head, short stubby body,
> oversized hands and feet. The transformation is caught halfway: the child's
> shape is still clearly there, dissolving upward from the feet into a rough,
> shaggy, monstrous outline, with a faint sickly glow bleeding through the
> cracks between the two forms.
>
> Left figure: a boy whose wild curly hair is lengthening into thick sticky
> strands that hang past his knees, sickly pale green light in the cracks.
> Centre figure: a girl whose raised hands are breaking apart into flickering
> chaotic purple sparks, deep violet light in the cracks.
> Right figure: a boy whose edges are thinning and going transparent, half of
> him already faded into the dark, cold blue-white light in the cracks.
>
> Faces are dark and featureless — no eyes, no mouths, no expressions. They read
> as shadows of children lit from within, not as portraits.
>
> Sad rather than horrifying: this is something being done *to* them. No blood,
> no gore, no screaming. Flat even lighting, no cast shadows, no ground, no
> scene, no text.

---

## §I7 Every book in the school

Beat 7 — the objective, in one picture. This is a wide plate; the movement in it
is the books, and the camera barely moves.

> Paint a wide interior view of a school library at night, seen straight down a
> long aisle between tall wooden shelves that recede toward a dark doorway at
> the far end.
>
> **The shelves are empty** — bare boards, dust outlines where books stood, a
> few knocked-over bookends, one or two lonely volumes left leaning. From the
> shelves on both sides a stream of old hardback books flies through the air
> down the aisle, away from the viewer, toward the dark doorway: dozens of
> books, in a long curving ribbon, pages fanned open and fluttering, loose pages
> torn free and drifting behind them. The stream is thickest in the middle
> distance and vanishes into the black doorway.
>
> Cold moonlight comes from high windows on the left, striping the floor. The
> books catch that light along their edges and are the brightest thing in the
> frame — worn leather browns, faded reds and dull golds against a desaturated
> grey-blue room.
>
> Strange and sad rather than violent — nothing is being destroyed, everything
> is being *taken*. No people, no creatures, no hands, no text, and no readable
> writing on any book cover or spine.

---

## §I8 The stopped clock — transition motif

The intro's wipe. A plain crossfade between the girl's face and TikTak's throws
away a free chance to say who is doing this, and the same asset later serves as
the boss's arrival sting.

⚠️ Object gate. **One shape on black, absolutely centred**, because it is
rotated in code around its own centre — an off-centre clock face wobbles.

> Paint a single old round school wall clock face, seen straight on and dead
> centre, isolated on a pure black background with nothing else in the frame.
>
> A battered brass rim, badly tarnished; a yellowed off-white dial with plain
> black numerals; the glass cracked across one corner. **Draw the dial with no
> hands on it at all** — the face is bare. Dusty and dead, long stopped.
>
> Beneath and separate from the clock, draw the two hands as two isolated
> objects lying apart from each other on the black: one long thin black minute
> hand and one shorter hour hand, each seen flat and straight on, each pointing
> straight up, each drawn as one clean shape.
>
> Flat even lighting, no shadow, no glow, no reflection, no scene, no text.

The hands come separately so they can be rotated independently. The wipe is the
minute hand sweeping once around the dial, and the sweep is what carries the
scene change.

---

## Where the files go, and what happens next

Deliver into **`~/Downloads/the-vidadiyot/intro/`**. `spritelib.source(name)`
resolves by filename across that whole tree, so the folder is a convenience, not
a contract.

| § | filename | becomes |
|---|---|---|
| I1 | `intro_forest.png` | `assets/ui/intro_forest.png` |
| I2 | `intro_school.png` | `assets/ui/intro_school.png` |
| I3 | `intro_girl_run.png` | `assets/sprites/girl_run_{0..3}.png` |
| I3B | `intro_girl_portrait.png` | `assets/sprites/girl_portrait.png` |
| I4 | `intro_maya.png` | `assets/ui/intro_maya.png` |
| I5 | `intro_tiktak.png` | `assets/sprites/tiktak.png` |
| I6 | `intro_transform.png` | `assets/ui/intro_transform.png` |
| I7 | `intro_books.png` | `assets/ui/intro_books.png` |
| I8 | `intro_clock.png` | `assets/ui/intro_clock{,_min,_hour}.png` |

⚠️ **The plates key with `MODE_RAMP`, not `MODE_FILL`.** `MODE_FILL` floods
inward from the border treating dark pixels as background — on a full-bleed
night scene that eats the painting from the edges in. The character sheets
(§I3, §I3B, §I5, §I6, §I8) are on black and use `MODE_FILL` as usual.

## Before you send a sheet back

- [ ] 1536×1024, and everything that matters inside the central 1370×770
- [ ] **No text anywhere** — no signage, no book spines, no numbers except a
      clock dial's
- [ ] Plates: paint to all four corners, no black bars, no vignette frame
- [ ] Plates: **no painted characters**, except §I4's Maya
- [ ] Character sheets: pure `#000000`, nothing touching, generous gutters
- [ ] §I3: four frames, one ground line, one size
- [ ] §I6: Snir, Tirosh, Emri — left to right, in that order
- [ ] It passed its gate: `art_request.py --phase 3 <section> --out …` runs the
      right one automatically and prints the verdict
