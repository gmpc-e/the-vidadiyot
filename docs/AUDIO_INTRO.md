# Audio book — the intro

One two-minute cue and nine effects. Companion to `INTRO_SCRIPT.md`; the same
rules as `AUDIO_BOOK.md` apply except where this file says otherwise, and where
it says otherwise it is because **the intro is the one piece of music in this
game that is not a loop.**

**Where it goes:** `~/Downloads/the-vidadiyot/audio/`, then:

```bash
./venv/bin/python tools/import_audio.py --list   # what it will do
./venv/bin/python tools/import_audio.py          # transcode into assets/
```

---

## §X0 The three rules that are different here

**1. ⚠️ It must not be trimmed.** `import_audio.py` cuts the tail off any music
file that ends below 25% of its own body level, because a loop that fades to
silence dies and snaps back every two minutes. The intro cue is the opposite
case: it is *supposed* to resolve and fade, straight into the title screen. So
`intro` is declared in **`NO_LOOP`** in `tools/import_audio.py` and keeps its
ending.

> That set exists now because of this cue, but the bug it fixes is older:
> `victory` and `defeat` are also one-shot music and have been going through the
> loop trim since they landed. Both are in `NO_LOOP` too.

**2. Vocals are allowed here, and nowhere else.** `AUDIO_BOOK.md` bans them
outright, correctly: a voice in a loop you hear for twenty minutes becomes the
thing you turn off. This cue plays once. **A wordless child's voice in the
middle section is permitted and encouraged** — no words, no language, just tone.
Nothing that sounds like a lyric.

**3. Length is a target, not a contract.** See below.

### ⚠️ Deliver the music first, then time the picture to it

Suno will not put a section boundary at 1:08 because a document asked it to. It
returns something close to two minutes with the right sections in the right
order and the seams a few seconds from where you wanted them.

**That is fine, and the intro is built for it.** `INTRO_SCRIPT.md`'s beat sheet
is two flat tables of numbers; retiming to the delivered cue is an edit to those
tables. So the working order is:

1. Generate the cue. Take the best of three or four rolls.
2. Listen with a stopwatch and write down where the sections *actually* change.
3. Move the beat boundaries to those numbers.
4. Only then request the art, which does not care about timing at all.

**Aim for 60 BPM**, one beat per second, four seconds to the bar. That is
TikTak's tempo — his name is the sound — and it is why every beat boundary in
the script is a multiple of four seconds. If the cue lands near 60, every cut in
the intro falls on a bar line for nothing.

### Generating it in Suno

Use **Custom mode** with **Instrumental on** (the wordless voice in §X1 comes
from the style description, not from the lyrics box — words in that box become
sung words). Two fields:

- **Style** — the short line under each prompt below. Suno's style field is
  small; long prose gets truncated from the end, so the important words go first.
- **Lyrics box** — the bracketed structure tags. Suno honours section tags even
  on an instrumental, and it is the only reliable handle on where a change
  happens.

---

# Music

## §X1 The intro cue — ✅ request this one

Two minutes, through-composed, five sections. It carries the whole sequence, so
it is the only piece of audio in this project that is allowed to *build*.

**Style field:**

```
spooky playful orchestral storybook score, celesta, music box, pizzicato
strings, tack piano, low woodwind, bowed vibraphone, ticking clock percussion,
minor key, 60 bpm, cinematic, no drums, Luigi's Mansion, Costume Quest
```

**Lyrics box (structure only):**

```
[Intro - sparse night forest, music box alone]
[Verse - a dark building appears, low drone enters]
[Break - almost silence, a single ticking clock]
[Verse 2 - urgent, pizzicato strings, a frightened child]
[Bridge - the villain, ticking loud, wordless voices]
[Outro - brave and rising, resolves, ends warm]
```

> An instrumental score for the opening cutscene of a children's horror-lite
> game set in an abandoned school at night. Spooky and playful — Luigi's Mansion
> or Costume Quest, never frightening. Minor key, about 60 beats per minute, two
> minutes long, ending on a clean resolved chord.
>
> It moves through five moods without a break. It opens sparse and lonely: a
> music box and a single low sustained note, wide gaps of near-silence, a night
> forest — a distant owl and one settling branch worked into the space. After
> about a quarter of a minute a low drone slides underneath and a slightly
> out-of-tune tack piano picks out a slow figure: something is wrong. The music
> then falls almost entirely away to leave a single dry ticking clock, alone,
> for several seconds.
>
> Out of that silence the pace lifts into hurried pizzicato strings and anxious
> celesta — someone is running, someone is frightened and telling you something
> quickly. It builds, then lands hard on the villain: the ticking returns much
> louder and takes over the rhythm, joined by muted low brass, a detuned
> music-box motif and a soft wordless children's choir humming in the
> background, no words and no language.
>
> Finally it turns. The ticking is pushed under, the strings find a warm rising
> line, and the last twenty seconds are brave and determined rather than
> triumphant — small heroes deciding to go in — resolving to a clear final chord
> that rings and fades naturally.
>
> No drums, no modern production, no synth pads, no electric guitar, no sung
> words. Leave headroom.

⚠️ **The ticking is the load-bearing element.** It is TikTak, it is the tempo,
and it is the sound the duel track (§M5) is already built on. If a roll comes
back with a lovely arc and no clock in it, re-roll — that one detail ties the
intro to the boss fight the campaign is pointed at.

## §X2 Plan B — two stems instead of one cue

Only if §X1 keeps returning a good two minutes with the *wrong shape* — the
usual failure being an arc that peaks in the wrong place. Two shorter pieces
crossfaded at the one cut that matters (the villain reveal) is easier to land
and easier to retime, at the cost of one seam.

> **`intro_a`** — a slow, sparse, lonely instrumental for walking through a night
> forest toward an abandoned building. Music box and one low sustained note, long
> gaps of near-silence, a distant owl. Grows uneasy in its second half as a low
> drone and a detuned tack piano come in, and ends by thinning out to almost
> nothing over a single dry ticking clock. Minor key, 60 bpm, about 70 seconds,
> no drums, no vocals, ends quiet but not silent.

> **`intro_b`** — a short instrumental that opens on a loud dry ticking clock and
> muted low brass, tense and theatrical for a storybook villain, then turns after
> about fifteen seconds into a warm, rising, determined line for small heroes
> walking toward danger. Ends on a clear resolved chord that rings and fades.
> Minor key turning hopeful, 60 bpm, about 55 seconds, no drums, no vocals.

## §X3 TikTak's tick — the motif on its own

Worth having whether or not it is used in the intro, because the moment TikTak
becomes a real boss this is his arrival.

> A single dry mechanical clock tick, close-mic'd in a small hard room, with a
> faint brassy ring after it. No reverb tail, no music, no pitch. One tick only.
> 0.25s.

**Cap 0.9s** — it fires once per second under beat 3 and again under the three
names in beat 6. Anything near a second overlaps the next tick.

---

# Sound effects

Nine files. Same rules as `AUDIO_BOOK.md`: WAV, 48kHz stereo, dry, tails
trimmed, and **the length after each prompt is a ceiling, not a preference** —
each one has a slot in the script and a clip longer than its slot overlaps
itself or the next line.

### 1. `intro_gate` — the girl gets out

> A heavy rusted iron gate flung open hard: a sharp metallic clang, a rattle of
> chain, and a squeal of a dry hinge swinging on afterwards. Outdoors, a little
> distant, no reverb tail. 0.8s.

**Cap 2.0s** — the only sound in its second.

### 2. `intro_run` — she reaches them

> The light, quick footsteps of a running child on gravel and dead leaves,
> getting closer and stopping short. About eight fast steps. Dry, close, no
> music, no breathing. 1.5s.

**Cap 3.5s** — it covers her run across the plate and must be over before she
speaks.

### 3. `tiktak_reveal` — his name

The four seconds his name is on screen, alone. The one place in the intro where
a sound is allowed to be big.

> A slow, wrong music-box phrase of four notes winding down and going flat, over
> a deep brass swell and a hard mechanical clock tick that lands on the last
> note. Theatrical and sinister but not a jump-scare — no screech, no impact
> boom, no scream. 3.0s.

**Cap 4.0s** — the card holds four seconds and nothing else plays under it.

### 4. `transform` — the friends changing

> Something soft and living being stretched and re-made: a low sliding groan
> pitching upward, a wet fibrous crackle, and a dull hollow pop at the end.
> Strange and sad rather than gory — no bones, no tearing, no screaming. 1.2s.

**Cap 2.5s** — it plays once on the dissolve into the triptych, 1.5s before the
next card.

### 5. `book_swarm` — every book in the school

> A great rush of paper moving fast: dozens of hardback books flying past
> together, covers thumping, hundreds of loose pages fluttering, receding into
> the distance. Airy and papery, no wind howl, no musical tone. 2.5s.

**Cap 4.0s** — it runs under the plate's own beat and must be gone before the
rule card.

### 6–8. `girl_talk`, `roni_talk`, `wallad_talk` — the talking blips

Sixteen dialogue cards and no voice acting. The cheap, old and genuinely good
answer is a **text blip**: one tiny sound per few characters as the line types
on, pitched per character. Three small files make the whole intro feel spoken.

⚠️ **These ride the machinery that already exists.** `AudioSystem.play_voiced`
refuses to start a clip that is still playing, so a blip fired every 55ms simply
skips when it would overlap — no cooldown, no channel management, no new code.
The call is `play_voiced("girl", "talk")`, and the files are named
`girl_talk.wav` to match the voice-pack convention the teachers established.

> **`girl_talk`** — one very short, soft, breathy vocal blip from a young girl.
> A single unpitched syllable, close, dry, no words, no melody, no reverb. It
> will be repeated many times a second, so it must be tiny and unobtrusive.
> 0.06s.

> **`roni_talk`** — the same blip, from an older girl: a fraction lower, calmer
> and rounder. 0.06s.

> **`wallad_talk`** — the same blip, from a grown man: low, quiet, gruff, still
> a single soft syllable. 0.06s.

**Cap 0.08s each, and this one is hard.** A blip is a `Sound` and a `Sound`
holds one of pygame's eight mixer channels for its entire length; at 0.06s
against a 55ms interval one is retiring as the next starts. At 0.3s you have
starved the mixer of five channels for a sentence.

### 9. `intro_drip` — optional

Only if §X1 comes back without a drip in its third section. The script wants one
at t=30, in the eight seconds of near-silence.

> A single drop of water falling into a shallow puddle in a large empty room:
> one clean plink with a short natural echo. Cold and lonely. 0.5s.

**Cap 1.5s.**

---

## Already in the game — do not request these

The intro uses four sounds that already exist. That is deliberate: a sound the
player meets in the intro and again in the school is a sound that means
something the second time.

| | used for |
|---|---|
| `zina_bark` | Roni's last line — "Neither are we." |
| `pickup` | under the rule card, "Every book home…" |
| `monster` | optional, under the transformation |
| `emri_blink` | optional, under Emri's silhouette in the triptych |

---

## Before you send the batch back

- [ ] WAV, 48kHz stereo, no pre-compression
- [ ] The cue **resolves and fades naturally** — and `intro` is in `NO_LOOP`,
      so that ending survives the import
- [ ] No sung words anywhere; the wordless choir in §X1 is the only voice
- [ ] Effects dry, tails trimmed, every one inside its cap
- [ ] The three talk blips are **under 0.08s** — check this one with a waveform,
      not by ear
- [ ] Filenames match the stems in `TRACKS` (`tools/import_audio.py`)
- [ ] Dropped in `~/Downloads/the-vidadiyot/audio/`
