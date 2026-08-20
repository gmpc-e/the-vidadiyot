# The intro — "Every Book Home"

The two minutes before the title menu. A cold open that answers four questions
and no others:

1. **Where am I?** An abandoned school, at night, and it is wrong.
2. **What do I want?** Every book back where it belongs.
3. **Who are these creatures?** *Your friends.* Snir, Tirosh and Emri were
   children this morning.
4. **Who did this?** **TikTak.**

Everything else is atmosphere, and atmosphere is most of the two minutes.

> **Companion docs.** `ART_PROMPTS_INTRO.md` is the art book (seven painted
> plates + one run cycle) and `AUDIO_INTRO.md` is the audio book (one
> through-composed cue + eight effects). Both are parsed by the tools —
> `art_request.py --phase 3` and `import_audio.py` — so they are runnable, not
> just readable.

---

## The cast

| | Who | Where the art comes from |
|---|---|---|
| **Wallad** | The knight. Says nine words in two minutes. | ✅ existing sprites + `knight_portrait.png` |
| **Roni** | The warrior princess. Asks the two questions that move the scene. | ✅ existing sprites + `roni_portrait.png` |
| **Zina** | Roni's dog. Has the last sound in the intro. | ✅ `zina.png`, `zina_bark.ogg` |
| **The girl** ⚠️ | The messenger. Carries the entire story. Placeholder name: **Yali**. | ⬜ new — art book §I3 |
| **Queen Maya** | Taken. Never speaks, never moves; she is the *reason*, not a character yet. | ⬜ new — §I4 |
| **TikTak** | The one who did it. Appears for four seconds and does not speak. | ⬜ new — §I5 |
| **Little Snir · Tirosh · Emri** | Her friends, changed. | ✅ existing game sprites, over new silhouettes (§I6) |

⚠️ **The girl's name is the one thing left to decide.** Every other name in this
game belongs to a real child, and "Yali" is a placeholder chosen so it doesn't
collide with the roster. It appears in exactly one place in the script and one
in the art book — swapping it is a two-line change. Do it before the art is
requested, because her portrait prompt describes her and a name changes how she
gets drawn.

### What the intro does to the existing lore

⚠️ **"Little Terror" is labelled *(Maya Tirosh)* in the bestiary table**
(ROADMAP §7) — that is the name on the delivered character sheet. The intro
splits that name in half: **Maya** is the Queen who was taken, **Tirosh** is the
friend who was changed. They cannot be the same person any more.

**Recommendation: the monster stays "Little Terror", and the bestiary's
parenthetical becomes *(Tirosh)*.** No asset renames — the sprites are
`terror_*.png` and stay that way; this is one string on one screen that does not
exist yet.

⚠️ **TikTak is not in the game and the intro must not pretend otherwise.** The
girl states the *campaign* goal — every book home, and beat TikTak's pack — and
level one delivers the first wing of the school and **Emri**, the first of the
three friends you catch up with. That is an honest promise: the intro never says
"tonight", and Emri's duel is a real ending for a level. TikTak is the boss the
campaign is now pointed at (see ROADMAP §11).

**TikTak's motif already exists.** His name is a clock, his head is a stopped
school clock, and he moves in ticks. The duel track (§M5) is already built on
"a ticking clock rhythm", and `props/clock.png` is already "stopped at a
sinister hour". Nothing has to be retrofitted — the intro just names what the
game has been doing.

---

## How it is made — the decision that sets the budget

**Painted plates with slow camera moves, and the game's own sprites walking on
top of them.**

The alternative — building the forest as a real tilemap and walking real actors
through it — costs an entire outdoor tileset (grass, path, trees, fence),
a second map, and scripted pathing. The roadmap already flags the outdoor
tileset as the most art-expensive thing on the list (§4), and it would buy
exactly one scene that is never played.

So: **seven paintings and one run cycle**, with the characters composited from
sprites the game already ships. That last part is not a saving, it is the point
— the three monsters in the intro are literally the three monsters you fight, at
the same size, in the same animation. A painted monster that doesn't match the
one in the classroom teaches the player the wrong face.

| Layer | Source | Moves how |
|---|---|---|
| Plate | painted, 1536×1024 | slow push-in or drift, 1.00 → 1.08 over the beat |
| Actors | **intro-scale poses, ~96px** (see below) | walk cycles at the game's own frame rate |
| Portrait bust | painted / existing | slides up from the bottom edge, 0.25s |
| Text card | drawn in engine | fade in 0.2s, hold, fade out 0.2s |
| Vignette + fog | one painted overlay (§I8) | drifts, alpha-cycles |

---

## ⚠️ The cast is cut at double size for the intro

**Proven on the first delivered plate (2026-08-21).** The game's walk cycles are
48px tall. Composited onto a 640×360 plate they are 13% of the screen height, and
against a forest whose foreground trees fill the frame the two heroes read as
insects — which defeats the one thing beat 1 has to do.

**`tools/extract_intro.py` cuts the same poses at ~96px** rather than reusing the
48px game sprites. That costs nothing and loses nothing: the source paintings are
~1500px and every sprite in this game is already a downscale of one, so a 96px
cut is *more* faithful than the 48px one, not a blow-up of it.

⚠️ **Do not scale the 48px game sprite up in code.** It is already the lossy end
of the pipeline; doubling it doubles the mush. Cut from the painting.

⚠️ **A plate must leave the bottom third walkable** for figures that size — see
§I0. The first plate put a fallen log and a boulder exactly where the heroes
walk in.

## ⚠️ The music is delivered first, and the picture follows it

Suno will not hit a mark at 1:08. It will return something *near* two minutes
with sections in roughly the right order, and the seams will be a second or
three off wherever they land.

**So the beat sheet below is a starting timetable, not a specification.** Deliver
`intro.wav`, listen to it with a stopwatch, then edit `BEATS` and `CARDS` to
match what actually arrived. Everything below is written to make that edit cheap:
two flat tables of numbers and no timing baked into any drawing code.

**The grid is 60 BPM — one tick per second, four seconds to the bar**, which is
TikTak's own tempo. Every beat boundary in the table is a multiple of four
seconds for that reason: if the delivered cue is anywhere near 60 BPM, the cuts
land on bar lines for free.

---

## The beat sheet

Nine beats, 120 seconds.

| # | In | Dur | Plate | What happens |
|---|---|---|---|---|
| 1 | 0:00 | 16s | §I1 forest | Two kids walking a moonlit path. Nothing is wrong yet. |
| 2 | 0:16 | 12s | §I2 the school | The trees end. The school is there. They stop. |
| 3 | 0:28 | 8s | §I2 (held) | **No words.** A window flickers. A pipe drips. The first tick. |
| 4 | 0:36 | 16s | §I2 (held) | The gate bangs. The girl runs out and reaches them. |
| 5 | 0:52 | 16s | §I4 Maya | What she is telling them, seen. |
| 6 | 1:08 | 16s | §I5 → §I6 | **TikTak.** Then the three friends changing. |
| 7 | 1:24 | 12s | §I7 the books | Every book in the school, leaving. The rule. |
| 8 | 1:36 | 12s | §I2 (return) | They turn and walk toward the door. |
| 9 | 1:48 | 12s | `ui/title.png` | The title arrives on the last chord. Hand off to the menu. |

**Beat 3 is the one to defend.** Eight seconds of a still building, a flickering
window and no text is what makes the girl's arrival land — and it is exactly the
beat that will feel "too long" when you are watching it for the twentieth time
while building it. It is not long for someone seeing it once.

**Beat 9 costs nothing and is the best transition in the sequence.** The intro's
last frame *is* the title screen, so the menu doesn't arrive — it is already
there. Reuses `ui/title.png` as delivered.

---

## The script

**Format rules**, and each is load-bearing at 640×360:

- **Two lines maximum, 40 characters maximum per line.** The HUD font renders
  about 45 characters across the screen; 40 leaves margin for a bust.
- **One card on screen at a time.** Never two.
- **A card holds for at least 3 seconds**, and longer for longer lines. The
  reading pace assumed is ~2.5 words/second, which is a comfortable seven-year-old
  reading aloud, not an adult skimming.
- **A speaker card carries a bust**; a narration card is centred and has none.

The whole script is **89 words**. At the pace above that is ~36 seconds of
reading spread across 120 seconds of runtime, and text is on screen about 63% of
the time. That ratio is the budget — if a card gets added later, one has to go.

---

### Beat 1 — the woods (0:00 – 0:16)

*Plate §I1. Black for the first 1.5s, then a slow fade up. Push-in 1.00 → 1.06.
Wallad and Roni enter from the left at t=2 walking right, Zina trotting behind.
Slow — 28px/s, tired, not marching. They are still walking when the beat ends.*

| t | | |
|---|---|---|
| 4.0 | *narration, 6s* | **The woods behind the school.**<br>**Long after anyone came here on purpose.** |

*Audio: owl, one branch settling, no music until 0:02.*

---

### Beat 2 — the school (0:16 – 0:28)

*Cut to plate §I2 through a 0.6s dip to black. The two walk three more steps and
stop at the gate. Push-in continues, 1.00 → 1.05 across beats 2–3 without a
reset — one continuous move over 20 seconds.*

| t | | |
|---|---|---|
| 17.5 | **WALLAD**, 5s | **Nobody's been in this school in years.** |
| 23.0 | **RONI**, 4.5s | **Then who left a light on?** |

⚠️ **The lit window in §I2 must be painted, and it must be the only warm thing
in the plate.** Roni's line points at it. If the plate comes back with three lit
windows or none, the line is nonsense — this is the one composition note in the
art book that is a script dependency.

---

### Beat 3 — something is wrong (0:28 – 0:36)

**No text. This is the beat the user asked for: *they stop, because something
feels wrong*.**

| t | |
|---|---|
| 28.0 | The lit window begins to flicker — the game's own `LAMP_PATTERN`, not an even blink. |
| 30.0 | A drip, off in the dark. |
| 32.0 | **The first tick.** One clock tick, close, louder than it should be. |
| 32.5 | Both warriors take a single step back — nudge the sprites 6px left over 0.8s, then idle. |
| 34.5 | The second tick. Nothing else. |

⚠️ **The tick is never explained here and must not be.** It is TikTak, four
beats before his name, and a child who notices that on the second watch is the
whole reason to build an intro at all.

---

### Beat 4 — the girl (0:36 – 0:52)

*Same plate. At t=36.5 the gate bangs open (`intro_gate`). The girl's sprite
enters from the school side at ~90px/s, running — the four-frame cycle from §I3
— and stops in front of the warriors at t≈40. Her bust slides up at t=40.*

| t | | |
|---|---|---|
| 40.0 | **GIRL**, 5.5s | **Help! Please — you have to help!** |
| 46.0 | **GIRL**, 5.5s | **He took her. He took the Queen.** |

*The warriors do not react in sprite. They have no "surprised" pose and inventing
one is a whole art request; stillness reads as stunned anyway.*

---

### Beat 5 — the Queen (0:52 – 1:08)

*Cross-dissolve (1.2s) to plate §I4 — Maya, held somewhere dark. This is a thing
being **told**, not a thing being seen: desaturate the plate a further 25% and
push in slowly. The girl's bust stays; she is still the one talking.*

| t | | |
|---|---|---|
| 53.0 | **GIRL**, 5s | **Queen Maya. She's still inside.** |
| 58.5 | **GIRL**, 5.5s | **He hid her somewhere in the school.** |
| 64.5 | **RONI**, 3s | **Who did?** |

**Roni's two words are the most important line in the script.** They exist so
that the next thing anyone hears is a name, alone, in silence.

---

### Beat 6 — TikTak, and the three (1:08 – 1:24)

*At t=68 the clock-face wipe (§I8): the plate is swept away by a sweeping minute
hand over 0.5s, with a hard tick on the cut. Plate §I5 — TikTak — arrives
against the dark school. He does not move. The music drops to almost nothing.*

| t | | |
|---|---|---|
| 69.0 | **GIRL**, 4s | **TikTak.** |

*One word. Held four seconds. Rendered at double size, centred, no bust.*

*t=73: dissolve to §I6, the three silhouettes.*

| t | | |
|---|---|---|
| 74.0 | **GIRL**, 5s | **He changed my friends into monsters.** |
| 79.0 | **GIRL**, 5s | **Little Snir. Tirosh. Emri.** |

⚠️ **The three names land on three ticks — 79.0, 80.5, 82.0 — and each one fades
the matching game sprite in over its silhouette.** Snir left, Tirosh centre,
Emri right, in the order they are named. This is the single most functional
moment in the intro: it is where the player learns the roster's faces, and it is
free, because those sprites already exist. Do not reorder the names without
reordering the plate.

---

### Beat 7 — the books (1:24 – 1:36)

*Dissolve to plate §I7 — shelves emptying, books streaming away into the dark.
Slow drift left to right; the movement is the books, not the camera.*

| t | | |
|---|---|---|
| 85.0 | **GIRL**, 5s | **And he took every book in the school.** |
| 90.5 | *narration, 5.5s* | **Every book home, and the Queen goes free.** |

**That second card is the game's objective and gets its own treatment** —
centred, no bust, held a half-second longer than anything else, with the book
pickup chime under it. It is the sentence a player should be able to repeat
after watching this once. It is also literally true of the loop that is already
built: three books, three lockers, and the level opens onto the boss.

---

### Beat 8 — we go in (1:36 – 1:48)

*Back to plate §I2, no dissolve — a hard cut, because the telling is over. The
warriors are facing the school now (`knight_walk_up_*`, `roni_walk_up_*`). The
girl's sprite stands where she stopped.*

| t | | |
|---|---|---|
| 97.0 | **WALLAD**, 4s | **Then we go in.** |
| 101.0 | **GIRL**, 4s | **He isn't alone in there.** |
| 105.0 | **RONI**, 3s | **Neither are we.** |

| t | |
|---|---|
| 106.5 | **`zina_bark`** — the existing sound, and the last thing said in the intro. |
| 107.0 | Both warriors start walking up, toward the door, and are still walking when the beat cuts. |

---

### Beat 9 — the title (1:48 – 2:00)

*Dissolve (1.5s) to `ui/title.png` + `ui/title_rule.png`, laid out exactly as
`MenuState` draws them, over black. No text, no menu rows. On the last chord,
hand off to the menu — which draws the same art in the same place, so the
transition is invisible.*

---

## Skipping, and watching it again

- **The first 1.5 seconds accept nothing.** `LevelCompleteState.CAN_SKIP_AT`
  exists for the same reason: a key still down from the last screen should not
  eat the thing it opens.
- **The first press jumps to beat 9** (the title), not out of the sequence. A
  kid who has seen it twice gets out in a second and a half, and still gets the
  chord and the clean hand-off instead of a lurch.
- **A press during beat 9, or Esc at any time, exits immediately** to the menu.
- **It plays once.** A flag next to the leaderboard (`scores._user_data_dir()`,
  the same per-profile directory) records that it has been seen.
- **"Story" joins the title menu** so it can be watched again on purpose. That
  is the right place for it: the bestiary (§7) is going in the same menu for the
  same reason — a kid who wants to look at the monsters should be able to.

---

# Appendix — what lands on the code side

Not built yet; this is the shape it should take. **Nothing here touches gameplay
code**, which is deliberate — the intro is a new state and a new tool, and it
should stay that way.

### `game/core/intro_state.py`

```python
class IntroState(State):
    draw_below = False
```

- **`BEATS`** — `(start, plate, move)` per beat. **`CARDS`** — `(t, speaker,
  lines, dur)`. Both module-level tables. Retiming to the delivered music is an
  edit to these two lists and nothing else. ⚠️ If a timing ends up computed
  inside `draw()`, that property is gone and retiming becomes archaeology.
- **`enter()`** calls `play_music("intro")`; the menu's own `enter()` switches to
  `menu` on hand-off, and `play_music` no-ops when the track is unchanged, so
  there is nothing to stop manually.
- **`exit()`** has nothing to unsubscribe: the intro subscribes to no
  `EventBus` topics. ⚠️ That is worth keeping true. The moment it listens for
  anything, it inherits the rule that bites every state — the bus lives on
  `Game` and outlives the state, so a handler left behind doubles on a replay.
- **Skip reads `inp.confirm or inp.attack or inp.interact`** — all three are
  already in `InputState.EDGE_FIELDS`, so **no new edge intent is needed** and
  the latching invariant is inherited rather than re-solved. ⚠️ If a dedicated
  "skip" intent is ever added instead, it must go in `EDGE_FIELDS` or it will be
  dropped on frames that run no sim step.

### `main.py`

```
intro seen?  no  -> push IntroState -> switch(MenuState)
             yes -> push MenuState
--intro / --no-intro force either path (dev; the boss level has --boss already)
```

### `tools/extract_intro.py`

Cuts the plates to 640×360 and the girl's run cycle to game scale. Same shape as
the existing extractors, same `spritelib` calls; ⚠️ the plates key with
**`MODE_RAMP`, not `MODE_FILL`** — they are full-bleed scenes with no black
background to flood-fill from, so `MODE_FILL` would eat into the painting.

### Tests worth having

The fixtures in this project **draw every frame** because a real share of the
defects are draw-only, and a cutscene is nothing *but* draw. So:

- Step the state through all 120 seconds at `FIXED_DT`, drawing every frame, and
  assert it never raises and hands off exactly once.
- Assert every card's text fits: `font.size(line)[0] <= 620` for every line of
  every card. This is the test that catches a rewrite that reads fine in the doc
  and overflows on screen.
- Assert `CARDS` is sorted by `t` and that no two cards overlap — the "one card
  at a time" rule, enforced rather than remembered.
- Assert every plate named in `BEATS` exists in `assets/`, so a missing painting
  fails a test instead of a black screen.
- Skip at t=0.5 does nothing; skip at t=5 jumps to the last beat; skip during
  the last beat exits.
