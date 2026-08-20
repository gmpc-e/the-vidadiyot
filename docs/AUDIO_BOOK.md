# Audio book — what to generate, and how to hand it over

Prompts for every piece of sound the game needs. Same shape as
`ART_PROMPTS.md`: a style block that rides on every request, then one prompt per
item.

**Where it goes:** `~/Downloads/the-vidadiyot/audio/`. Then:

```bash
./venv/bin/python tools/import_audio.py --list   # what it will do
./venv/bin/python tools/import_audio.py          # transcode into assets/
```

That transcodes to Ogg Vorbis and files it. The delivered menu track went from
**39.9MB to 2.9MB** — worth knowing, because the whole rest of the source tree is
about 1.5MB, so raw WAVs cannot be committed.

---

## §0 The rules the audio has to live inside

| | |
|---|---|
| Deliver as | **WAV, 48kHz stereo** — the tool compresses; don't pre-compress |
| Music length | 1–3 minutes, **seamlessly loopable** |
| Effects length | under 1.5s, most under 0.5s |
| Filename | must match a stem in `TRACKS` (`tools/import_audio.py`) or it is skipped |
| Loudness | **leave headroom.** Music plays at 35% under the effects |

**Loops must actually loop.** No fade-in, no fade-out, no silence at either end
— the file restarts the instant it ends, so a fade reads as the music dying every
two minutes. If the generator insists on a tail, say so and it gets trimmed.

**No vocals in the loops.** There is no dialogue in this game and a voice in a
two-minute loop becomes the thing you hear, then the thing you notice, then the
thing you turn off.

**Effects are dry.** A long reverb tail on a sword swing overlaps the next swing;
the game has no ducking. Short, close, and mono is fine.

---

## §1 Style block — paste this first, every time

> Instrumental score for a horror-lite 2D game set in an abandoned school at
> night. The register is Luigi's Mansion or Costume Quest — **spooky and playful,
> not frightening**; the audience is children. Dusty, decayed, slightly comic
> menace rather than dread. No screaming, no gore, no jump-scare stingers.
>
> **Palette:** celesta, toy piano, pizzicato strings, muted low brass, bowed
> vibraphone, brushed drums, a tack piano slightly out of tune. Low woodwind for
> weight. Occasional music-box. Nothing modern — no synth pads, no EDM drums, no
> electric guitar.
>
> **Feel:** minor key, waltz or loping triple time where it fits, plenty of space
> between notes. Quiet and patient rather than busy. **No vocals.**

---

# Music

⚠️ **`victory` and `defeat` are both requested by the game already** and neither
exists, so both screens keep playing the level track underneath. That is not a
crash — `play_music` deliberately leaves the music alone rather than cutting to
silence — but the victory banner currently celebrates over the level's own
soundtrack, which is the single most noticeable gap in the game's audio.


## §M1 Menu theme — ✅ delivered

`main_menu.wav` → `assets/music/menu.ogg`. Kept here as the reference the rest
should sit beside.

## §M2 Level one — the school at night — ✅ delivered

The bed for almost all play time, so it has to survive being heard for minutes on
end without pulling attention off a fight.

> A slow, sparse, looping instrumental for exploring a dark abandoned school.
> Music-box melody over a soft low drone, with long gaps of near-silence.
> Occasional distant creaks of a settling building and a faint dripping pipe
> worked into the rhythm. Patient and unhurried — this plays for minutes at a
> time under sound effects, so it must never build to a climax or demand
> attention. Minor key, very quiet, lots of space. No drums, no vocals.
> Seamless loop, 2–3 minutes.

## §M3 Victory — ✅ delivered

Pairs with the blood-drenched painted VICTORY! banner, so it is allowed to be
bigger and more gothic than the rest.

> A short triumphant flourish that turns just slightly sinister at the end.
> Church organ and low brass, a rolling timpani, a bright major resolution that
> lands on an unexpectedly dark final chord. Grand and a bit theatrical, like a
> curtain call in a haunted theatre. 20–30 seconds, no vocals. Does not need to
> loop.

## §M4 Defeat — ✅ delivered

> A short, deflating instrumental sting for losing. A music-box winding down and
> going out of tune as it slows, one low woodwind note underneath, ending on an
> unresolved chord. Sad and a little funny rather than harsh — nobody is being
> punished. 10–15 seconds, no vocals.

## §M5 Boss duel — Emri — ✅ delivered

For the hidden-classroom duel (roadmap §9). It is the only fight in the game
with a beat, and that is the point: everything else is patient, so this arriving
means something.

> A tense looping instrumental for a one-on-one boss fight in a dark classroom.
> Low pulsing strings, a ticking clock rhythm, bowed vibraphone stabs on the
> offbeat. Builds pressure through repetition rather than volume. Faster and more
> insistent than the rest of the score but still restrained — no orchestral
> bombast. Minor key, seamless loop, 1–2 minutes, no vocals.

---

# Sound effects

The five below already exist as **synthesized placeholders** in
`game/systems/audio.py`. Dropping a real file with the matching name overrides
the synth with no code change — so these are drop-in replacements, and each one's
prompt describes what the placeholder is already doing.

| deliver as | replaces |
|---|---|
| `monster.wav` | the growl when a monster first locks on |
| `success.wav` | the chime when a book goes into its locker |
| `zina_bark.wav` | Zina launching at a target |
| `zina_bite.wav` | Zina's kill |
| `level_done.wav` | the level-complete sting |

> **`monster`** — a short, wet, low growl from a small creature noticing you.
> Menacing but cartoonish, not a horror-film roar. Pitch bends downward. 0.6s.

> **`success`** — a bright, soft three-note rising chime, like a small bell or a
> celesta. Warm and satisfying, clearly a *reward*. Must not sound triumphant
> enough to be confused with the victory flourish. 0.5s.

> **`zina_bark`** — one sharp, bright dog bark from a small determined dog.
> Two syllables, close-mic'd, no reverb. 0.3s.

> **`zina_bite`** — a hard snap of teeth followed by a short low crunch. Sharp,
> not gory or wet. 0.3s.

> **`level_done`** — a rising three-note cheer that curdles into a low, detuned
> laugh. It marks the end of a *level*, not the run, so it must be recognisably
> its own thing. Slightly comic, definitely wrong. 1.5s.

## New effects — worth adding next

These need a `play()` call site as well as a file, since there is no synth
placeholder behind them. Ordered by how much they'd add.

**✅ delivered and wired:** `sword_swing`, `hit_flesh`, `knife_throw`,
`fire_cast`, `fire_hit`, `web_cast`, `door_unlock`, `pickup`, `potion`,
`player_hurt`, `monster_die`, `emri_blink`. Their prompts are kept below as the
record of what was asked for — do not re-send them.

### Voice packs — the better shape, adopted 2026-08-20

The teachers arrived as a **per-character set** rather than as variants of the
generic effects: `spotplayer` / `throw` / `hit` / `die`, one file each for the
female and the male. That is a better model than a flat name per event and the
game now supports it directly — `AudioSystem.play_voiced(voice, event, default)`
looks for `<voice>_<event>.ogg` and falls back when there is no take.

**Deliver a pack as `<voice>_<event>.wav`.** Any monster can have one; the voice
name is set on the monster (`teacher_f`, `teacher_m` today).

| event | when it plays |
|---|---|
| `spotplayer` | it first notices you — falls back to the generic growl |
| `throw` | it launches its attack — falls back to the projectile's cast sound |
| `hit` | it takes a blow — layered *over* `hit_flesh`, which is the weapon connecting |
| `die` | it dies — falls back to `monster_die` |

⚠️ **A voice never overlaps itself.** `teacher_f_hit` came in at 1.59s and a
sword swings every 0.36s, so a flurry of four hits would stack four copies of the
same yelp — the mistake `zina_bark` made at 1.85s against a 0.42s retrigger.
Rather than a cooldown per sound, `play_voiced` asks whether the clip is still
playing and skips it. **So a long take is safe here** — it just means the
character says less. The events with hard ceilings are the ones that *don't* go
through a voice.

⬜ **`teacher_f_spotplayer` is the one gap in the pair** — the male has one, the
female falls back to the generic growl, which is audibly a different character.

**⬜ Still missing, and every one of them already has a call site in the game**
(they are silent, not broken — `tests/test_systems.py::PENDING_AUDIO` is the
list, and it fails if this doc and the code disagree):

**Six effects and one voice line. Every prompt is below — copy the blockquote.**
Ordered by how much each one adds.

⚠️ **The lengths are not taste, they are ceilings.** Each of these fires on a
timer the game already runs, and a clip longer than its slot overlaps itself.
The number after each prompt is the cap and where it comes from.

### 1. `tome_hit` — the most valuable one left

A teacher's book landing on the player. The *throw* is voiced now, so their
attack starts loud and lands in silence — this is the missing half of the pair
that fire already has.

> A heavy old hardback slamming shut against something solid: a flat, dry slap of
> board on board, with a scatter of loose pages fluttering away after it. Papery
> and cold, no impact boom, no musical tone. Recorded close, in a room with hard
> walls. 0.35s.

**Cap 1.0s** — `TOME_CAST_CD` is 2.4s, so two teachers can land shots 1.2s apart.

### 2. `web_stuck` — being caught

> The moment of being wrapped: a wet, sticky rush of silk closing in around a
> body, ending muffled and close as if a blanket has been thrown over the
> microphone. Slightly comic, not horrifying. 0.5s.

**Cap 1.5s** — `WEB_CAST_CD` is 5.0s and the web holds you for several seconds.

### 3. `web_break` — mashing free

The release is the payoff of all that mashing, and right now it is silent.

> Dry fibrous strands tearing apart under force, three or four rips in quick
> succession, ending in a clean snap and a sense of open air. Satisfying. 0.4s.

**Cap 0.8s.**

### 4. `web_hit` — the web landing

> A ball of wet silk splattering against a surface: a soft, sticky slap with a
> spread of thin strands after it. Wet and light, over almost immediately. 0.2s.

**Cap 0.6s** — it plays the instant the projectile connects, just before
`web_stuck`, so it must be out of the way before that starts.

### 5. `locker_open` — the payoff of the whole level

> A battered steel locker door swinging open on a dry, complaining hinge, then a
> hardback book set down firmly on a metal shelf, then the door left standing
> open. Three distinct beats, mechanical and satisfying — this is the sound of
> finishing something. 0.8s.

**Cap 1.6s.**

### 6. `teacher_f_spotplayer` — the female teacher's missing line

The male teacher has one; she borrows the generic monster growl, which is
audibly a different character.

> An elderly woman noticing someone in her classroom and being *displeased*
> about it: a sharp indrawn breath through the nose and a low, disapproving hum,
> close-mic'd, no words and no melody. She is a teacher first and a monster
> second. Match the register of `teacher_m_spotplayer`. 1.0s.

**Cap 2.0s** — the scare cue has a 2.5s cooldown.

### 7. `tome_cast` — fallback only, lowest priority

Both teachers have their own `throw`, so this never plays today. Deliver it only
if a third tome-thrower ever appears without a voice pack.

> A heavy old hardback snapping open and being flung, with a dry rush of pages
> and a low hollow note under it, like a word spoken in an empty room. Papery
> and cold rather than fiery. 0.4s.

**Cap 0.5s** — `TOME_WINDUP` is 0.50s and this plays at the *start* of the
wind-up, so it should finish as the book leaves.

⚠️ **`emri_blink` came back at 2.91s** against a blink cycle of 4.55s at its
fastest — it is still playing through most of Emri's telegraph. It is wired and
usable, but a **0.5s** take is what the prompt below asks for and what the boss
level will want.

Two notes from wiring that batch, for whoever writes the next prompt:

- **A cast sound is capped by its cooldown, not by taste.** `CASTER_CAST_CD` is
  1.8s and `WEB_CAST_CD` is 5.0s, so anything under about a second is safe
  there. `pickup` and `hit_flesh` have no cooldown at all and must stay short.
- **Delivered effects arrive as 2.00s files holding 0.2s of sound.**
  `import_audio.py` trims the padding, because a `Sound` holds one of pygame's
  eight channels for its whole length — padding starves the mixer with silence.

> **`sword_swing`** — a short, heavy whoosh of a blade cutting air. Weighty, low,
> no metallic ring. 0.25s.

> **`hit_flesh`** — a dull, soft impact landing on a creature. Not gory: a thud
> with a little body to it. 0.2s.

> **`fire_cast`** — a small whoomph of flame igniting and being thrown. Airy,
> not explosive. 0.4s.

> **`fire_hit`** — a fireball bursting against something. A short crackle and
> scatter, no boom. 0.3s.

> **`web_cast`** — a wet, stringy launch of sticky silk. Slightly comic. 0.3s.

> **`door_unlock`** — an old iron key turning in a heavy lock, then the clunk of
> the bolt drawing back. Satisfying and mechanical. 0.6s.

> **`pickup`** — a light, bright tick for taking a key or a book off the floor.
> Small and dry. 0.15s.

> **`potion`** — a cork pulling free and a few quick gulps of thick liquid. 0.6s.

> **`player_hurt`** — a short winded grunt from a child in armour. Not a scream;
> the audience is children. 0.3s.

> **`monster_die`** — a small creature popping out of existence: a startled
> squeak and a soft puff of dust. Comic rather than violent — nothing in this
> game dies horribly. 0.5s.

> **`emri_blink`** — a cold, breathy rush of air as something arrives where it
> was not. Reversed-sounding, with a faint metallic shimmer. 0.5s.

---

## Before you send a batch back

- [ ] WAV, 48kHz stereo
- [ ] Music loops with **no fade at either end** and no silence
- [ ] No vocals anywhere
- [ ] Effects are dry and short, with the tail trimmed
- [ ] Nothing mastered to brickwall loudness — leave headroom
- [ ] Filenames match `TRACKS` in `tools/import_audio.py`
- [ ] Dropped in `~/Downloads/the-vidadiyot/audio/`
