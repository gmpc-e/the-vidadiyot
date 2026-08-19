# Roadmap — The Vidadiyot

Living doc for planned work. Spirit: **fun sandbox** — pick what's fun, no
obligation to finish everything.

**Where it lives:** `~/github/the-vidadiyot` → https://github.com/gmpc-e/the-vidadiyot
(`main`). The user pushes with **GitHub Desktop** and plans to branch later, so
leave committing to them unless asked. `venv/ build/ dist/ .idea/` are
gitignored — ~1.5MB of source against ~117MB of ignored build output.

**Current state:** a playable level with a painted title screen and warrior
select; two playable warriors (Elad — longsword; Roni — thrown knives + Zina);
three ranged monsters designed, two of them live (Little Snir = web, Little
Terror = fire) with Emri built but parked for the boss level; furnished
classrooms; keys→doors→books loop over three guarded books; potions, timer,
level-complete sequence, victory + leaderboard, defeat; difficulty scales monster
damage. 330 headless tests.

**The one thing holding the look back:** the map is still four flat-colour
rectangles. See §1 and `docs/ART_REQUESTS.md` / `docs/ART_PROMPTS.md`.

Status legend: ⬜ not started · 🔶 in progress · ✅ done · 🌟 stretch goal

Rough order: **§1–§2 make it feel good, §3–§4 make it bigger, §5 tightens the
core loop.** §10 (multiplayer) is a *stretch goal* — not until the game is crisp
and there's more of it. Plenty to do first.

**Next up, in order:** (1) map tiles — §1, blocked only on art; (2) §5 lockers,
which gives the book-return burst a real destination; (3) §9 the Emri boss duel,
whose behaviour is already written and tested.

**Level 1 pacing (2026-08-19):** a run was finishing in ~60s. Three books now
instead of two, **every** book guarded (6 monsters, up from 5 with one book free),
Snir and Terror +15% HP, Roni's knife -15% damage. Required fighting time roughly
doubled — but note most of a run is *walking*, so the third book is what actually
lengthens it; the HP bump adds only a second or two of combat. Expect ~90s, not
~120s.

**Done so far:** §6 (book-return payoff), §6b (level-complete sequence), the
painted title screen, **warrior select** (§8) with Elad and Roni and their two
weapons, and **Emri** built but parked for §9's boss level. §5 (lockers) is
still the natural next step; it gives §6's burst a real place to happen.

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

## 2. ⬜ Add more monsters
Currently 2 ranged casters. Add variety in *behavior*, not just stats.

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

## 5. ⬜ Return the book to the room's locker — and clear the room first
Every classroom gets a **locker** (the delivery point) and a **resident guardian**.
You can't deliver the book until that room's monster is dead — so each return is
*earned* with a fight, not just a walk.

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
- Point the §6 effect at the locker: `_on_book_returned` (`play_state.py`) passes
  `self.player.pos` to `effects.book_returned()` today — swap it for the locker's
  center and the sparkles + flying book land on the objective instead of on you.

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
**Done.** Returning a book was silent and invisible — the counter just ticked.
It now lands as the payoff beat of the loop: a chime, a burst of sparkles, the
room flushing to its own color, and the HUD counter glowing.

**What shipped**
- **Success chime** — `_synth_success()` + `AudioSystem.play_success()`
  (`systems/audio.py`). A rising E–A–E triangle-wave arpeggio, **0.39s** against
  the victory fanfare's **1.24s**, and softer (triangle, not square), so the two
  moments never blur. Goes through `_get_sfx`, so dropping
  `assets/sfx/success.wav` (or `.ogg`) overrides the synth with no code change.
- **`systems/effects.py`** (new) — a tiny cosmetic pool: `_Sparkle` (26 outward,
  gravity-pulled dots, half the room's color and half warm white) and
  `_RisingBook` (the returned book drawn floating up and fading out). Drawn with
  primitives, no assets. `Effects.book_returned(pos, color)` fires both.
- **Room tint pulse** — the classroom flushes to its own color and fades back
  over `BOOK_TINT_TIME`, on top of the existing static tint.
- **HUD counter glow** — a gold halo expands and fades behind the book counter,
  and the count text washes toward gold (`HUD.draw(..., flashes=…)`).
- **Camera shake** on the return, reusing `camera.shake()`.
- All of it hangs off `Events.BOOK_RETURNED` as planned — `_on_book_returned`
  in `PlayState`. Nothing new needed plumbing.
- Tunables live in `settings.py` under *Book-return payoff*:
  `BOOK_FLASH_TIME`, `BOOK_TINT_TIME`, `BOOK_TINT_ALPHA`, `BOOK_SHAKE_MAG`,
  `BOOK_SHAKE_TIME`.

**Two things worth knowing**
- ⚠️ **The burst spawns at the player, not at a shelf**, because there is no
  shelf yet. When §5 lands, the one-line change is to pass the locker's position
  to `effects.book_returned()` — then the sparkles and the flying book resolve
  *at the objective*, which is where they always wanted to be.
- Fixed a latent leak found while wiring this up: the `EventBus` lives on `Game`
  and outlives a run, but `PlayState` and `QuestManager` subscribed without ever
  unsubscribing, so every restart stacked another live listener. `PlayState.exit()`
  now unsubscribes and calls the new `QuestManager.dispose()`. Without it the
  chime would have played twice on a second run.

**Tuning notes from the first pass** (kept in case the numbers get revisited)
- 1px sparkles read as *noise* at 640×360 — they need 2–4px.
- Fading a particle linearly to black makes it look like dirt on a dim floor for
  most of its life. They now hold full brightness and dim only over the last 45%.
- The room pulse started at alpha 95 and flooded the screen; 68 reads as a pulse
  rather than a flash. This is the §1 "dark environment, bright actors" rule
  biting early — the payoff has to be legible without washing the room out.

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

## 8. 🔶 Playable warriors — pick who goes into the school
**Done: the roster, the select screen, and two warriors.** A "Select your
Warrior" row on the title menu opens a one-page-per-character screen (portrait,
blurb, stat card, power) — one page rather than a row of cards, because at
640×360 a card carrying all four of those does not survive being shrunk to a
third of the screen.

| Warrior | Plays like | Power |
|---|---|---|
| **Elad — The Knight** (default) | reach 52, 100 HP, speed 165 | *Steadfast*: none. The longest reach and deepest health bar in the game. |
| **Roni — The Warrior Princess** | reach 38, 85 HP, speed 196 | *Royal Bond*: **[Z]** send Zina. She flies out, bites once — an **instant kill** — and returns. **3 per level.** |

**How a warrior is defined.** `entities/warriors.py` is pure data: the sprite
prefix to animate, the numbers the simulation reads, and an optional power id.
`Player` reads them; there is no subclass per character, so a third warrior is a
dict plus four extracted poses.

**⚠️ The card stats are flavour; the play stats are real.** Each entry carries
its painted `card` (HP/ATK/DEF/SPD) *and* separate `speed` / `max_health` /
`reach` that actually drive the game. This is the §7 trap handled deliberately
rather than by accident — but it means the two can drift. Keep them consistent
in spirit: Roni's SPD 22 is *why* she is the fast one, Elad's reach is *why* his
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
- **Elad — Longsword.** Two pips a swing, reach 52. The sword now actually hits
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
| Elad, longsword | 2 | 0.36s | **5.6** | reach 52 — inside a caster's kite range |
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
- ⬜ **Elad's "power" is the absence of one.** Steadfast is honest but flat next
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

## Testing

`pytest` suite in `tests/`, ~290 tests, headless and a few seconds to run — see
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

## 9. ⬜ Boss level — the duel with Emri in the hidden classroom
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

---

_Update this file as items progress; see `docs/vidadiyot_game_design.md` for the
original concept and `README.md` for how to run._
