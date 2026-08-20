# Roadmap — The Vidadiyot

Living doc for planned work. Spirit: **fun sandbox** — pick what's fun, no
obligation to finish everything.

**Where it lives:** `~/github/the-vidadiyot` → https://github.com/gmpc-e/the-vidadiyot
(`main`). The user pushes with **GitHub Desktop** and plans to branch later, so
leave committing to them unless asked. `venv/ build/ dist/ .idea/` are
gitignored — ~1.5MB of source against ~117MB of ignored build output.

**Current state:** a playable level with a painted title screen and warrior
select; two playable warriors (Wallad — longsword; Roni — thrown knives + Zina);
five ranged monsters live — the two **teachers** (tome) hold the classrooms while
Little Snir (web) and Little Terror (fire) work the corridors — with Emri built
but parked for the boss level; classrooms furnished with **solid** desks;
potions, timer, level-complete sequence, victory + leaderboard, defeat;
difficulty scales monster damage.

**Clearing the level is no longer the end of the run** — it opens the **duel with
Emri** (§9), and the clock carries through it.

**The loop, and it is now entirely made of fighting:** kill anything → it hands
over a **key** (first three kills) → unlock a colour-coded door → kill the
**teacher** inside → pick up the **shining** book it drops → put it in that
room's **locker**, which only opens once the room is clear. ⚠️ Neither keys nor
books are placed on the map any more. Both used to be errands you ran before the
game started; every objective is now produced by the fight that gates it.

Seventeen sound effects are real plus **voice packs for both teachers**; six
effects are wired but silent; **all five music tracks are in**. 478 headless
tests.

**✅ The classroom furniture is solid (2026-08-20)** — desks, the teacher's desk
and the bookshelf stop a body, so a room is somewhere to move around rather than
a flat floor with pictures on it. ⚠️ **The spacing is what makes that survivable**
and it is the thing to be careful with: the grid went from 4 columns at 58px to 3
at 86px, because 58px spacing leaves a 38px aisle between two 19px desks and the
monster that lives in the room is 44px wide. `decor.LANE_MIN` names the number,
and a test walks a 44px agent from the doorway to the return locker in every
classroom. ⚠️ Doorways are kept clear explicitly — the scenery locker bank runs
along the same wall the classroom door is in, so before this it was painted
straight across the doorway and made solid it would have sealed the room.

**✅ The corridors are no longer empty (2026-08-20)** — `world/ambience.py`
places flickering ceiling tubes, dripping pipes and cobwebs in *every* room,
including the corridor and entrance that `decor.py` has never furnished. It is a
separate system from `decor` for two reasons: it moves, so it cannot be baked
into the room's one blitted Surface; and it is placed from a bare room rect, so
it does not care what kind of room it is.
- ⚠️ **Each instance needs its own phase.** Without one every lamp in the level
  stutters on the same frame and it reads as the *screen* glitching rather than
  as several tired fittings.
- ⚠️ **A flicker is not a cycle.** Playing 0-1-2-3 evenly reads as a disco light;
  `LAMP_PATTERN` sits lit for seconds, stutters briefly, and rarely flares.
- ⚠️ Everything hangs against the **top wall**, because ambience draws under the
  actors and that is the one strip of a room with no walkable floor to be wrong
  about.

**Still holding the look back:** the corridor has *ambience* now — flickering
tubes, cobwebs, a dripping pipe — but no **furniture**. Its painted props (locker
bank, notice board, trophy case, radiator) are extracted and still sitting
unused, because `decor.py` furnishes classrooms and nothing else. Ambience proved
the placement idea works from a bare room rect; furniture is the harder half,
since it is solid and has to leave a lane. See §1.

## 0. ✅ Playtest pass — 2026-08-20 (twenty fixes)

A single session's list, kept together because the items argue with each other
and the reasoning is only legible as a set.

**Difficulty was one dial and is now three.** It scaled *incoming damage* only,
so a monster died in the same number of swings on Easy as on Hard and the level
was the same length either way — which is why Normal felt too easy. `hp` (0.85 /
1.20 / 1.45) and `regen` (1.4 / 1.0 / 0.6) join `dps`.
- ⚠️ **Health regeneration was doing most of the work of an easy mode by itself.**
  At 3.0/sec a full bar came back in 33s, so a fight cost nothing once it ended.
  1.4/sec, and a 4s delay before it starts.
- ⚠️ **One potion in the level**, down from three. With regen on top, health was
  never really a resource.

**⚠️ A tuning request can break a documented relationship, and the suite is what
notices.** Cutting Roni's knife 20% (0.85 → 0.68) as asked pushed melee to
**2.3x** the thrower, past the "under 2x" rule that stops the thrower being a
trap choice. Fixed by slowing Wallad's swing (0.36 → 0.42) rather than undoing
the cut or trimming his damage — his identity is "two pips a swing", and the
cooldown is the dial that does not touch it.

**Keys are killed for.** The first three kills hand one over
(`KEYS_FROM_KILLS`), straight into the inventory rather than onto the floor —
a pickup dropped mid-fight is one more thing to chase while being shot at.
⚠️ It still emits `ITEM_COLLECTED`, because that is what the quest counts; award
it silently and the HUD's key counter never moves.

**The web bites.** It used to hold you still and do nothing, so the right play
was to ignore it and mash. It drains `WEB_DPS` while it holds you, through a new
`Player.drain()` — `take_damage` flinches and asks for a grunt, which is right
for a blow and wrong sixty times a second.

**Monsters are solid to the player** (`PlayState._WithMonsters`).
- ⚠️ Only the *player* uses that collider. Feeding monsters each other's hitboxes
  makes a monster collide with itself and jams the roster the moment two meet.
- ⚠️ A monster already overlapping the player is excluded. Monsters do not
  collide with the player when *they* move, so one can walk into you — if that
  overlap were solid you would be sealed inside it with no axis to escape on.

**Projectiles clear the furniture** (`PlayState.wall_rects`). `solid_rects` grew
to include desks so a body would bump into them, and that quietly meant a thrown
book died against the nearest chair — the teachers hold rooms full of furniture,
so they were mostly shooting their own classroom.

**Enter works where the screen says it does.** Every end screen printed
"Enter: play again" and only Space worked. A new `confirm` edge intent — kept out
of `attack` on purpose, or Enter would swing the sword.

**Both end screens own the whole frame now**, and both needed their panel
resized for the art behind it. ⚠️ The victory screen needs **two** panel rects:
name entry holds four lines and must sit low so the banner reads, while the board
needs height and cannot. One rect could not serve both, and the row that
overflowed onto the "play again" line is what proved it.

**Wallad, not Elad** — everywhere. ⚠️ The rename broke the select screen, because
the menu loaded `f"{warrior['id']}_menu.png"` and so the character's id was
quietly part of an asset path. Named explicitly now.

Also: the teachers hit for 19 (was 14), the sword's swing effect is a glint at
the blade's tip instead of three stacked arcs 48px across, `monster_die` is the
v2 take, and the painted `YOU LOST!!` scene replaces the drawn banner.

---

Status legend: ⬜ not started · 🔶 in progress · ✅ done · 🌟 stretch goal

Rough order: **§1–§2 make it feel good, §3–§4 make it bigger, §5 tightens the
core loop.** §10 (multiplayer) is a *stretch goal* — not until the game is crisp
and there's more of it. Plenty to do first.

**✅ Phase 1 tiles are finished (2026-08-20).** The three §R1–R3 re-paints
generated through `art_request.py` are extracted and in the map: a tileable
cinderblock wall with no dado rail, a wooden doorway threshold (it was standing
in as flagstone), and three herringbone floor variants that finally match the
parquet they scatter through.
- ⚠️ **A silently-failed patch cost a round trip here.** The `SLABS` edit did not
  match, so none of the v2 art was actually in — and the preview *looked* better
  anyway because a separate change had removed the decal stamping. Two changes,
  one visible improvement, wrong cause. Verify the file, not the picture.
- ⚠️ **Window size sets material scale.** A 380px window on ~64px planks put six
  planks in a 32px tile and the wood read as masonry; 200px reads as a floor.
- ⚠️ Painted swatches do not arrive at matching brightness. The cracked variant
  came in at mean luma 56 against the floor's 38, which sprinkles as pale
  patches rather than wear; `TONE` brings it to 38.7.

**Next up, in order:**

1. **§S8 Emri's character sheet** — six rows: three walks, materialise, strike,
   hurt. The boss is the worst-animated thing in the game (one sprite faded in
   and out) and it is the only fight with phases. The prompt is written.
2. **§S11 the teachers.** Their attack pose is extracted and **unusable** — both
   §R8/§R9 sheets drew it a quarter smaller than its siblings — so the enemy the
   player meets most attacks without moving at all.
3. **A back-facing walk for Little Snir** (Little Terror already has one). She
   cannot turn away from the camera without it, and a back view cannot be
   mirrored out of a front one.
4. **The six missing sound effects** (§1c) — `tome_hit` first. All five music
   tracks are in. Every prompt is ready in `docs/AUDIO_BOOK.md`.
5. **Corridor furniture.** Ambience landed there but the painted props (locker
   bank, notice board, trophy case, radiator) are still extracted and unused.
6. **The intro (§11)** — script, art book and audio book are written and the
   tools are wired. The next move is *not* art: name the girl, then generate the
   cue (§X1) and retime the beat sheet to what Suno actually delivers, because
   the picture is timed to the music and never the other way round.

⚠️ Two entries sat in this list stale after the fact — the Phase 1 tile re-dos,
and "Phase 2 animation strips" after the warriors were finished. Re-read this
block whenever a numbered item is finished; it is the part of the roadmap that
rots fastest and the part most likely to be trusted.

**Level 1 pacing (2026-08-19):** a run was finishing in ~60s. Three books now
instead of two, **every** book behind a fight (6 monsters, up from 5 with one
book free — and since 2026-08-20 the books are *carried* rather than guarded),
Snir and Terror +15% HP, Roni's knife -15% damage. Required fighting time roughly
doubled — but note most of a run is *walking*, so the third book is what actually
lengthens it; the HP bump adds only a second or two of combat. Expect ~90s, not
~120s.

**Done so far:** §6 (book-return payoff), §6b (level-complete sequence), the
painted title screen, **warrior select** (§8) with Wallad and Roni and their two
weapons, and **Emri** built but parked for §9's boss level. §5 (lockers) is
still the natural next step; it gives §6's burst a real place to happen.

---

## 1a. 🔶 Animation — the system is in, the strips are not

**✅ The animator moved to `Entity` (2026-08-20)** and the monsters use it. It
was only on `Player`: four painted poses, a state machine (hurt > attack > walk
> idle) and a synthesized gait — a two-step bob with a squash on the off-beat,
because the sheets give one frame per state and not a cycle.

- `set_frames(idle=…, walk=…)`, an overridable `anim_state`, and
  `frame_for(state, clock)` now live on `Entity`. `Monster.anim_state` is
  velocity-driven and `WALK_HZ` drops from 7 to 4 — the teachers shuffle.
- **The teachers animate today off art that already existed** — the WALK pose on
  their own §R8/§R9 sheets, which had been extracted and left unused. No Phase 2
  art was involved.
- ⚠️ **A missing pose degrades, it does not crash.** `assets.load` returns None
  for art that was never generated and `set_frames` drops it, so a monster with
  no extra pose keeps one sprite and never changes stance — exactly what every
  monster did before. This is what lets the Phase 2 strips land one sheet at a
  time instead of all at once.
- ⚠️ **The ATTACK pose is extracted and unusable.** Both teacher sheets drew it
  about a quarter smaller than the other three, so wiring an "attack" state makes
  the teacher visibly shrink every time it casts. See §R8's note.
**✅ The strip pipeline is built and one sheet is through it (2026-08-20).**
`set_frames` takes a Surface *or a list*; `spritelib.slice_strip` cuts a
delivered strip; `art_request` gates registration; `tools/extract_phase2.py`
writes the frames. Wallad's walk cycle is painted, sliced and playing in game.

Seven rolls bought that, and every one of them taught something the pack now
carries:
- ⚠️ **Ask for three frames, not four.** Told "four", the model delivered 3, 4,
  3, 3 — and the one time it drew four it packed them so tightly two touched and
  could not be cut apart. Three arrives reliably and well-registered.
  `Entity.PINGPONG` plays a three-frame walk **0-1-2-1**, which is a four-beat
  cycle out of three drawings and a standard walk anyway. A one-shot must not
  bounce or it plays its wind-up backwards after the strike.
- ⚠️ **Frames touching is the common failure, not frames drifting.** Registration
  came back excellent (0.2–0.6% baseline spread) almost every time; what kept
  failing was the count, because neighbouring frames overlapped. §A now asks for
  a black gap "at least half as wide as the subject" and a margin round the
  image. The expected count is read from the section heading — "(3 frames)" — so
  the doc stays the single source of truth.
- ⚠️ **§0's "every character is chibi" was my error and it cost two rolls.** That
  rule came from the *monsters*; applied to the whole cast it produced a chibi
  Wallad, a fine drawing of a different character than the one in `knight_idle`.
  §0 is now per-character: monsters ~3 heads, Roni ~4, Wallad a realistic adult.
- ⚠️ **The pack described characters the game does not have.** §S2 asked for "a
  girl in a hooded travelling cloak" and got exactly that — but Roni is a warrior
  princess in a gold crown, purple cloak and white skirt. The sheet prompts
  predate the final warrior art. All four Priority-1 prompts have been rewritten
  **from the sprites**, and the pack now says to check them against
  `assets/sprites/<name>_idle.png` before editing.
- ⚠️ **§A said "everything faces screen-right" and the warriors are painted
  front-on.** A side-facing walk under a front-facing idle turns the character
  90° the instant it moves. **Decided 2026-08-20: keep front-facing** and re-shoot
  the strips, rather than re-shooting all eight warrior poses side-on and
  discarding painted art that already works. §A now asks for a three-quarter
  front view, which also mirrors correctly for leftward movement.
- ⚠️ **A held weapon bridging the gutter is the single commonest failure.** A
  sword held out sideways reaches into the next frame, the two join, and the
  sheet is cut as one item. §A now asks for blades angled down beside the leg or
  upright against the shoulder, and for nothing to be wider than the character's
  own shoulders. This is what finally got §S1 through.
- ⚠️ **The model resists non-chibi proportions.** §0 now specifies Wallad's head as
  "one sixth of his total height — measure it", and the delivery still came back
  nearer a quarter. At 48px it reads as the same character family as
  `knight_idle` but visibly stockier. Accepted; worth knowing that proportion
  instructions are the weakest lever in the pack.
**✅ The manual round-trip beats the API for character sheets (2026-08-20).**
`elad-knight-sheet-v2.png`, made by hand in ChatGPT, registered at **0–1px**
baseline spread where nine API rolls managed 4px at best, and carried the right
character first time. Wallad's walk and attack are cut from it and playing.
- ⚠️ **Ask for one sheet per character, one animation per row.** The pack asked
  for one strip per image and that was wrong: separate requests drift in scale
  and style against each other, and then the character changes size when it stops
  walking. A grid fixes it by construction. `spritelib.strip_rows` picks a band
  out of a sheet and `extract_phase2.STRIPS` names which rows to take.
- ⚠️ **Frames must keep their position within their own cell, not be re-centred
  on their content.** A swing frame is much wider than a standing one because the
  blade sticks out; centring each trimmed frame put Wallad's *body* somewhere
  different every frame, so he slid sideways as he swung.
- ⚠️ **Never ask for a pose the game has no mechanic for.** Both delivered
  sheets carried a lightning-sword attack; Wallad's `power` is `None`. Worse, the
  beam crossed between frames and welded them into one uncuttable blob — an
  effect that leaves the character's outline breaks the sheet as well as wasting
  a third of it.
- ⬜ **The walk is too subtle at 48px.** It registers perfectly and reads as a
  shuffle: from the front the legs are foreshortened, so the body bob carries the
  movement and this one barely bobs. §A now asks for an exaggerated knee lift and
  bounce.
**✅ Directional facing (2026-08-20).** Wallad turns to face where he walks —
toward the camera, away from it, or in profile. `Player.facing_dir` picks the
view from the dominant axis of movement and `anim_state` returns
`walk_down`/`walk_up`/`walk_side`.
- ⚠️ **A back view cannot be mirrored out of a front view.** `Player.facing` was
  ±1 and `draw` flipped the sprite, so left/right was already handled — it just
  looked wrong, because the art was near square-on front (mirroring it changes
  almost nothing) and up/down had no art at all. The only fix was painting a back.
- ⚠️ **The art was already on disk.** `elad-knight-sheet-v3.png` was judged
  "better sheet, worse fit" and set aside — a verdict made before facing came up.
  It carries front, back and side walks, and re-cutting it cost no new art at all.
  ⚠️ Its rows are drawn at different sizes (side ~234px, front ~193px, back
  ~176px); normalising each row to the same 48px output is what keeps Wallad one
  height whichever way he walks.
- ⚠️ **Only the side view mirrors.** Flipping a front or back view swaps the
  sword into the wrong hand and the shield with it, for nothing.
- The rows are **optional**: a warrior with no directional art keeps its single
  `walk` and behaves exactly as before, so Roni is untouched until her sheet lands.
- ⬜ **Idle is still front-only**, so Wallad turns to face the camera when he stops
  walking away. Fixable with an idle frame per direction, or by holding the last
  walk frame — worth a look once Roni is done.
**✅ Roni is fully animated (2026-08-20)** — `roni-sheet-v2.png`, three rows of
three: walk, knife throw and hurt, at 2, 2 and 9px baseline spread. Cut and
playing. Her hurt row is the first one either warrior has had.
- ⚠️ **Height is advisory, the baseline is not** — and her hurt row is why. Its
  middle frame is 30px shorter than its neighbours because it is the doubled-over
  stagger. A gate on frame height would have rejected a correct sheet.
- ⚠️ **Two row-detection bugs, both found by this sheet.** Its rows are separated
  by **7px** (a flaring cape below, flying hair above), under the 12px default —
  and inside that gap sat a *single* stray lit pixel, so an `any()` test bridged
  two rows into one 634px band holding six figures. `strip_rows` now uses a 6px
  gutter and treats a row as empty when it is *nearly* empty: one pixel is a
  speck of cape, two is content. Both Wallad sheets still parse unchanged.
**✅ Both warriors are fully animated (2026-08-20).** `elad-hurt-bottom-left.png`
gave Wallad his flinch (row 3: struck / braced / recovered — only the first cell
looks "hurt", but the three read as a cycle) and `roni-directional.png` gave Roni
the same three walks Wallad has, at 2, 2 and 1px baseline spread. Each warrior now
has **idle, three directional walks, attack and hurt**.
- ⚠️ **A painted left-facing row is worse than no row.** Roni's sheet has four:
  front, side-right, back, and side-*left*. The fourth is skipped —
  `player.draw` mirrors the side view for leftward movement, so a painted
  left-facing row could only ever disagree with the mirror it duplicates.
- ⚠️ **Wallad's hurt frame carries painted red impact rays.** The game already
  flashes the sprite and the screen on damage, so that is two hit-indicators at
  once; at 48px it reads as a few red pixels and is fine, but a future hurt row
  should leave the effect to the game.
**✅ Directional idle, with no new art (2026-08-20).** A warrior used to spin
round to face the camera the instant it stopped walking away. It now holds the
direction it was going.
- ⚠️ **The art was already there, inside the walk.** A three-frame walk is
  contact / passing / contact, and the **passing** frame has the legs together
  and the body upright — near enough a standing pose to hold.
  `PlayState._directional_idles` lifts `walk_<dir>[1]` into `idle_<dir>`, so this
  cost one function and no commission.
- "down" is deliberately excluded: the painted `idle` is already a front-facing
  standing pose, and a real one beats a borrowed walk frame.
- ⚠️ **Mirroring is now a rule, not a flag.** `Player._mirrors()` flips only
  sideways views — a mirrored front or back view puts the sword in the wrong
  hand — and "idle" counts as a front view *once a character has directional
  art*. A character with no directional rows keeps the old blanket flip, so
  nothing that predates this changed behaviour.

- ⬜ **Sheets S2–S9 still to land, and the cost is the open question.** §S1 took
  **nine rolls** — but seven of those bought pack-wide fixes (frame count,
  gutters, weapon containment, proportions, character descriptions, facing) that
  every remaining sheet now inherits, and §S2 passed registration on its second
  roll before being rejected for describing the wrong character. Expect 2–3 rolls
  a sheet from here, not nine.
- ❌ Sheet 10 is cancelled: it was art for the book-return burst that §6 removed.

---

## 1. 🔶 Make it look and feel like a real (creepy) school
Right now the art is mixed: flat-color tiles + procedural icons + cartoon-ish
extracted monster sprites + a generated knight. Goal is a consistent, sharp look.

**✅ Art direction — decided: "horror-lite abandoned school at night."**
This was the open question here; it's now settled, and it matches what
`docs/vidadiyot_game_design.md` always said (§1 of that doc: kids sneak into an
old abandoned school at night). Dim, dusty, *atmospheric* — spooky rather than
frightening. Reference register: Luigi's Mansion / Costume Quest, not survival
horror. The audience is kids (the design doc says so outright), so **tension and
mood, no jump-scares and no gore.**

> ⚠️ **Open tension: the title screen is now gore-styled.** The painted
> "The Vidadiyot" logo on the menu (`assets/ui/title.png`, built by
> `tools/make_title.py`) is blood-drenched, with skulls and a spiked mace. That
> is a deliberate choice, but it is louder than the rule above, so the splash
> and the in-game look currently promise different games. Either the rule moves
> to "gory title card, horror-lite gameplay" — a real and common combination —
> or the logo gets a tamer variant later. Worth settling before §1's art pass,
> since whichever way it goes sets the register for every room after it.

**✅ Started: classrooms are furnished** (`world/decor.py`). Each room bakes one
overlay Surface at load — blackboard with the room's color chalked on it,
teacher's desk, a 4×4 grid of student desks, a locker bank down one wall, wall
clock, posters, litter. Layout is seeded from the room id, so a room looks the
same every run while rooms don't look copy-pasted.
- ⚠️ **All of it is non-solid**, which is the constraint §1 always flagged: a
  monster's hitbox is 44×44 against a 32px tile, so solid desks in rows would
  make the room impassable for the monster that lives in it.
- ✅ **UI text is crisp now.** `AssetManager` hands out a `CrispFont` that never
  antialiases — everything renders at 640×360 and is then integer-scaled, so an
  antialiased glyph got its blur magnified. Forced off in one place rather than
  at ~30 call sites, where any of them could reintroduce it.
  ⚠️ Turning antialiasing off is only half of it: pygame's built-in face is very
  cramped at these sizes and *falls apart* with a hard edge — thin, patchy,
  broken glyphs. The UI face is now Verdana (built-in as the fallback), scaled by
  `UI_FONT_SCALE` so it matches the old *widths* and every existing layout keeps
  working. A wide, open face is what survives having no antialiasing.
- ✅ **Title-screen cast is crisp.** The menu used to scale the 48px *game*
  sprites up to 72px — an upscale of already-downscaled art, which is exactly
  what read as pixelated. `tools/make_menu_art.py` cuts everyone at 104px off
  the original sheets so the menu downscales instead. Note the select-screen
  portraits could not be reused: those are painted *scenes* keyed off black,
  invisible on the select page but a grey box against the menu grid.
- Still to do below: corridor dressing, lighting/darkness, dust and cobwebs,
  ambience, the rest of the juice list.

**⬜ Next: real tiles.** The map is still four flat-colour rectangles
(`tools/gen_map.py` paints the whole tileset in code). Two docs drive this:
**`docs/ART_REQUESTS.md`** (what to paint, sizes, the constraints) and
**`docs/ART_PROMPTS.md`** (copy-paste prompts for generating it). Tiles first,
then the three item icons, then classroom props — nothing else in §1 will look
finished until the floors and walls are real.

⚠️ **Do not ask a model for a 32×32 seamless tile.** Image models do not
register tile edges reliably. Ask for a large evenly-textured *slab* of material
and cut tiles out of it in the tooling — that plays to texture generation and
away from edge matching. `tools/` will need a `make_tiles.py` that does the
cutting and edge-blending when the slabs arrive.

**Make the rooms read as a school**
- **Classrooms:** rows of desks, a blackboard on the wall, a teacher's desk, a
  clock, posters/charts, scattered paper and fallen chairs.
- **Lockers** — one per classroom, and it's the **book-return point** (see §5).
  Also lines up with the design doc, which already planned a `Locker` entity.
- **Corridors:** locker banks, notice boards, trophy cases, flickering lights,
  a mop bucket, doors ajar.
- **Other rooms to make it feel like a whole school:** cafeteria, science lab,
  toilets, art room — good fits for the per-classroom weapons (§3). (Library,
  gym, staff wing and the schoolyard are big enough to be their own *areas* —
  they're specced in §4.)

**Atmosphere**
- Darkness + a knight-carried light radius, soft vignette, per-room tint (the
  classroom tints already exist).
- Dust motes, cobwebs in corners, moonlight shafts through windows, a subtle
  screen grain.
- Ambience over music in corridors: wind, distant creaks, a dripping tap. The
  procedural synth (`systems/audio.py`) can carry drones cheaply.
- Juice: hit sparks, movement dust, fireball/web impact puffs, damage numbers,
  screen transitions, a proper pixel font for UI.

**Considerations**
- ⚠️ **Décor must not clog the rooms.** `TILE = 32` and a monster hitbox is
  **44×44 px — larger than one tile** (`settings.py:50`). A classroom is roughly
  8×6 tiles, so solid desks in rows would make rooms impassable for monsters and
  turn every fight into a geometry puzzle. **Rule: most décor is floor-layer and
  non-solid**; at most one or two solid clusters per room, always leaving a
  ≥2-tile lane around the locker.
- ⚠️ **Dark vs. readable.** At 640×360, a murky scene hides monsters and
  projectiles. **Rule: environment dark and desaturated, actors and interactables
  bright and saturated.** The creepiness lives in the *background*; anything that
  can kill you or that you can use stays legible.
- The **garden is a new tileset** (grass, hedges, paths, trees, sky/outdoor
  light), not classroom decoration — it's a chunk of art on its own. It fits
  naturally as the *final area* since the design doc ends with escaping through
  the main gate, so it's tracked in §4 rather than here.
- Internal res is 640×360 integer-scaled (already crisp). Biggest single win is
  matching the tiles' fidelity to the monster sprites.

**✅ Phase 1 map art is in the game** (2026-08-20). The four flat-colour
rectangles are gone: `tools/extract_map_art.py` cuts real material out of the
painted slabs delivered in `~/Downloads/the-vidadiyot/map/`, and `gen_map.py`
now calls it so the tileset and the `.tmx` can never drift apart.
- **8 tiles**, up from 4: herringbone parquet, corridor vinyl, cinderblock,
  stone threshold, three worn-floor variants scattered at 9% through the
  classrooms, and bare stone for the electrical room so leaving the teaching
  wing is legible underfoot.
- ⚠️ **Tiles are cut from big slabs, never painted at 32px.** Image models cannot
  paint a registering 32px tile, so the art is large *material* and `make_seamless()`
  fixes the wrap by cross-fading the overhang back over the near edge. Run the
  tool with `--preview` for a 3×3 repeat — a seam is invisible in a single tile
  and obvious in nine.
- ⚠️ **Two regressions the new art caused, both fixed, both the same mistake:**
  the old flat grey was a neutral backdrop and the painted material is not. The
  classroom tint at alpha 38 turned a parquet room solid red (now
  `ROOM_TINT_ALPHA = 16`), and the cinderblock arrived *brighter than the floor*,
  inverting §1's own rule — a wall that glows pulls the eye off the monster in
  front of it. `TONE` darkens and desaturates it at extraction.
- ⚠️ **The wall slab is an elevation, not a patch** — it came with a dado rail
  and a skirting board, both of which tile into stripes. Only the plain block
  above the rail is usable, which is why `WALL_SAMPLE` sits where it does.
- Painted **book, key, potion and doors** replaced their code primitives.
  `ui/icons.py` owns the swap so the book on the floor and the book in the HUD
  stay one object, and every one keeps its procedural drawing as a fallback for
  a checkout with no source art. All four needed `brighten()` at extraction:
  they were painted lit for a big canvas, and the iron key was simply invisible
  against the HUD at 15px.
**✅ The props landed too** (2026-08-20, `phase-1-rework.png` →
`tools/extract_props.py`). 25 pieces: three desk variants, a chair and a knocked-
over chair, teacher's desk, blackboard, bookshelf, clock, three posters, six
litter specks, the return locker, and the corridor set. `world/decor.py` now has
two furnishing strategies — `_painted()` and the original `_drawn()` kept as the
fallback — behind one `build()`.
- ⚠️ **Crops are *found*, not typed.** The sheet still arrived with painted
  captions above every item, so "biggest blob" finds the label. Instead the
  labels sit in known bands and the items below them are split on black gutters.
  Each band asserts its expected column count, so a merged detection fails loudly
  rather than saving a bookshelf as a wall clock — which is exactly what caught
  the litter strip bleeding into the fittings row.
- ⚠️ **Dark props on a dark floor vanish.** Straight off the sheet the desks
  were invisible: brown wood on brown parquet, with only the lit tabletop edge
  surviving. §1's rule is that the environment stays dark, but the *purpose* of
  the rule is that furniture must not out-shout a monster — furniture nobody can
  see isn't background, it's absent. Fixed with `PROP_GAMMA = 1.3` plus a contact
  shadow under free-standing pieces, which is also what stops a desk floating.
- ⬜ Corridor props (locker bank aside), cobwebs, the window and the creepy-decor
  set are extracted or available but **unplaced** — there is no corridor
  furnishing system yet, only the classroom one.
- ⚠️ The **blackboard came at 2.5×** its final size rather than the 4× asked for,
  so it is the one prop that is a near-1:1 downscale.

**✅ Art requests are written and split into two phases** (2026-08-19).
`docs/ART_PROMPTS.md` is **Phase 1 — the map**: floor/wall material swatches,
damage decals, doors, item icons. `docs/ART_PROMPTS_PHASE2.md` is
**Phase 2 — animation**, and it exists because nothing in the game actually
animates: each warrior has four *single* poses and the walk cycle is a code fake
(a two-step bob plus a 4% squash, `entities/player.py`), monsters are one frame
on a sine bob, and every projectile and effect is drawn with primitives.
- The highest-value sheet in Phase 2 is **the caster wind-up** (Little Terror /
  Little Snir). It is not decoration: a fireball currently appears with no tell,
  so a ranged fight has no readable moment to dodge. Frames hooked to the
  existing cast timer turn that into a fair fight.
- ⚠️ **Art is the larger half but not the only half.** `Player.set_frames()`
  takes exactly four Surfaces, `Monster.draw()` has no animation clock at all,
  and `spritelib` cannot slice a strip. A frame-list animator and a strip slicer
  land with the first sheet, not after it.
- ⬜ Phase 2 (animation) is waiting on art. Phase 1's **round 2** — a tileable
  wall, a top-down doorway threshold, herringbone floor variants, and the props
  at 4× their final size — is what finishes §1.

## 1b. ✅ Playtest fixes (2026-08-20)

From a play session, in the order they were reported.

- ✅ **Monsters left their rooms.** Aggro was pure distance with no line of
  sight, so a classroom guard locked on *through its own wall* and walked into
  the corridor — or the next classroom, where since §5 it silently blocked that
  room's book return. Two additions: `MONSTER_LEASH` (230px from its post before
  it gives up and walks back) and a segment line-of-sight test. A monster now
  stays in the room it guards, which is what makes "clear this room" a promise
  the level can keep.
- ✅ **The leaderboard could be spammed.** Not the reported bug, quite: duplicate
  names *were* refused. The flaw was the opposite — a player who beat their own
  time had no way to record it, so the real board had grown "Wallad" **and**
  "Walladi". `scores.add` now upserts, keeping a player's best run and reporting
  ADDED / IMPROVED / SLOWER so the screen can say "NEW PERSONAL BEST!" instead of
  "name already taken".
- ✅ **The victory screen was a birthday party.** Confetti and balloons on top of
  a blood-drenched painted banner promised a different game. Replaced with
  drifting dust and a few embers in the muted palette.
  ⚠️ It was also *soft*, and the cause is worth remembering: `_draw_ribbon`
  smoothscaled the banner to a **fractional** size every frame for a breathing
  effect, on a 640×360 surface that is then integer-scaled ×2 — so the one
  painted asset on the screen was the blurriest thing on it. It breathes on
  alpha now. **Never resample art per frame at this resolution.**
- ✅ **The colour swatches read as UI dropped on the art.** The door plate, the
  locker plate and the blackboard swatch were all `pygame.draw.rect` in the raw
  palette colour — fine against flat grey tiles, wrong against painted wood and
  steel: fully saturated, perfectly flat, brighter than anything near them.
  `palette.draw_tag()` gives them a darkened body, a lit top edge and a dark rim;
  `palette.draw_chalk()` draws the blackboard's in chalk instead, as an outline
  of a book. Both live in `palette.py` so all three places say "this is the red
  room" identically.
- ✅ **Knockback teleported monsters through walls.** The reported "monster jumps
  from class A to class B when hit": `take_hit` did `self.pos += push * 26` with
  **no collision check**, and walls are 32px — one blow cleared most of a wall.
  The shove is now recorded and spent in `update()`, the only place with a
  collider, through a new `Entity.displace()`.
  ⚠️ **Anything that moves an entity outside its normal velocity must go through
  `displace()`.** A raw `pos +=` is a teleport.
- ✅ **Roni's knife made monsters hop at random.** Same call, different cause: a
  thrown weapon lands *inside* its target, so `monster.pos - knife.pos` is a
  near-zero vector and `normalize()` on that is direction noise at full force.
  The sword, thrown from a body-width away, was stable — which is why only the
  knife showed it. Weapons that know their heading now pass it
  (`take_hit(..., direction=)`), and a blow landing within `KNOCKBACK_MIN_DIST`
  of the centre shoves not at all rather than somewhere invented.
- ✅ **The coloured boxes are gone.** Reported as "colour boxes" on entering a
  class, in class, and on the locker — three separate things saying the same
  thing, all of them flat saturated rectangles stamped onto painted art:
  - The **blackboard swatch is removed outright.** The door plate already tells
    you whose room it is on the way in and the locker tells you where the book
    goes; a third marker chalked on the board was redundant *and* read as a
    bright box floating on a blackboard.
  - The **locker label** was 14x7 on a 16px-wide locker — most of the door. It
    is now an 8x3 inset strip, sized like a real locker label.
  - The **book pickup** was the one I had not spotted: `BLEND_RGBA_MULT` with a
    room colour is destructive, since blue is (90, 140, 240) and so scales every
    pixel's red channel to 0.35. The painted book's highlights, page edges and
    ribbon collapsed into a blue blob. `icons._soften()` lifts the colour toward
    white first, at `TINT_STRENGTH`, which keeps the painting and still reads as
    "the blue book".
  ⚠️ **Shrinking the marks was not enough** — reported again, and rightly. A
  small coloured rectangle is still a rectangle stuck onto a painting. Both the
  door plate and the locker label are now **gone entirely**: `palette.tint()`
  washes the whole object toward its room colour instead, so the red room's door
  is warm wood and the blue room's locker is cool steel, and nothing has been
  added to the picture. Same trick as the book tint — lift the colour toward
  white first, then apply `TINT_STRENGTH` of it, or a saturated multiply crushes
  the painting.
  ⚠️ **The rule this leaves, third time of asking:** *recolour what the art
  already has.* Never draw a coloured shape on top of it. Flat tiles forgave it;
  paintings do not.
  ⚠️ Colour-matching is a core mechanic (§2.8), so the wash has to stay
  **readable**, not just tasteful. 0.30 was too subtle to tell red from green;
  0.42 is the setting that reads across a room. Check all three side by side
  before changing it.
- ⬜ **The book-return effect** still needs work — reported as "not good", and
  the direction wasn't specified. See §6.
- ⬜ **The entrance needs art refinement.** It is the one room with no colour and
  no furnishing pass; it uses classroom parquet and nothing else.

## 1c. 🔶 Audio — real music, synthesized effects

**✅ Music is now streamed and per-state** (2026-08-20). It used to be one
procedural chiptune loop started once in `main.py` and never changed.
`AudioSystem.play_music(track)` streams `assets/music/<track>.ogg` and each state
asks for its own; the menu theme is in, level one is on the way.
- ⚠️ **The mixer moved to 44100 stereo** (it was 22050 mono — real music through
  that sounds like a phone call). The synths still generate mono at 22050 and a
  raw buffer is read in the *mixer's* format, so `_fit_mixer()` converts on the
  way in. Change either rate and that conversion has to keep up.
- ⚠️ **Asking for a track that isn't installed leaves the music alone.** The
  first version fell back to the chiptune, which dropped it on top of whatever
  was streaming — states legitimately request tracks before those tracks exist.
- ⚠️ **Never commit a WAV.** 39.9MB delivered → 2.9MB Ogg, against ~1.5MB for
  the entire rest of the source. `tools/import_audio.py` transcodes, and only
  imports files it has an explicit mapping for so a delivery can't be guessed at.
**✅ Level one and the first effect are in** (2026-08-20). Menu + level tracks
stream; `monster.ogg` overrides its synth with no code change, which is the
pattern every remaining effect follows.
- ⚠️ **Generators fade tracks out, and a loop must not.** The delivered level
  track ended at **1% of its own body level** — looped, the music dies away and
  snaps back to full volume every two minutes. `import_audio._fade_trim()` finds
  where the fade starts, cuts there, and tapers 120ms so the seam doesn't click.
  A *musical* taper is left alone (the menu ends at 51% and keeps it); the bar is
  "faded to near-silence", not "quieter at the end".
- ⚠️ **Delivered names describe the prompt, not the slot.** Real examples:
  `Playful Wet Cartoon Monster Growl.wav`, `monster-grawl-1.wav`. Exact stems in
  `TRACKS` win; `ALIASES` catches the rest by substring, **most specific first**
  (`monster_death` before `monster`, or the death sound becomes the growl), and
  the match is printed so a wrong guess is visible. Take numbers and `(2)`
  suffixes are stripped. An unmatched file is reported, never guessed at.
**✅ Seven effects are real** (2026-08-20): monster, success, zina_bark,
zina_bite, sword_swing, hit_flesh, level_done.
- ⚠️ **Effects arrive padded with silence.** The sword swing was 2.00s of file
  holding **0.28s** of sound; the bite 2.00s holding 0.18s. That is not just
  untidy: a `Sound` holds one of pygame's 8 mixer channels for its whole length,
  so a padded swing fired repeatedly starves every other sound while playing
  nothing. `import_audio._silence_trim()` cuts both ends — leading silence too,
  since a swing that starts 100ms in lands after its own animation.
- ⚠️ **A sound needs no synth entry any more.** `play()` used to look the name
  up in `SYNTHS` *before* looking on disk, so the delivered sword swing — a new
  effect nobody had written a synth for — was silent. File first, synth second,
  neither is fatal. Call sites can now be written before the audio exists.
- ⚠️ **Delivered lengths reshape the game, not just the mix.** `zina_bark` came
  as 1.85s of *sequence* against a 0.42s retrigger interval — four copies of a
  dog stacked on each other — so `ZINA_BARK_EVERY` is now 2.0s and she barks
  once per run. `level_done` is 7.2s on a screen skippable from 1.9s, so it is
  faded out on leaving or it collides with the victory fanfare.
**✅ Twelve effects are real** (2026-08-20): the five above plus `fire_cast`,
`fire_hit`, `web_cast`, `pickup`, `door_unlock` — and with them, the first four
call sites that were *added for* a sound rather than dubbed onto something that
already made noise.
- ⚠️ **The impact sound belongs to the projectile, not to the play loop.**
  `_update_projectiles` reads `f.hit_sound`, a class attribute on `Fireball` /
  `LightBolt` / `WebProjectile`. The alternative was an isinstance ladder in
  `PlayState`, which means every new projectile edits the play loop to be heard.
  A projectile with no `hit_sound` is silent, not an error.
- ⚠️ **The two casts are deliberately different sounds.** `web_cast` and
  `fire_cast` fire on the frame the projectile spawns, so an off-screen monster
  waking up tells the player *which* monster it was before they can see it. Both
  are well under their cooldowns (1.8s fire, 5.0s web), which is the real cap on
  how long a cast sound may be.
**✅ Seventeen effects are real** (2026-08-20): the twelve above plus `potion`,
`player_hurt`, `monster_die`, `emri_blink` and `knife_throw`.
- ⚠️ **Entities ask for sounds; they do not play them.** `player_hurt` and
  `emri_blink` set `sound_request` and `PlayState._drain_sounds` plays it — the
  pattern Zina already used. The alternative was giving `Player.take_damage` a
  reference to the audio system, which means every future damage source has to
  remember to make a noise. ⚠️ The drain runs **before the defeat check**, or the
  killing blow is the one hit that never makes a sound.
- ⚠️ **A silent sound is now a declared decision.** `tests/test_systems.py`
  scans `game/` for every name the code asks for and asserts the still-silent
  set equals `PENDING_AUDIO` exactly — in *both* directions, so a new call site
  without audio fails, and so does a stale entry after a file lands. This is
  what keeps `docs/AUDIO_BOOK.md` honest without anyone remembering to check.
- ⚠️ **`emri_blink` came back at 2.91s** against a 4.55s blink cycle: it plays
  through most of Emri's telegraph. Wired and usable, but the boss level wants
  the 0.5s take the prompt asked for. Same failure as `zina_bark`'s 1.85s.
**✅ The teachers have voices (2026-08-20)** — and the shape of the audio system
changed to take them. They arrived as a **per-character pack**
(`spotplayer` / `throw` / `hit` / `die`, one set each for the female and the
male) rather than as variants of the flat effect names, which is the better
model: `AudioSystem.play_voiced(voice, event, default)` looks for
`<voice>_<event>` and falls back when a character has no pack, or no take for
that event. `Monster.voice` names the pack.
- ⚠️ **A voice never overlaps itself.** `teacher_f_hit` is 1.59s and a sword
  swings every 0.36s, so four hits would stack four copies of the same yelp —
  `zina_bark`'s mistake again. Rather than a cooldown constant per sound,
  `play_voiced` asks pygame whether the clip is still on a channel and skips it.
  That needs no numbers and survives a take being re-recorded at a new length,
  and it means **a long voice take is safe** where a long generic effect is not.
- ⚠️ **The blow and the reaction are two sounds on purpose.** `hit_flesh` is the
  weapon connecting and has to fire on the exact frame or the hit feels unlanded;
  the voice is the monster reacting and is allowed to be slower and to be
  skipped. Both go through `PlayState._hurt_monster`, which is now the one place
  a blow lands — the sword and the knife had drifted into separate copies of it.
- ⚠️ **`import_audio` now reports slot collisions.** `monster_die.wav` and
  `monster_die_v2.wav` both resolve to `sfx/monster_die` because `_stem` strips
  take numbers on purpose, and whichever sorted last silently won. Re-recording
  a take is exactly when that happens and exactly when you want to be told.
**✅ All five music tracks are in** (2026-08-20): menu, level one, victory, defeat
and the duel. ⚠️ The duel track starts from silence and `_fade_trim` only trims
tails, so its loop has a ~2s gap in it.
- ⬜ **Six effects and one voice line still silent, all with live call sites:**
  `tome_hit` (the teachers' throw is voiced, so their attack starts loud and
  lands mute — the most valuable one left), `web_stuck`, `web_break`, `web_hit`,
  `locker_open`, `teacher_f_spotplayer`, and `tome_cast` as a fallback that
  never fires today. **Every one has a ready-to-send prompt** in
  `docs/AUDIO_BOOK.md`, each with a length cap derived from the timer it fires
  on rather than from taste.
- ⬜ **Still no `victory` or `defeat` music**, so both screens keep playing the
  level track. Prompts for all of it: `docs/AUDIO_BOOK.md`.

## 2a. ✅ The cast wind-up — the tell that makes a ranged fight fair

**Done 2026-08-20, and it needed no art at all.** A caster used to fire on the
frame its cooldown expired: the shot simply existed, there was nothing to react
to, and being hit was a question of where you happened to be standing. It now
**commits** — stops moving, locks its aim, grows a charge at its hands — and only
then throws.

⚠️ **This was filed under "waiting on §S5/§S6" and that was wrong.** The fairness
fix is a *timer*, not a painting. The wind-up frames are a better tell than the
drawn charge orb; they were never the mechanism. Anything blocked on art is worth
re-reading for the same mistake.

- ⚠️ **The aim locks when the charge starts.** Tracking the player through the
  wind-up would make the tell purely decorative — there would be nothing the
  warning let you *do*. `test_the_aim_locks_when_the_charge_starts_so_dodging_works`
  walks the player sideways mid-charge and asserts the shot still goes where it
  was aimed.
- ⚠️ **Breaking line of sight cancels it.** A wind-up you can hide from is one
  worth answering.
- ⚠️ **The cast sound moved to the start of the charge**, not the spawn of the
  projectile. A warning that arrives with the shot is not a warning — and since
  each caster has its own voice, it also says which monster woke up before it is
  on screen.
- ⚠️ **The charge draws at the hands, offset toward the aim** — a glow centred on
  the body reads as being lit, not as winding up — and it *grows*, so the moment
  of release is predictable rather than a surprise at the end of a pause.
- Timings are guarded: over a human reaction time (0.35s+), under 60% of the
  caster's own cooldown, and long enough that a walking player clears the
  projectile's width. The web gets the longest warning because it is the worst
  thing to be hit by.
- ⬜ `Caster.charge` runs 0→1 and is exactly what a painted cast strip will read
  to stay in step with the shot. §S5/§S6 now *upgrade* this rather than enabling
  it.

---

## 2b. ✅ Getting hit looks like getting hit

**Done 2026-08-20.** Until now the entire response to a monster being hit was a
**white tint over its sprite** — it flashed into a white box, which reads as a
rendering glitch rather than as pain. Monsters with a painted flinch now play it.

- `MONSTER_HURT_TIME` (0.40s) is separate from `HIT_FLASH_TIME` (0.12s) on
  purpose: the flash is the frame-exact "that connected", far too short to play
  three frames through. A painted hurt is a performance and needs time to read.
- ⚠️ **The tint is now the fallback, not the effect** — it draws only for a
  monster with no hurt art, and never on top of one that has it.
- ⚠️ **Hurt outranks casting.** Being hit mid-wind-up has to *look* like being
  interrupted, or the flinch is invisible exactly when it matters most — during
  the one moment the monster is standing still.
- ⚠️ **A hurt row is now required on every character sheet**, monster or
  champion. It is written into §A of `docs/ART_PROMPTS_PHASE2.md` rather than
  left to be remembered. It also says **not** to paint sparks or rays into the
  frame: the game already flashes and shakes, and Elad's delivered hurt row has
  red rays that fight it.

**✅ Little Terror and Little Snir are both fully sheeted** — walk, cast wind-up
and hurt, front and side, with Little Terror also turning away from the camera.
- ⚠️ **Snir needed *both* her sheets.** v2 is entirely front-facing and v3
  entirely side-facing; Terror's v3 happened to contain her v2, so "take the
  newer sheet" would quietly have thrown Snir's front views away.
- ⚠️ **v3 is drawn facing left** and every directional sprite in the game is
  painted facing right and mirrored — a left-facing row disagrees with the
  mirror on every frame, so it is flipped on the way in.
- ⚠️ **Monsters keep the facing they were last moving in** (`facing_dir`),
  rather than deriving it from the current velocity. A caster stands still for
  its whole wind-up, and deriving it made the monster snap round to front
  mid-cast — which is most of the time it is on screen.
- ⚠️ **The strafe was a sine through zero** and read as a monster stuck
  juddering on the spot: half of every cycle at 0-33px/s, then a reversal. It is
  a steady speed that occasionally turns now, which is what circling looks like.
- ⚠️ **`and self.chasing` on the cast quietly capped every caster at 190px.**
  `MONSTER_AGGRO` is 190 and a fire caster's range is 250, so gating the shot on
  chasing made `CASTER_CAST_RANGE` a dead number. What a shot needs is range,
  leash and a *clear line* — the line being the half worth keeping, since without
  it a caster fires through walls.
- ⬜ **Neither has a back-facing walk except Terror.** Snir never turns away.

**Little Terror's sheet, in detail** (`little_terror_sheet_v3`):
walk, fireball wind-up wired to `Caster.charge`, hurt, and side views of all
three, plus her painted fireball and its impact burst.
- ⚠️ **`kind` is not the art prefix.** The map says `caster`, the files say
  `terror_`. `spawn_monsters(poses=...)` now takes `(prefix, stances)` rather
  than deriving one from the other — deriving an asset path from an identifier
  is what broke the select screen when a warrior was renamed.
- ⚠️ **Blanking beats keying when the position is known.** Each front-row cell
  carries a small purple ①②③ that cannot be cropped out (the horns reach into the
  same rows) and is too close in brightness to key. The cells are evenly spaced,
  so the corner is painted out before the strip is cut.
- ⬜ **No back-facing walk on the sheet** — a BACK pose exists in its neutral
  stand strip, but one still frame is not a cycle. She turns toward the camera
  and sideways, never away. That is the one refinement to ask for.

---

## 2. 🔶 Add more monsters
Currently 2 ranged casters. Add variety in *behavior*, not just stats.

**✅ The teacher monsters are in (2026-08-20)** — a pair of zombie-ish staff, one
female and one male, who hold the *inside* of the classrooms. Little Terror and
Little Snir moved out into the corridors, where the 250-260px range they were
tuned for finally has somewhere to go. The teachers throw a smoking book.

- `Teacher(Caster)` in `entities/monster.py` — a caster that **wanders its post**
  when it cannot see the player, instead of `Caster`'s beeline. ⚠️ Without that,
  a classroom monster is already crossing the floor before the player is through
  the door, and the room stops being a room.
- `DarkTome` in `entities/tome.py` — the first projectile with **painted art**
  rather than a procedural shape, so it is handed its sprite at construction the
  way monsters are. It tumbles by rotating the sprite; a book sliding through the
  air face-on reads as a brick.
- ⚠️ **Who lives where is a range decision.** A classroom is barely wider than a
  fire caster's 250px reach and its 130px kite-away, so indoors it retreats into
  a corner and the fight stalls. `TOME_CAST_RANGE` is 190 and `TEACHER_SPEED` 58.
  `test_the_classrooms_hold_teachers_and_the_corridors_hold_the_casters` fails if
  anyone is moved back.
- ⚠️ **`TOME_SPEED` shipped at exactly `PLAYER_WALK`** (165 vs 165) and the
  balance suite caught it on the first run — a projectile that cannot outrun a
  walk is never hit by a player strolling away. Now 178, still the slowest shot
  in the game.

This was also the first art asked for, gated, extracted and sized **entirely
through the bridge** — no chat window, no hand-measured crop. Three rolls, and
what they taught:

- ⚠️ **The gates cannot see composition, and composition is what fails.** The
  first sheet passed every check — black background, corners dark, no captions —
  and was still unusable: the ATTACK pose was drawn at a third of the size of
  the other three and cropped at the waist. Nothing in `check()` looks at
  whether the items on a sheet are the *same size as each other*, and for a
  four-pose character sheet that is the whole contract. Fixed in the prompt
  ("one common ground line, whole body visible in every one of the four"), not
  in the gate — but a `_matched_heights()` gate would have caught it.
- ⚠️ **§0's "environment must stay dark" applies to the model's whole picture.**
  Both rolls came back at roughly wall brightness, because the style block says
  dark four times and the "actors are bright" invariant lives in `CLAUDE.md`
  where the model never sees it. §R8 now explicitly overrides the palette block
  for its own subject, and `extract_teacher.LIFT` finishes the job.
- ⚠️ **The roster is chibi and nothing says so.** Snir, Little Terror and Emri
  are big-headed cartoon children — roughly three heads tall. The teacher came
  back at realistic adult proportions, about seven, so at 54px she is a thin
  grey stick with a six-pixel head while the others read instantly. This is the
  single biggest thing standing between the delivered art and usable art, and
  it is not written down in any prompt file. See §R8.
- ⚠️ **§0 said nothing about proportions, and §0 is the only file the model
  reads.** The fix landed there rather than in §R8, and Phase 2's §0 got it too;
  while porting it, Phase 1's §0 turned out to be **missing the "characters stay
  bright" exception** that Phase 2 has carried all along, which is most of why
  the teacher kept arriving at wall brightness. Both packs now match.
- ⚠️ **`strip_markdown` left literal asterisks in any bold run that wrapped.**
  `.` does not match a newline, so the emphatic sentences — the ones long enough
  to wrap — were the ones that leaked `**` into the prompt. Nothing pointed at
  it because the requests still worked; it was found by reading a `--dry-run`.
**✅ The classroom loop closed (2026-08-20).** Killing a teacher is now what
*produces* the book, instead of unlocking one already lying in a corridor.
- `MONSTERS` in `gen_map.py` carries `drops` (a book colour) where it used to
  carry `guards`; the .tmx writes it, `spawner` reads it, and
  `PlayState._drop_book` puts a **shining** `Pickup` where the teacher fell.
- ⚠️ **The `guarded` flag is kept but no longer used by level one.** It is how a
  map places an item behind a fight rather than behind a door, and a test still
  covers it — but the level's own books do not exist until they are won.
- ⚠️ **`BLEND_RGB_ADD` ignores source alpha.** The book's shine took three
  attempts because of it: setting a low alpha on the halo does nothing, the full
  colour is added wherever it was drawn, and the result is a flat white disc with
  a hard edge. The falloff has to live in the *colour* of each ring.

- ⚠️ **Column detection does not work on character sheets.** `extract_props`
  finds items by scanning for black gutters, which assumes each item owns a
  vertical slice. A figure with both arms overhead does not: the projectile sits
  in the gap under one arm and shares its x range, so the two merge into one
  item. `extract_teacher._blobs()` labels connected components instead and sorts
  poses from extras by height — a pose spans most of the band, an extra does not.


**Ideas**
- **Brute (melee):** slow, high HP. Contact is harmless now, so it needs a real
  *attack action* — a telegraphed lunge/slam that damages in an arc. (New: melee
  attack pattern; today only casters have attacks.)
- **Swarmer:** fast, low HP, comes in pairs — pressure, not damage.
- **Healer/Summoner:** hangs back, heals other monsters or spawns minions.
- **Boss:** one big monster per level with multiple attack phases.
- Reuse the `Caster` framework for new projectile types (ice = slow, poison =
  damage-over-time). Each new monster = sprite + attack action + stats.
- **Theme them as teachers** (see §4): gym teacher = the Brute, maths teacher =
  the Summoner, chemistry teacher = puddles, the Principal = the Boss. Same
  behaviors as above, but with a fiction a kid remembers — and it gives each new
  monster an obvious home area.

**✅ Emri is in** — the first monster that isn't a sniper. `Blinker` in
`entities/monster.py` runs a four-state loop: **hidden → appear → strike →
vanish**. It never walks: it waits out of the world entirely (invisible,
untargetable, unhittable), materializes one arm's length from you at a random
angle, charges for `EMRI_TELEGRAPH`, throws a `LightBolt`, and dissolves.
- It used to wake on the first book returned; that spawn is gone, along with
  `EMRI_SPAWN_AFTER_BOOKS`. `PlayState.wake_emri()` is now the only way in, and
  nothing in level 1 calls it — §9's boss duel is its intended caller.
- ⚠️ **`EMRI_TELEGRAPH` is the difficulty dial, not `EMRI_HITS`.** The telegraph
  is the only window in which the boss can be hit at all, so shortening it makes
  the fight harder in a way that raising its HP never will — raising HP just
  makes the same fight longer.
- Needed one new rule everywhere else: `Monster.targetable`. `_nearest_monster`,
  `take_hit` and the attack hint all skip anything that isn't currently present,
  or you swing at empty air and the hint advertises a monster you cannot touch.

**✅ The roster is fixed now — nothing respawns.** The old hunter-respawn timer
(a faster monster after every kill, forever) is gone: Little Snir and Little
Terror hold the corridor, one Little Terror stands in each classroom, and a kill
is permanent. A room you clear stays cleared, which is what makes §5's
"clear the room to return the book" rule possible at all. Emri is the only
monster that arrives later, and it arrives on the **book count**, not a timer.

**Considerations:** need a melee-attack action to make non-ranged monsters
threatening (since bumping no longer hurts). Keep the "growl on spot" + red pips.

## 3. ⬜ Weapons the knight can pick up (one per classroom)
Each classroom holds a weapon; picking it up changes the knight's attack.

**Design**
- Weapon pickup entity in each classroom (unlock door → get weapon + return book).
- Weapon defines: damage (hits dealt per swing), swing arc size/range, cooldown,
  maybe a projectile (magic staff = ranged).
- Examples: **Sword** (starter, balanced), **Longsword** (bigger arc/range),
  **Hammer** (slow, hits 2), **Staff** (ranged bolt), **Dagger** (fast, short).
- HUD shows the current weapon; swapping replaces it (or a small loadout).
- Nice loop reinforcement: keys → unlock classroom → weapon + book.

**Considerations:** refactor attack so damage/range/cooldown come from the
equipped weapon instead of constants. Swing visual can vary per weapon.

## 4. ⬜ More levels (needs planning)
Today it's one authored map (`school_slice.tmx`, generated by `tools/gen_map.py`).
Going multi-level needs a level system.

**Level system plan**
- Each level = a Tiled `.tmx` map + a JSON config (spawns, monsters, weapons,
  quests, difficulty). Generalize the generator/loader to handle several maps.
- Add a **LevelManager**: load level N, on win advance to N+1 (carry weapon +
  maybe health), show a between-levels screen, track overall time/score.
- Linear chapters (simple) vs. level-select. Start linear.

**Proposed levels (draft — tune later)**
| # | Area | New stuff | Goal |
|---|-------|-----------|------|
| 1 | Ground floor (current slice) | tutorial: 2 casters, sword | return 2 books |
| 2 | **Library** | +Brute melee, +1 weapon, shelf maze | return 3–4 books |
| 3 | **Gym** | wide-open arena, +Swarmers | survive + return books |
| 4 | **Teachers' room / staff wing** | **teacher monsters**, the Principal | get the master key |
| 5 | Basement / boiler | hazards (dark, doors re-lock) | restore power |
| 6 | **Outdoor schoolyard** | outdoor tileset, night sky, weather | reach the main gate |

**Area hooks — each area needs a *mechanical* reason to exist, not just a reskin**
- **📚 Library.** Tall shelves = a maze that blocks line of sight and projectiles.
  Flips the fight: casters can't snipe you across the room, so it plays close and
  tense. Best fiction fit in the game — **this is where the books come from**, so
  it's a natural home for the loop's story. Possible toy: topple a shelf onto a
  monster.
- **🏀 Gym.** The deliberate opposite of the library: one huge open room, no
  cover, very long sightlines. Ranged casters become genuinely dangerous and the
  knight has to close distance. Bleachers, climbing ropes, a stage. **The obvious
  boss arena.**
- **🍎 Teachers' room / staff wing.** The strongest idea of the batch — see the
  note below. Small warren of staff rooms, the Principal's office locked behind
  the others, a staff-room key ring, roll-call boards.
- **🌳 Outdoor schoolyard.** Playground, football pitch, hedges, bike racks,
  the fence line and the main gate. Open sky, moonlight, maybe rain. It's the
  natural *final* beat — the design doc ends with escaping through the gate.
  ⚠️ Needs a whole new tileset (grass, paths, hedges, trees, fences), so it's the
  most art-expensive area here; worth doing last, once the indoor look is settled.

**🍎 Teacher monsters** — the best hook in this list, because it gives §2's
"behavior variety" an actual *fiction* instead of abstract stat blocks. Each
teacher is a monster whose attack is their subject, which makes them memorable
and instantly readable to a kid:
- **Gym teacher** — fast, melee, charges you (a natural Brute, §2).
- **Chemistry teacher** — throws flasks that leave damaging puddles.
- **Maths teacher** — summons numbers/minions; hangs back (the Summoner, §2).
- **Music teacher** — sound waves in a cone; you have to break the line.
- **The Principal** — the boss. Big, slow, and can *re-lock doors you opened*.

**Design principle: alternate tight and open areas.** Every monster you have is a
ranged caster, so room shape *is* the difficulty dial — open rooms make casters
lethal and force the knight to close, tight rooms neutralize them and favor the
sword. Library (tight) → gym (open) → staff warren (tight) → schoolyard (open)
gives a natural rhythm for free, before any stat tuning.

**Open planning questions**
- What carries between levels — weapons? health? a running timer/score?
- Win/lose flow across levels (retry level vs. restart run).
- Story framing (the doc's abandoned-school premise) or pure arcade.
- Reuse the shelved design-doc ideas (power/alarm hook, escape-the-gate) as a
  level-3/4 mechanic.
- Six areas is a lot to build — is this one long campaign, or a pool of areas to
  pick from? Each one is a map plus (for most) new art.
- Which areas reuse the indoor tileset (library, gym, staff wing all can) and
  which need new art (schoolyard definitely, boiler probably)? Cheapest order is
  indoor-first.

## 5. ✅ Return the book to the room's locker — and clear the room first
Every classroom gets a **locker** (the delivery point) and a **resident guardian**.
You can't deliver the book until that room's monster is dead — so each return is
*earned* with a fight, not just a walk.

> **✅ Shipped 2026-08-20.** Every classroom has a Return Locker on its own wall,
> the book goes *into it*, and it refuses while anything is still alive in the
> room. The §6 burst now fires on the locker instead of on the player, so the
> payoff lands on the objective. The art arrived labelled "Return Locker (book
> drop)" and is lit brighter than the rest of the furniture on purpose — it is
> the one prop that is a game object rather than scenery.
>
> **Three decisions worth keeping:**
>
> 1. **The locker is derived from the room rect, not placed in the .tmx.** The
>    plan was a map object. But the locker has to land in the gap `decor.py`
>    leaves for it, so the map would have been a third file forced to agree on a
>    position decor already owns. `decor.LOCKER_SLOT` is the entire contract, and
>    "exactly one locker per classroom" stops being something map data can get
>    wrong.
> 2. **Any living monster in the room blocks the drop — not just the original
>    guardian.** A webber chased in from the corridor counts. "There's something
>    in here with me" reads instantly; "only the guardian counts" would leave a
>    monster breathing down your neck while the delivery quietly worked.
> 3. ⚠️ **The respawn worry below is now moot.** It was written when hunters
>    respawned on a timer; nothing respawns any more (`_spawn_hunter` is gone),
>    so a blocked room can always be unblocked by killing what walked in. This
>    is why (2) is safe.
>
> ⬜ **Not done:** the locker has no *open* state. The re-request asked for shut
> and open views; only shut arrived, so a filled locker is signalled by a page
> edge painted on its colour plate rather than a door standing ajar.

**The locker as the return point**
Today you return a book by standing *anywhere* in the classroom and pressing E
(`_classroom_at(self.player.pos)`, `play_state.py:247`). Making it a specific
locker is a small change with an outsized payoff:
- The room gets a **focal point** — somewhere to walk *to*, which also gives the
  decoration (§1) a reason to be arranged around something.
- The guardian gets something concrete to guard: **a chokepoint, not a vague
  area.** "Kill the thing standing between me and the locker" reads instantly.
- Delivery becomes a moment of risk — reaching a fixed spot while being chased —
  instead of a formality.
- It's cheap: `Locker` is the existing `Door` pattern almost verbatim (a rect +
  `room_id` + `color` + `dist_to()` + `draw()`, `entities/interactable.py`), and
  `_interact()` already resolves "nearest locked door, else classroom" — it just
  becomes "nearest locked door, else nearest locker". The design doc already
  planned a `Locker` class, so this is picking up something previously shelved.
- Give it the same **colored plate** the door has, so the room's color is readable
  from across the room and the locker announces itself as the objective.

**What already exists (this is half-built)**
The `guards` / `guarded` mechanic is in: a monster with a `guards` property in the
`.tmx` flags its matching book `guarded`, and the book can't be *picked up* until
that monster dies (`world/spawner.py`, `play_state.py:213`). So the piece to build
isn't the guardian concept — it's **moving the gate from pickup to return** (or
adding a second gate at the return step).

**Tasks**
- Add a `Locker` interactable (mirror `Door`) and place one per classroom in the
  map (`tools/gen_map.py` / `school_slice.tmx`), against a wall, with a clear lane
  in front of it.
- Retarget the return branch in `_interact()` (`play_state.py:247`) from
  "player is inside the room" to "player is within `INTERACT_RANGE` of the
  room's locker".
- Track per-classroom "cleared" state: does a living guardian still occupy
  `room["rect"]`? `_classroom_at()` (`play_state.py:266`) already does the
  point-in-room lookup — this is the same test applied to monsters.
- Gate the return: if the room isn't cleared, don't consume the book — show a hint
  instead. The hint channel already exists (`"Wrong classroom for this book"`,
  `play_state.py:286`), so the message costs nothing.
- Place a guardian in **each** classroom (today not every room necessarily has
  one), posted near its locker.
- Decide how this interacts with respawned hunters — see below.

**Considerations**
- ⚠️ **Locker double-duty.** The design doc uses lockers as *hiding spots* for the
  shelved stealth mechanic. Making them the book-return point is compatible and
  arguably better — one iconic object per room, two uses — but if hiding ever
  lands, decide what happens when the room's guardian is parked on the locker you
  want to hide in. Worth an explicit choice then, not now.
- ⚠️ **The respawn rule can make a room un-clearable.** Hunters respawn on a timer
  and wander (`_spawn_hunter`, `play_state.py:226`), so a wandering hunter drifting
  into a cleared classroom would re-lock it — the player could be stuck through no
  fault of their own. Fix: only the *original* guardian (a monster with `guards`
  set) blocks the return, and roaming hunters are ignored by the check. Cheap to
  implement, and it keeps the rule readable to the player.
- Keep pickup gating too, or move it? Gating *both* means two fights per book,
  which may be a slog with 2 books; gating only the return is probably the better
  loop. Worth playing both.
- The HUD should say *why* a return failed, or it reads as a bug.

## 6. ✅ Book-return moment: effect + success sound
**Done, then deliberately cut back (2026-08-20).** Returning a book was silent
and invisible — the counter just ticked. It became a chime, a burst of sparkles,
the room flushing to its own colour, and the HUD counter glowing. **The sparkles
and the room flush have since been removed at the user's request**, and the
reason is worth keeping: a shower of coloured sparks over a rising icon reads as
a mobile game's reward animation, dropped into a dark school at night. It is the
same mistake the victory screen made with confetti, in a different place.

What is left is what carries weight without changing register: **the chime, the
camera shake, and the HUD counter**. `systems/effects.py` went with it — nothing
else used it. ⚠️ The counter-argument, if this ever comes back: the moment does
need *something*, and the shake alone is easy to miss if the player is already
being shot at. If it needs more, it should be more of what is already there —
a longer shake, a heavier chime — not a new colour.

**What shipped**
- **Success chime** — `_synth_success()` + `AudioSystem.play_success()`
  (`systems/audio.py`). A rising E–A–E triangle-wave arpeggio, **0.39s** against
  the victory fanfare's **1.24s**, and softer (triangle, not square), so the two
  moments never blur. Goes through `_get_sfx`, so dropping
  `assets/sfx/success.wav` (or `.ogg`) overrides the synth with no code change.
- ~~**`systems/effects.py`**~~ — the sparkle pool and the rising book. **Deleted
  2026-08-20** along with the burst it existed for; it is in git history if a
  cosmetic pool is ever wanted again.
- ~~**Room tint pulse**~~ — the classroom flushed to its own colour and faded
  back. **Removed 2026-08-20** with the sparkles; `BOOK_TINT_TIME` and
  `BOOK_TINT_ALPHA` are gone from `settings.py` with it.
- **HUD counter glow** — a gold halo expands and fades behind the book counter,
  and the count text washes toward gold (`HUD.draw(..., flashes=…)`).
- **Camera shake** on the return, reusing `camera.shake()`.
- All of it hangs off `Events.BOOK_RETURNED` as planned — `_on_book_returned`
  in `PlayState`. Nothing new needed plumbing.
- Tunables live in `settings.py` under *Book-return payoff*:
  `BOOK_FLASH_TIME`, `BOOK_SHAKE_MAG`, `BOOK_SHAKE_TIME`.

**One thing worth knowing**
- Fixed a latent leak found while wiring this up: the `EventBus` lives on `Game`
  and outlives a run, but `PlayState` and `QuestManager` subscribed without ever
  unsubscribing, so every restart stacked another live listener. `PlayState.exit()`
  now unsubscribes and calls the new `QuestManager.dispose()`. Without it the
  chime would have played twice on a second run.

**Tuning notes from the removed effect** (kept: they apply to any particle work)
- 1px sparkles read as *noise* at 640×360 — they need 2–4px.
- Fading a particle linearly to black makes it look like dirt on a dim floor for
  most of its life. Hold full brightness and dim only over the last 45%.
- The room pulse started at alpha 95 and flooded the screen; 68 read as a pulse
  rather than a flash. This is the §1 "dark environment, bright actors" rule
  biting early — anything additive has to be legible without washing the room out.
- ⚠️ And the one that cost the most time, learned again on the book's shine:
  **`BLEND_RGB_ADD` ignores the source alpha.** Lowering a particle's alpha does
  nothing under it; the brightness has to be in the colour.

## 6b. ✅ Level-complete sequence
Finishing the level now lands as a two-beat celebration before the name entry:
**"LEVEL ONE"** drops in, holds a second so it registers, then **"COMPLETED"**
slams in with a horror sting. Both banners arrive with an overshoot-and-settle
rather than a fade, which is what makes them punch.

- `core/level_complete_state.py`, drawn over the frozen classroom you just
  finished, then handing off to `VictoryState`.
- Art: `tools/make_level_banners.py` lifts the lettering off its painted sheets.
  "LEVEL ONE" sits on a dungeon scene rather than on black, so it needed a steep
  alpha curve (`alpha_gamma`) to separate the slime from its background.
- Sound: `_synth_level_done` — three rising detuned steps that curdle into a
  low, tremolo'd laugh. Deliberately not the victory fanfare: this marks a
  *level*, and the run-end fanfare still marks the run.
- ⬜ The banner says "LEVEL ONE" specifically. When §4's level system lands this
  needs to become per-level art, or a number drawn over a shared plate.

## 7. ⬜ Bestiary — a "Monsters" screen showing every Vidadiya and its ability
A new title-menu entry opening a page per monster: portrait, name, what it does
to you, and its stats. **The art for this already exists** — every monster was
designed as a full character sheet with a stat card baked into it, so this is
mostly cropping and laying out work that's already been paid for.

**The roster, as the sheets define it**

| Monster | Ability (from the card) | HP | ATK | DEF | SPD | In game? |
|---|---|---|---|---|---|---|
| **Little Snir** | "Throws curly hair like spider web on people" | 5 | 26 | 10 | 16 | ✅ web caster |
| **Little Terror** (Maya Tirosh) | **Purple Chaos** — "shoots a burst of chaotic energy!" | 5 | 28 | 12 | 18 | ✅ fire caster |
| **Emri, the Disappearing Monster** | "Uses lightbolt to engage enemies within close range" | 5 | 28 | 12 | 18 | ✅ blink boss |
| **The Teacher** | throws a dark flying book; holds a classroom | — | — | — | — | ✅ tome caster |
| **The Schoolmaster** | the same, wider and slower | — | — | — | — | ✅ tome caster |

⚠️ **The two teachers have no stat card**, because they were not designed on a
card sheet — they were generated through `art_request.py` from §R8/§R9, which
asks for four poses and no card. Either write them a card in the same voice as
the others, or the screen shows three filled rows and two blanks. Their menu
portraits (`teacher_f_menu.png`, `teacher_m_menu.png`, 268px) already exist.

Source sheets (each has MAIN / IDLE / WALK / ATTACK poses):
- `~/Downloads/little_snir_monster_modes.png` — Little Snir, with stat card
- `~/Downloads/maya-tirosh-monsters.png` — Little Terror, with stat card, expression
  row and palette; `~/Downloads/maya_tirosh_monster_2.png` is a cleaner four-pose
  sheet of the same character, no card
- `~/Downloads/emre-monster.png` — Emri, with stat card

**Build notes**
- The screen itself is nearly free: `_BackScreen` in `game/core/menu_state.py`
  already gives an Esc/Enter-dismissed sub-screen, and `HowToState` /
  `LeaderboardState` are the working template. Add `"bestiary"` to `ITEMS`.
- Portraits crop out with the existing flood-fill extractor —
  `tools/extract_snir.py` is the pattern (crop a pose, flood-fill the background
  from the borders, auto-trim, scale). Use the **ATTACK** pose: it's the most
  characterful and it *shows the ability* instead of describing it.
- Monster data belongs in `data/` as JSON (next to `quests.json`), not in code,
  so adding a monster stays a data change. That file then wants to be the same
  one §2 and §4's spawns read from — otherwise the bestiary drifts from the game.
- The stat cards are gorgeous but low-res-hostile; at 640×360 a full card per
  monster won't fit. **One monster per page, Left/Right to flip**, with the
  portrait on one side and name + ability + stat rows drawn in-engine on the
  other. Redrawing the stats in-engine also means they can show *live* values.

**Considerations**
- ⚠️ **The card numbers are fiction and don't match the game.** The cards say
  ATK 26/28, DEF 10/12, SPD 16/18; the game actually runs on `WEBBER_HITS = 4`,
  `CASTER_HITS = 5`, speeds 72 and 66, and has no DEF stat at all. Showing
  numbers that drive nothing is a trap — a kid will compare two monsters by ATK
  and be wrong. **Decide up front:** either display the real tuned values (and
  let the bestiary double as a balance readout), or drop the numbers and keep
  the ability sentence, which is the part that actually helps you play.
- The ability sentences are the real content — "throws curly hair like spider
  web" tells you exactly what the web root is, which the game currently teaches
  only by doing it to you.
- Fits naturally alongside §2: every new monster added there should land in the
  bestiary in the same commit, or the screen rots immediately.
- ⚠️ **Do not gate entries on kills.** "Unlock it by meeting the monster" is the
  obvious idea and it is wrong here: the roster is fixed, nothing respawns, and
  a child who wants to look at the monsters should be able to.
- **Requested 2026-08-20:** the user asked for this explicitly as a menu roster,
  "which is just informative" — so the read is *reference screen*, not progression
  reward, which settles the point above.

## 8. 🔶 Playable warriors — pick who goes into the school
**Done: the roster, the select screen, and two warriors.** A "Select your
Warrior" row on the title menu opens a one-page-per-character screen (portrait,
blurb, stat card, power) — one page rather than a row of cards, because at
640×360 a card carrying all four of those does not survive being shrunk to a
third of the screen.

| Warrior | Plays like | Power |
|---|---|---|
| **Wallad — The Knight** (default) | reach 52, 100 HP, speed 165 | *Steadfast*: none. The longest reach and deepest health bar in the game. |
| **Roni — The Warrior Princess** | reach 38, 85 HP, speed 196 | *Royal Bond*: **[Z]** send Zina. She flies out, bites once — an **instant kill** — and returns. **3 per level.** |

**How a warrior is defined.** `entities/warriors.py` is pure data: the sprite
prefix to animate, the numbers the simulation reads, and an optional power id.
`Player` reads them; there is no subclass per character, so a third warrior is a
dict plus four extracted poses.

**⚠️ The card stats are flavour; the play stats are real.** Each entry carries
its painted `card` (HP/ATK/DEF/SPD) *and* separate `speed` / `max_health` /
`reach` that actually drive the game. This is the §7 trap handled deliberately
rather than by accident — but it means the two can drift. Keep them consistent
in spirit: Roni's SPD 22 is *why* she is the fast one, Wallad's reach is *why* his
SPD 14 is survivable.

**⚠️ Zina is a one-shot kill, so her limits are the whole balance.** Charge count
(`ZINA_CHARGES`), leash (`ZINA_RANGE`) and the round-trip time are what stop the
power from trivializing the level — not the damage, which is infinite by design.
A charge is spent only when she actually launches; pressing Z with nothing in
range costs nothing and says so.

**Animation.** Four painted poses per warrior (idle / walk / attack / hurt),
state-driven: hurt beats attack beats walk beats idle. The sheets give one frame
per state, so the walk cycle is *synthesized* — a two-step bob paired with a
squash on the off-beat — rather than inventing frames the artist never drew.

**✅ Weapons now differ in kind, not just in numbers.** A warrior's `weapon` is
`"melee"` or `"knife"`, and `damage` is how many pips a connect takes:
- **Wallad — Longsword.** Two pips a swing, reach 52. The sword now actually hits
  like ATK 32 said it did.
- **Roni — Royal Blade.** [Space] throws knives across the room, unlimited but
  paced by `KNIFE_COOLDOWN`, one pip each. Range 250 out-reaches both casters'
  keep-away distance, which is the point — and the halved damage is what it
  costs. Zina stays on [Z] as her three-a-level finisher.

This added the first projectile that travels *outward* (`entities/knife.py`), so
`PlayState` keeps `player_shots` separate from monster casts: it damages
monsters rather than the player and dies on the first thing it hits.

**⚠️ Melee had no cooldown — measured, and fixed.** Damage *per hit* said the
knight was 2x the princess. Damage *per second* said something else entirely:
the thrower was capped by `KNIFE_COOLDOWN` while a swing cost only a keypress,
so the knight ran at 4 pips/sec at a gentle 2 presses/sec and **66 pips/sec**
held down. That is not a trade-off, it is a reward for mashing.

Both weapons are paced now (`SWING_COOLDOWN` 0.36s, `KNIFE_COOLDOWN` 0.28s) and
the comparison is throughput:

| | damage | cooldown | pips/sec | from |
|---|---|---|---|---|
| Wallad, longsword | 2 | 0.36s | **5.6** | reach 52 — inside a caster's kite range |
| Roni, knives | 1 | 0.28s | **3.6** | range 250 — outside it |

Melee leads by ~1.6x, paid for by having to stand in a fireball's way.
`test_melee_out_damages_range_but_not_by_a_landslide` pins both ends: melee must
lead, but under 2x, or the thrower is a trap nobody picks. Still worth playing
both through a level — the *feel* of closing distance is not in these numbers.

**Still open**
- ⬜ **Charges never refill.** `ZINA_CHARGES` is per `PlayState`, so a restart
  resets them and there is no pickup that grants one. Fine for a single level;
  needs an answer the moment §4's multi-level system lands (carry over? refill
  between levels?).
- ⬜ **Wallad's "power" is the absence of one.** Steadfast is honest but flat next
  to sending a dog. His sheet has **ATTACK 2 – LIGHTBOLT** and **ATTACK 3 –
  EXECUTE** painted and unused — a chargeable lightbolt, or an execute that
  finishes a monster below one pip, would give him a Z of his own.
- ⬜ **Zina has no sprite variety** — one pose, flipped by direction. The sheet's
  RUN row would give her a real gait.
- ⬜ More warriors. The pattern is a dict + four poses; the sheets exist.
- ⬜ Warrior choice isn't saved between sessions (the leaderboard already writes
  to a per-user dir — the same place could hold this).

## Art pipeline

Source art lives in a tree under `~/Downloads/the-vidadiyot/`
(`champions/`, `monsters/`, `menus/`, and `tiles/`, `props/`, `items/` as they
arrive). `spritelib.source(name)` resolves a **filename** across that tree and
the flat Downloads folder, so a tool names the file it wants and art can be
refiled without editing nine extractors. Two sheets are still loose and want
moving in: `little_snir_monster_modes.png` → `monsters/`, and
`maya-tirosh-monsters.png` → `monsters/` (it is Little Terror's card sheet; the
tree currently only has `maya_tirosh_monster_2.png`, which has no stat card).

Every extractor is re-runnable and idempotent — `tools/*.py` regenerate every
derived asset in `assets/` from the sources, so nothing in `assets/` is precious.

### 🔶 `tools/art_request.py` — asking for art without leaving the repo

The pipeline was automated on both sides of one manual step: a human pasted a
prompt from `docs/ART_PROMPTS*.md` into a chat window and downloaded the PNG
into the source tree. This tool closes that gap by calling the OpenAI Images API
(`gpt-image-1`) directly, writing the result into the tree under the filename
`spritelib.source()` already resolves.

```bash
./venv/bin/python tools/art_request.py --list            # sections in the pack
./venv/bin/python tools/art_request.py R1 --dry-run      # exact payload, no cost
./venv/bin/python tools/art_request.py R1 --out map/tiles/wall_v2.png
./venv/bin/python tools/art_request.py --check <file>    # gates, on existing art
```

Three decisions behind it:

- **The prompt packs stay the source of truth.** Sections are parsed out of the
  markdown at run time (`## §N Title` in Phase 1, `## Sheet N —` in Phase 2), and
  the prompt is the *blockquote* under the heading. Unquoted prose is commentary
  for us — §1's "image models cannot paint a seamless tile" warning is the reason
  that distinction exists — and is never sent. Preambles chain automatically: §0
  on everything, §R0 on the re-do sheets, §A on the Phase 2 sheets, exactly as
  the headings instruct.
- **Stdlib only.** The venv is five packages; `urllib` makes the call. No new
  dependency, and nothing about the game's runtime changes.
- **⚠️ What comes back is not trusted.** `check()` runs before the art can reach
  an extractor, gating on the two failures this pipeline has actually suffered:
  art delivered on a painted scene rather than flat black (`level-one.png`, which
  then needed a bespoke alpha curve), and a bright border or vignette reaching
  the corners. A failing sheet is renamed `.rejected.png` rather than deleted, so
  it can be looked at. **Painted text labels are still an eyes-on check** — the
  trap that once made a cutout tool export a 387px ribbon instead of the knight —
  and the tool says so on every pass.

The key lives in `.env` at the repo root (`OPEN_AI_API=` or `OPENAI_API_KEY=`),
which is **gitignored as of this work — it was not before, and it was staged for
commit.** Note this is the OpenAI *API*, billed per image on an API key; a
ChatGPT subscription does not cover it.

⬜ **Not yet exercised against the live API.** Everything up to the network call
   is verified — both packs parse, preambles chain, the gates catch a painted
   scene and a bright corner (`tests/test_art_request.py`, 10 cases, no key
   needed). The first real request should be §R1, the tileable wall, since it is
   the outstanding re-do with the most visible payoff.
⬜ A `--extract` flag chaining straight into `extract_map_art.py` would close the
   loop end to end; today the extract step is still run by hand.

## Testing

`pytest` suite in `tests/`, 347 tests, headless and a few seconds to run — see
the README for layout. Two things worth knowing before adding to it:

- **`test_balance.py` asserts relationships, not values.** "Fireballs must be
  faster than a walk but slower than a sprint" survives retuning; "fireball
  speed is 210" would just break every time you touch it. This is where a
  tuning change that has a consequence somewhere else gets caught.
- **Drawing is part of the test.** Several fixtures render each frame, because
  a real share of the defects here are draw-only (a rect built from a stale
  size, a surface keyed to the wrong room). A test that only calls `update`
  never sees them.

**Defects the suite found on its first run:**
1. The defeat screen printed *"Enter: try again"*, but no intent was mapped to
   Return — the advertised key did nothing and only E/Space restarted. Fixed in
   `DefeatState.handle_event`.
2. **Both casters' projectiles were slower than a walking player** (fireball 155
   and web 140 against `PLAYER_WALK` 165). You could stroll away from every
   shot, which quietly made both ranged monsters harmless to anyone retreating.
   Raised to 210 / 190 — still under `PLAYER_SPRINT`, so spending stamina stays
   the way out.

**Known limitation, deliberately pinned rather than fixed:** `move_and_collide`
tests the destination, so a step long enough to cross a whole wall tunnels
through it. Nothing in the game moves fast enough — the guard is
`test_nothing_in_the_game_moves_far_enough_per_step_to_tunnel`, which fails if
any speed constant is raised past the margin.

## Engine notes

**⚠️ Edge intents must be latched across the fixed timestep.** `Input.poll()`
runs once per *render* frame, but the sim steps at a fixed 60Hz — so on a 120fps
display roughly **half of all single key presses were consumed by a frame that
ran no sim step at all**, and a stalled frame delivered the same press two or
three times. That is what "doors don't open with E" actually was; mashing Space
hid it, a single tap of E did not. `Game.run` now parks each press in a pending
`InputState` and hands it to exactly one step. Any new edge intent must be added
to `InputState.EDGE_FIELDS` or it will inherit the original bug.

**Sound is a registry, not a method per noise.** `audio.SYNTHS` maps a name to a
synth fallback, and `audio.play("zina_bark")` looks it up; dropping a real file
at `assets/sfx/<name>.(wav|ogg)` overrides the synth with no code change. Giving
a new character a voice is one synth plus one line. Entities never touch the
audio system — Zina raises `sound_request` and PlayState plays it, the same
pattern the casters use for `cast_request`.

## 9. ✅ Boss level — the duel with Emri (2026-08-20)

**Clearing the level no longer ends the run.** LEVEL ONE / COMPLETED now hands
off to a duel instead of straight to the leaderboard, and the clock carries over
so a run is still measured whole.

⚠️ **The duel is `PlayState(duel=True)`, not a state of its own.** Emri has to
move, cast, be knocked back, be hit and die under exactly the rules the rest of
the game runs on — a bespoke boss state would have been a second implementation
of all of that, and the second one is always the one with the bugs. `duel`
*removes*: every other monster, every pickup, every locker, the room's furniture
and the book quest. It leaves one room, one very strong monster and the clock.

- ⚠️ **The arena needs no new mechanic.** A classroom's door starts locked and
  the duel gives the player no keys, so the room seals itself.
- ⚠️ **The furniture goes.** A duel against something that blinks to arm's length
  is about spacing; desks turn that into a scenery problem — the boss can appear
  behind one and you cannot back away in a straight line.
- ⚠️ **Winning is "Emri is gone", not "the roster is empty".** It starts
  untargetable and away, so an empty-roster test would hand over the win on
  frame one, before the boss had arrived. `_emri_woke` guards it.
- ⚠️ **Stripping happens *after* the world is built**, not instead of building
  it. The map, the collision, the camera bounds and the room rects are all still
  wanted, and building a cut-down version of them is how two paths drift apart.
- ✅ It has its own track (§M5, `level-1-boss-background-music.wav`). ⚠️ That
  track **starts from silence**, and `import_audio` trims a fade-*out* at the end
  of a loop but nothing at the start — so a ~2s gap opens every time the 128s
  loop repeats. Inaudible in a short fight, obvious in a long one.
**✅ The duel has phases (2026-08-20).** At 75%, 50% and 25% of its health Emri
**leaves** — hidden, untargetable, not advancing its own state machine — and two
of the school's own arrive. Only when they are dead does it come back.
- ⚠️ **The marks are one-way.** Emri does not regenerate, so a fraction already
  passed is popped off the list rather than compared again; sitting exactly on
  0.5 would otherwise summon a room's worth of monsters one frame at a time.
- ⚠️ **Zina wounds a boss rather than killing it.** Her bite kills an ordinary
  monster outright, which made Emri a formality — one charge of a power the
  player carries three of. `Monster.boss` marks the exception and a bite is worth
  a third of the boss's health, so spending every charge is a real answer and
  still not a free win.
- ⚠️ **Emri drifts while visible.** It was nailed to the floor between blinks,
  which reads as a prop for the 1.3s it spends telegraphing. It circles now, at
  34px/s — slow enough that the telegraph is still a window to swing into.
- It is bigger than an ordinary monster (`EMRI_SIZE`), because a boss the size of
  a classroom monster reads as one whatever it does.
- **`--boss` starts the duel directly** for testing. ⚠️ Deliberately a flag and
  not a menu entry: the duel is the end of a full run, and a title-screen route
  to it would let a player skip the level to reach it.

**✅ Playtest round two (2026-08-21).**

⚠️ **`set_alpha` on a per-pixel-alpha surface fades the *rectangle*, not the
shape.** It discards the mask, so every impact splash and every Zina bite drew a
visible box. Three places did it — the splash pool, Emri's blink fade, and the
knife — and all three now multiply into the existing alpha with
`BLEND_RGBA_MULT`. **This is the single most repeated graphics mistake in the
codebase**; if something renders as a box, look for `set_alpha` first.

⚠️ **The duel handed out keys, and a key opens the arena.** `_drop_key` fired on
every monster death including Emri's summons — so killing one gave the player a
key to the classroom door they were sealed behind, and they could walk out of the
boss fight and strand the remaining add. Keys no longer drop in the duel, and the
duel's doors are `sealed`: a sealed door takes no key at all.

⚠️ **A key you never see is not a reward.** Keys went straight into the pack, so
the whole payoff for a fight was a number changing in a HUD corner. They drop on
the floor, shining, where the monster fell.

**✅ Emri at 24 hits, up from 8 (+200%).** At 8 a single sword swing was a
quarter of the boss, so Wallad's *first* hit tripped the 75% phase break and the
fight was over before it had a shape. A swing is now one twelfth.

**✅ Emri is fully animated** off `emri-movement-and-frames-v2/-hurt-v3`: front,
back and side walks, a cast and a hurt. ⚠️ Both sheets were needed — v3 has the
hurt and a better run, v2 has the front and back walks — and their side and back
rows are separated by **5px**, the third sheet to need hand-measured bands.

**✅ The electrical room has a resident.** It held a potion and nothing else: the
one room on the map you could walk into and out of for free.

**✅ Roni's knife lost its streak trail** — five drawn lines added when the knife
was a 3px circle and needed help reading as a thrown object. It is a painted
blade now, and the trail was a second, cruder weapon drawn behind the real one.

**✅ Playtest round three (2026-08-21) — the duel's rhythm.**

⚠️ **A summon spawned inside the wall and deadlocked the fight.** The spawn was
`min(room.bottom - 60, player.y - 90)` with no *lower* bound, so a player
standing near the top of the arena put Emri's help **above the room's own top
edge**, inside the wall. An unreachable monster never dies, `_adds` never
empties, and Emri never comes back. `_spawn_spot` now clamps into the room and
walks the point down until it is genuinely standable.

⚠️ **Two phase breaks, not three, plus a grace period.** At 0.75/0.5/0.25 they
sat about six health apart — three sword swings — and a player landing a burst
crossed two in seconds, so it read as Emri *running away* rather than as a fight
with phases. Marks are now 0.66/0.33, and `EMRI_PHASE_GRACE` keeps it present for
7s after a return before it may leave again. **Damage arrives in bursts, so marks
alone cannot space breaks out** — that is what the grace is for.

⚠️ **A deferred break must not be a lost one.** The first version popped the mark
whether or not the grace let the break happen, which silently threw the phase
away — a player who burst Emri down got no break at all. Marks are only spent
when the summon actually fires.

⚠️ **A phase break summoned twice and stranded a live playtest.** `_summon_help`
fired once per *mark*, and a single heavy blow can cross two — which put four
monsters onto the two spawn points, two of them standing exactly inside the other
two. The player killed the pair they could see and Emri never came back, because
`_adds` still held the pair hidden inside them. **One break per crossing now,
however many marks it crossed.** The lesson generalises: a threshold that can be
passed by more than one step at a time needs a *crossed* flag, not a loop.

⚠️ **Monster collision was off whenever the player was touching one.** The
player's collider skipped any monster it was *already* overlapping, so an overlap
could be escaped — but monsters close on you constantly, so contact is the normal
state, and while touching, the player walked straight through. No exclusion now:
`Entity._resolve` snaps a body **out** of a solid it starts inside, and
`_separate_from_monsters` pushes along the shallowest axis for the other half of
the problem — a monster walking onto a player who is standing still, where
nothing the player does would trigger a resolve at all.

⚠️ **Zina's bite is a flat pip cost, not a share of the boss's health.** It was
`max_health / 3`, so against a 24-hit Emri one bite removed a *third of the
fight* — and it silently rescaled every time `EMRI_HITS` moved, so tuning the
boss quietly retuned the dog. `ZINA_BOSS_DAMAGE` is 3 pips: the heaviest single
blow in the game (a sword swing is 2), with all three charges coming to 9 of 24.

⚠️ **How long Emri is on screen is one number spread over three constants.**
`EMRI_TELEGRAPH + EMRI_STRIKE_TIME + EMRI_VANISH_TIME` was 2.35s — gone before a
player had crossed the room, so the fight was mostly chasing an empty floor. Now
3.35s: long enough to close, swing twice, and still be punished for over-staying.

- ⬜ **Tuning dials, all in `settings.py`:** `EMRI_HITS` (24), `EMRI_PHASE_MARKS`
  (0.66, 0.33), `EMRI_PHASE_GRACE` (7s), `EMRI_PHASE_ADDS` (2),
  `ZINA_BOSS_DAMAGE` (3 pips), and the three timings above. A simulated fight at four swings a second wins in ~12s
  and sees one break; a human pace sees both.
- ⬜ **Losing the duel is a plain defeat** — the level-one win does not stand.
  Worth revisiting after a playtest: it may be brutal to lose a clean run at the
  boss, and "the level counts, Emri is the bonus" is the gentler reading.

### The original plan, for reference
**Emri is built and parked.** The `Blinker` behaviour is finished and covered by
tests; what changed is *where* it belongs. Dropped into level 1 it was simply too
much: it woke on the first book returned and then blinked in, struck and vanished
faster than a player could answer, on top of the monsters already in the room.

**The shape.** Once every book is home, a door that was never there opens: a
hidden classroom, and a one-on-one duel with Emri. Beating it is what carries you
to the next level, so it reads as the punctuation *between* levels rather than
another room inside one.

**What already exists**
- `Blinker` (`entities/monster.py`) — hidden → appear → strike → vanish, with the
  `targetable` rule that makes it unhittable while gone.
- `PlayState.wake_emri()` — summons it, with the arrival banner, growl and shake.
  Nothing calls it during level 1 any more; the boss level is its caller.
- `LightBolt`, and the 104px `emri_menu.png` crop already on the title screen.

**Retuned for a duel** (it was tuned as a level-1 ambush):
`EMRI_TELEGRAPH` 0.55s → **1.30s**, `EMRI_VANISH_TIME` 0.40 → **0.75**, hidden
gap 1.5–2.6s → **2.2–3.4s**. It now spends over 2 seconds on screen per blink
instead of well under one, which is the difference between a fight and a coin
flip. `test_emri_stays_visible_long_enough_to_answer` guards that.

**Still to decide**
- ⬜ Where the hidden classroom lives — a fourth room on the existing map, or its
  own tiny arena map (which is really §4's level system arriving early).
- ⬜ Whether the duel is a separate `State` or a `PlayState` with one monster and
  no books. The latter reuses everything; the former makes the "between levels"
  framing explicit.
- ⬜ What you bring in: full health, or whatever you finished the level on?
- ⬜ Losing the duel — replay just the duel, or the whole level?
- ⬜ It should arrive *after* §6's level-complete banners, not instead of them.

## 10. 🌟 Multiplayer — play the knight *or* the Vidadiya (1v1 / 2v2 / 3v3)
Pick a side. Knights hunt books, monsters hunt knights, teams fight it out.

> 🌟 **Stretch goal — deliberately parked.** This is the biggest item in the doc
> by a wide margin, and it's the *last* thing to touch: not before the art is
> crisp (§1), there are more monsters (§2), weapons (§3), and more than one level
> (§4). Multiplayer on top of a thin game just multiplies the thinness. Kept here
> in full so the shape is on record, not because it's next.

**Modes**

| Mode | Shape | Notes |
|---|---|---|
| **Co-op** | 2–3 knights vs. AI monsters | Easiest — no PvP balance needed, reuses the current win condition |
| **1v1** | 1 knight vs. 1 monster | The purest test of the asymmetry |
| **2v2 / 3v3** | N knights vs. N players-as-monsters | Team play; may need a bigger map (ties into §4) |

**The two roles**
- **Knight** — melee sword, health pool + regen, stamina sprint, potions.
  Already exists (`entities/player.py`).
- **Vidadiya (playable)** — ranged caster. Little Snir's web is *already* a great
  PvP mechanic: `Player.take_web()` roots the knight and costs him Space-presses
  to `struggle_free()`. Little Terror's fireball is direct damage. A monster dies
  in `hits` (2–3), a knight has a health bar — so the monster plays as glass
  cannon and the knight as the bruiser. That asymmetry is the fun; don't flatten it.

**Win conditions** — asymmetric objectives beat plain deathmatch
- **Knights win:** all books returned before the timer runs out.
- **Monsters win:** the knight team's lives run out, or the clock expires.
- Monsters respawn on a delay (the hunter-respawn rule already in `PlayState`),
  knights have limited lives → natural tension, and it reuses code we have.

**Staged plan — each stage is playable on its own**
1. **Multi-player sim.** `PlayState.player` → a `players` list. Monster AI targets
   the *nearest living* knight. Per-player camera + HUD. No networking at all.
2. **Local split-screen.** Two `InputState`s off one keyboard (WASD+Space vs.
   Arrows+Enter), or a gamepad. Two 320×360 viewports side by side.
   **This already gives real head-to-head play with zero netcode.**
3. **Playable monster.** Split `Monster` into stats/actions + a *driver* — AI
   driver vs. input driver. Monster intents: move, cast, maybe a dash. The
   existing intent abstraction (`core/input.py`) means this plugs in cleanly.
4. **PvP balance pass.** Knight-vs-monster is *not* balanced today — the numbers
   were tuned for one knight against dumb AI. Needs its own constants (separate
   from the Easy/Normal/Hard damage scaling, which is a PvE axis).
5. **Online netcode.** See sketch below.
6. **Lobby.** Create/join a room by 4-letter code, pick a side, ready-up.

**Netcode sketch (stage 5, only if online is really the goal)**
- Authoritative server running the *same* sim headlessly — no rendering,
  `SDL_VIDEODRIVER=dummy`.
- The fixed timestep is a real head start: `game/core/game.py:52` already advances
  the world in deterministic discrete `FIXED_DT` steps, which is exactly what a
  server loop wants.
- Clients send intents (an `InputState` is a few bytes); server broadcasts
  snapshots at ~20 Hz; clients interpolate between them.
- **Skip rollback/prediction in v1.** Six friends on decent connections don't need
  it. Add prediction only if it actually feels laggy.
- Transport: WebSocket — works from both the browser build and desktop.
- ⚠️ **This needs a real backend**, unlike the WASM single-player port (which is
  pure static file hosting). One small Python process per match on Fly.io or
  Railway. Different hosting story, different cost, ongoing upkeep.

**Considerations**
- `self.player` (singular) is threaded through `PlayState` (351 lines),
  `Monster.update(dt, player, collider)`, `Camera`, and `HUD`. **Stage 1 is the
  real refactor** — everything else stacks on top of it.
- `PlayState` mixes simulation and drawing; a headless server needs them split.
- Asset loading in `enter()` touches the display — headless needs it lazy/optional.
- **Effort, honestly:** stages 1–4 (local split-screen, fully playable 1v1 and 2v2
  on one machine) ≈ **1 week**. Stages 5–6 (online) ≈ **3–4 weeks**, and it's the
  only item in this roadmap that is a genuinely different *class* of project —
  a persistent server, sync bugs, reconnects, lobby, matchmaking.
- **Recommendation: stop after stage 4** unless online play is the actual goal.
  Split-screen with a friend next to you is most of the fun for a fraction of the
  work, and it's a hard dependency of the online version anyway — nothing is wasted.

**Open questions**
- Split-screen or a shared camera for local play? Shared camera (both players must
  stay on screen) is simpler *and* creates its own tension; split-screen scales
  better to 3v3.
- Do monsters keep the PvE respawn-hunter rule in PvP, or fixed lives per team?
- Can teams mix sides? ("one monster secretly helps the knights" is a fun betrayal
  mode, but it's scope.)
- Is 3v3 too crowded for `school_slice.tmx`? Six players probably want a bigger
  arena — folds into the level system in §4.
- Online: private rooms by code, or public matchmaking? Code is far simpler and
  much safer for a kids' game.

## 11. 🔶 The intro — the two minutes before the title menu

**Written, not built (2026-08-20).** Three documents, all of them runnable by
the tools rather than only readable:

- **`docs/INTRO_SCRIPT.md`** — nine beats, sixteen dialogue cards, 120 seconds,
  plus the appendix for `IntroState`.
- **`docs/ART_PROMPTS_INTRO.md`** — seven painted plates, a run cycle, a bust and
  a transition motif. Parsed by `art_request.py --phase 3`.
- **`docs/AUDIO_INTRO.md`** — one through-composed cue and nine effects, written
  for Suno. Every filename in it has a `TRACKS` entry.

**The story, as the user gave it:** Roni and Wallad walk out of the woods to an
abandoned school and stop, because something is wrong. A girl runs out shouting
for help: **TikTak** has taken **Queen Maya** and hidden her somewhere inside, he
has changed her friends **Snir, Tirosh and Emri** into monsters, and he has taken
every book in the school. Return the books and the Queen goes free.

**⚠️ It is made of paintings and existing sprites, not of a forest map.** Building
the woods as a real tilemap costs the whole outdoor tileset §4 already flags as
the most art-expensive thing on this list, to buy one scene nobody plays. Plates
with a slow push-in, with the game's own walk cycles composited on top, costs
seven images — and the compositing is the *point*, not the saving: the three
monsters in the intro are literally the three monsters in the school. A painted
monster that doesn't match the one in the classroom teaches the wrong face.

**⚠️ The lore needed one repair, and it is in the bestiary.** §7's table labels
Little Terror *(Maya Tirosh)* — the name on the delivered character sheet. The
intro splits it: **Maya** is the Queen who was taken, **Tirosh** is the friend who
was changed, and they cannot be one person. **The monster keeps the name "Little
Terror" and the parenthetical becomes *(Tirosh)*.** No asset renames — the
sprites are `terror_*.png` and stay that way.

**⚠️ TikTak is a promise the game has not kept yet, and the script is careful
about it.** The girl states the *campaign* goal; level one still ends at Emri,
the first of the three friends you catch up with, and the intro never says
"tonight". TikTak is now what the campaign points at (§4's level system is the
route). His design is already half-built by accident: his name is a clock, the
duel track (§M5) is built on "a ticking clock rhythm", and `props/clock.png` is
already stopped at a sinister hour. **His head is a stopped school clock and he
moves in ticks** — which is also a free boss mechanic when §4 gets there: a thing
that only moves on the beat is a thing whose rhythm you can learn.

**⚠️ The music is delivered first and the picture is timed to it.** Suno will not
put a section change at 1:08 because a document asked. So the whole sequence is
two flat tables — `BEATS` and `CARDS` — and retiming to what actually arrives is
an edit to those numbers and nothing else. The grid is **60 BPM, one tick per
second**, which is TikTak's own tempo, and every beat boundary is a multiple of
four seconds so the cuts land on bar lines for free.

**The two things the intro buys the game, beyond atmosphere:** the roster's three
faces are named and shown *before* the player meets them, and the objective is
stated in one sentence a child can repeat — "Every book home, and the Queen goes
free", which is exactly true of the loop §5 already built.

### What landed on the tools side

Both packs are wired, because a prompt book the tooling cannot reach is half a
document.

**✅ `art_request.py` gained a third gate.** Every sheet before this arrived as
objects on flat black, or as a material swatch; an intro plate is a **full-bleed
painted scene** and both existing gates reject it for being exactly what it was
asked to be — the object gate because a plate *is* a painted scene, `--material`
because a plate has a focal point and a swatch must not.
- ⚠️ **The quiet failure is the dangerous one.** A night plate painted dark
  enough *passes* the object gate, and nothing then says the wrong gate ran. That
  is why `SCENE_SECTIONS` is a declared list rather than "whatever the default
  rejects" — the third time this project has learned that lesson, after
  `MATERIAL_SECTIONS` and `STRIP_SECTIONS`. There is a test pinning it.
- The scene gate checks the two things a plate can actually get wrong: that the
  painting reaches all four edges (a letterboxed picture slides a black bar into
  shot the moment the camera moves) and that no text is painted into it.
- ⚠️ **1536×1024 is 3:2 and the game renders 16:9.** The top and bottom of every
  delivered plate are cropped away; §I0 states the safe area (the central
  1370×770) because content painted in the corners is content painted for nobody.

**✅ `import_audio.py` learned that not all music loops.** `_fade_trim` cuts the
tail off any track that ends below a quarter of its body level, which is right
for a loop that would otherwise die and snap back every two minutes — and wrong
for the intro cue, which is *supposed* to resolve into the title screen.
- ⚠️ **This was already a live bug.** `victory` and `defeat` are one-shots too and
  have been going through the loop trim since they landed. All five one-shots are
  in the new `NO_LOOP` set.
- ⚠️ The alias table needed the "monster_death before monster" ordering again:
  `intro_gate_final.wav` contains the needle `intro`, so the general rule would
  have filed a gate clang as the two-minute cue.

**No gameplay code was touched.** The intro is a new state and a new extractor
when it gets built; nothing in `game/` needs to change to make room for it.

### ⬜ What is left

1. **Name the girl.** She is `Yali` as a placeholder, in one line of the script
   and one of the art book. Every other name in this game belongs to a real
   child, so this is a decision, not a detail — and it has to be made *before*
   §I3 is requested, because her portrait prompt describes her.
2. **Generate the cue** (§X1), then retime the beat sheet to it.
3. **Request the art** — seven sections, and §I2 is the one to get right: it is
   on screen for 48 of the 120 seconds and it has a script dependency (exactly
   one lit window, because Roni's line points at it).
4. **Build `IntroState`** — the appendix in the script doc has the shape, the
   tests worth having, and the two traps (`EventBus` handlers must not outlive
   it; the skip reuses existing edge intents so `EDGE_FIELDS` needs nothing new).
5. **Add "Story" to the title menu**, so it can be watched again on purpose —
   same argument as the bestiary in §7.

---

_Update this file as items progress; see `docs/vidadiyot_game_design.md` for the
original concept and `README.md` for how to run._
