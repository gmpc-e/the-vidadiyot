# Prompt pack — Phase 2: things that move

Phase 1 (`ART_PROMPTS.md`) was the map: floors, walls, doors, item icons. Phase 2
is **animation** — the frames the game has never had.

Worth knowing before you commission any of it: today **nothing in the game is
truly animated.** Each warrior has four *single* painted poses (idle, walk,
attack, hurt) and the walk cycle is faked in code — a two-step bob paired with a
4% vertical squash on the off-beat (`entities/player.py`). It reads as a gait
from ten feet away and falls apart the moment you look at it. Monsters have one
frame each and bob on a sine wave. Every projectile and every effect is drawn
with code primitives — circles, arcs, particles.

So this phase is not polish on top of animation. It is the animation.

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
> **Presentation:** pure black (#000000) background. No scene, no vignette, no
> floor beneath the subject, no gradient, no border, no frame. **No text, no
> labels, no captions, no frame numbers, no watermarks, no UI panels.**
> Output at 1536×1024, landscape.

---

## §A The animation rules — read once, they apply to every sheet below

**Registration is the whole game.** If the subject shifts or changes size between
frames, the animation jitters when played, and there is no fixing that
afterwards — not in the extractor, not in code. Every strip prompt below repeats
the registration clause on purpose. Do not trim it out to save space.

Append this to every sheet request:

> **Layout:** a single horizontal row of N frames, evenly spaced, with a wide
> pure-black gutter between frames and nothing touching. **The subject must be at
> exactly the same size, in exactly the same position within its frame, from
> exactly the same camera angle in every frame** — identical framing, identical
> scale, identical distance. Only the named detail changes from frame to frame.
> The subject's feet (or base) must sit on the same horizontal line in all
> frames. No text, no numbers, no borders, no separating lines.

Four more rules the code imposes:

| Rule | Why |
|---|---|
| **Four frames maximum per strip** | The game plays these at ~8fps; more frames buy nothing at 48px tall. Four also keeps each cell ~380px wide on a 1536px sheet, which is enough resolution to downscale from. |
| **One strip per image** | Two strips on one sheet drift in scale against each other, and then the character changes size when it stops walking. |
| **Everything faces screen-right** | `player.py` mirrors the sprite for leftward movement. Art painted facing left comes out backwards half the time. Monsters are the exception — they never mirror, so paint them facing the viewer. |
| **Paint big, downscale in the tool** | Same as Phase 1. Never draw at final pixel size. |

**Final in-game sizes**, so scale and detail budget are honest — these are what
the extractors output today:

| Subject | Final size |
|---|---|
| Elad / Roni (warriors) | ~44 × 48 px |
| Little Snir | 33 × 54 px |
| Little Terror | 44 × 54 px |
| Emri (boss) | 41 × 58 px |
| Zina (dog) | 28 × 34 px |
| Thrown knife | 34 × 11 px |

A 48px-tall character holds about three readable shapes. Faces do not survive;
silhouette and colour do.

---

# Priority 1 — the frames the game is faking today

## Sheet 1 — Elad's walk cycle (4 frames)

> A four-frame walk cycle of a boy knight, seen from the side, facing screen
> right, walking in place: a young knight in dented plate armour over a deep
> purple tunic, carrying a longsword. Frame 1 contact pose with the left leg
> forward, frame 2 passing pose with the legs together and the body at its
> highest, frame 3 contact pose with the right leg forward, frame 4 passing pose
> again with the opposite arm leading. The sword stays held in the same hand
> throughout. The armour and tunic stay bright and saturated.

Then paste the §A layout clause.

## Sheet 2 — Roni's walk cycle (4 frames)

> A four-frame walk cycle of a girl adventurer, seen from the side, facing screen
> right, walking in place: a girl in a hooded travelling cloak with a bandolier of
> throwing knives across her chest. Frame 1 contact pose with the left leg
> forward, frame 2 passing pose with the legs together and the body at its
> highest, frame 3 contact pose with the right leg forward, frame 4 passing pose
> with the opposite arm leading. The cloak hem swings slightly behind her,
> trailing the step. Bright and saturated.

## Sheet 3 — Elad's sword swing (4 frames)

The one attack that isn't a projectile, and the one the player sees most.

> A four-frame attack animation of a boy knight in dented plate armour swinging a
> longsword, seen from the side, facing screen right, standing in place. Frame 1
> the wind-up with the sword drawn back over the shoulder and the weight on the
> back foot; frame 2 the sword at the top of its arc; frame 3 the strike, the
> blade swept fully forward and down in front of him with the body leaning into
> it; frame 4 the recovery, the blade low and the knight settling back upright.
> His feet stay on the same spot in all four frames.

## Sheet 4 — Roni's knife throw (4 frames)

> A four-frame throwing animation of a girl in a hooded cloak throwing a knife,
> seen from the side, facing screen right, standing in place. Frame 1 she draws a
> knife from the bandolier across her chest; frame 2 the arm cocked back beside
> her head; frame 3 the arm snapped forward at full extension with the hand open
> and empty, the knife already gone; frame 4 the follow-through, shoulder
> dropped, returning to a ready stance. Her feet stay on the same spot in all
> four frames. **Do not paint the thrown knife in flight** — the game draws it.

## Sheet 5 — Little Terror winding up a fireball (4 frames)

⚠️ **This is a gameplay change, not decoration.** Casters currently give the
player no warning — a fireball simply exists. A visible wind-up is the tell that
makes a ranged fight fair, so it is the highest-value sheet in this pack.

> A four-frame casting animation of a small cartoon fire monster, seen from the
> front facing the viewer, standing in place: a squat imp-like creature with a
> round body, big glowing eyes and stubby arms. Frame 1 idle with its arms down
> and its eyes dim; frame 2 it hunches, both arms drawn in toward its chest, a
> small ember of purple-and-orange fire igniting between its hands, eyes
> brightening; frame 3 the ember swollen into a fierce fireball at full size, the
> creature leaning back, its eyes blazing; frame 4 arms flung forward, the
> fireball released and gone, the creature open-armed and its eyes dimming again.
> **Do not paint the fireball travelling away** — the game draws the projectile.
> The fire is the bright element; the creature's body stays a muted purple-grey.

## Sheet 6 — Little Snir winding up a web (4 frames)

> A four-frame casting animation of a small cartoon spider monster, seen from the
> front facing the viewer, standing in place: a round dark-bodied creature with
> too many thin legs and pale glassy eyes. Frame 1 idle, legs settled; frame 2 it
> rears up, forelegs raised, pale silk gathering into a small tangle between
> them; frame 3 the tangle swollen into a dense white ball of web at full size,
> the body arched back; frame 4 forelegs thrown forward, the web gone, the body
> low and spent. **Do not paint the web travelling away.** The silk is the bright
> element; the body stays near-black.

---

# Priority 2 — the beats that currently have no art at all

## Sheet 7 — Monster defeat puff (4 frames)

Killing something is the core verb and it currently has no visual. One neutral
strip covers every monster: the game tints and scales it.

> A four-frame dissipation effect on a pure black background, no creature in it —
> only the smoke. Frame 1 a small tight puff of pale grey dust just beginning to
> bloom; frame 2 the cloud expanded to full size, ragged and billowing, with a
> few dark specks flung outward; frame 3 the cloud thinning and spreading wider,
> beginning to break apart; frame 4 the last torn wisps, almost transparent. The
> cloud stays centred in exactly the same spot in every frame and only grows and
> fades. Neutral pale grey and off-white so it can be recoloured.

## Sheet 8 — Emri materialising (4 frames)

For the boss duel. The game currently fades one sprite in and out on alpha, which
is why the blink reads as a bug rather than a threat.

> A four-frame materialisation of a tall shadow creature, seen from the front
> facing the viewer, standing in place: a gaunt figure made of darkness with pale
> burning eyes and long thin limbs. Frame 1 barely there — only a faint vertical
> smear of darker air and two dim points of light where the eyes will be; frame 2
> half-formed, the silhouette readable but ragged and smoking at the edges,
> streaming upward; frame 3 almost solid, edges still fraying, eyes bright; frame
> 4 fully present, solid and sharp, eyes at their brightest. The figure occupies
> exactly the same position and height in all four frames — it does not rise,
> grow or drift, it only condenses. Played backwards this must also read as
> vanishing, so keep the change purely in density and edge, never in pose.

## Sheet 9 — Projectiles in flight (4 frames, one strip each)

Three separate images, one per projectile. All three are code primitives today.

> **Fireball** — a four-frame loop of a flying ball of purple and orange flame
> travelling screen right, seen from the side. The flame licks and churns and the
> trailing tail whips, but the ball's centre stays in exactly the same spot in
> every frame at exactly the same size. Bright, saturated, hot core.

> **Web ball** — a four-frame loop of a flying tangled ball of white spider silk,
> loose strands trailing behind it. The strands writhe between frames; the ball's
> centre and size never move. Bright pale silk against black.

> **Lightning bolt** — a four-frame loop of a jagged bolt of pale blue-white
> energy travelling screen right, crackling. The bolt's overall length, angle and
> position stay identical in every frame; only the branching forks change.

## Sheet 10 — The book coming home (4 frames)

The payoff beat of the whole loop (roadmap §6). Sparkles are code particles
today, which is fine, but a real flare would land it.

> A four-frame burst effect on a pure black background: a ring of light expanding
> outward. Frame 1 a small bright point with a tight ring just forming; frame 2
> the ring expanded and thick, with radiating spokes of light and a scatter of
> star-shaped sparks; frame 3 the ring wider, thinner and dimmer, the sparks
> flung further out; frame 4 the last faint ring and a few drifting motes. The
> burst stays centred on exactly the same point in every frame. Paint it in
> **neutral white and pale gold** — the game recolours it to the classroom's
> colour.

---

# Priority 3 — ambience, whenever

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

Worth knowing that the art is the larger half but not the only half. None of
this plays today:

- **`Player.set_frames()` takes exactly four single Surfaces** and fakes the walk
  cycle. It needs a small frame-list animator, and `spritelib` needs to slice a
  strip into frames on an even grid.
- **`Monster.draw()` has no animation clock at all** — one sprite and a sine bob.
  Casting frames also need hooking to the existing cast timer so the wind-up
  actually lines up with the shot, which is the entire point of sheet 5.
- **Projectiles and effects draw with primitives**, so each one becomes a sprite
  swap plus a frame clock.
- **`Blinker`'s appear/vanish is an alpha ramp** over the retuned 1.30s telegraph;
  sheet 8 replaces the ramp with real frames.

None of it is large, but it is the difference between the sheets sitting in
`~/Downloads` and the game moving.
