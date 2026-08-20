"""Bring delivered audio into the game as compressed, loop-ready assets.

Source: `~/Downloads/the-vidadiyot/audio/`. Tracks arrive from Suno as 48kHz
stereo WAV, which is the right thing to *deliver* and the wrong thing to ship:
the menu track alone is 40MB as a WAV against roughly 1.5MB for the entire rest
of the source tree. This transcodes to Ogg Vorbis, which brings that to a few MB
and is what `pygame.mixer.music` streams best.

Two things worth knowing before editing:

**The mapping is explicit.** A delivered file is only imported if `TRACKS` says
where it goes, because the name a track is generated under ("main_menu (2).wav")
is not the name the game asks for ("menu"). Unrecognised files are listed rather
than guessed at, so a new delivery tells you exactly what line to add.

**Music is not normalised here.** Loudness is handled in game by `MUSIC_VOLUME`,
which is one number to change rather than a re-encode. Effects *are* normalised,
because a quiet effect under loud music is the one mistake that is genuinely
annoying to fix later.

**Music fade-outs are trimmed, though.** Generators end a track by fading to
silence, which is correct for a song and wrong for a loop: the file restarts the
instant it ends, so the music dies away and then snaps back to full volume every
couple of minutes. The delivered level-one track ended at **1% of its own body
level**. `_fade_trim()` finds where the fade starts and cuts there, then applies
a 120ms taper so the seam doesn't click. A gentle *musical* taper is left alone
and only reported — the bar is deliberately set at "faded to near-silence", not
"quieter at the end".

Run:  ./venv/bin/python tools/import_audio.py [--list]
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.expanduser("~/Downloads/the-vidadiyot/audio")
MUSIC_OUT = os.path.join(ROOT, "assets", "music")
SFX_OUT = os.path.join(ROOT, "assets", "sfx")

# Vorbis quality. 4 is ~128kbps and transparent enough for a game loop playing
# under sound effects; the menu track lands around 3MB at this setting.
MUSIC_QUALITY = "4"
SFX_QUALITY = "5"

# Loop hygiene. A window this long is measured at each end and against the body.
LOOP_WINDOW = 0.4
# Below this fraction of the body level, the end is a fade-to-silence and gets
# cut. Above it, a quieter ending is a musical choice and is only reported —
# the menu track tapers to about half and should keep it.
LOOP_FADE_RATIO = 0.25
SEAM_TAPER = 0.12               # seconds of anti-click taper at each end

# Effects arrive padded: the delivered sword swing is 2.00s of file holding 0.28s
# of sound, and the bite is 2.00s holding 0.18s. That is not just untidy — a
# Sound occupies one of pygame's 8 mixer channels for its whole length, so a
# padded effect fired repeatedly (a sword swing *is* fired repeatedly) starves
# every other sound in the game while playing silence.
SFX_SILENCE = 0.03              # fraction of peak that still counts as sound
SFX_LEAD = 0.01                 # seconds kept before the first sound
SFX_TAIL = 0.08                 # ...and after the last, so decay isn't clipped

# delivered stem (lowercased, no extension) -> (kind, name the game asks for)
# The game's side of this contract: music names are passed to
# `AudioSystem.play_music()`, effect names are keys in `audio.SYNTHS`.
TRACKS = {
    "main_menu":   ("music", "menu"),
    "menu":        ("music", "menu"),
    "level_one":   ("music", "level_one"),
    "level_1":     ("music", "level_one"),
    "background":  ("music", "level_one"),
    "level_1_background_music": ("music", "level_one"),
    "level_one_background_music": ("music", "level_one"),
    "victory":     ("music", "victory"),
    "defeat":      ("music", "defeat"),
    # The boss duel's own track (§M5). Delivered under the level's naming, so it
    # needs an exact entry or the `level_1` alias would claim it for level one.
    "level_1_boss_background_music": ("music", "duel"),
    "boss":        ("music", "duel"),
    "duel":        ("music", "duel"),
    # The intro cue (docs/AUDIO_INTRO.md §X1) and the two-stem plan B (§X2).
    # ⚠️ All three are in NO_LOOP below — they are one-shots that end on a
    # resolve, and the loop trim would cut that ending off.
    "intro":       ("music", "intro"),
    "intro_a":     ("music", "intro_a"),
    "intro_b":     ("music", "intro_b"),
    # effects — these override the synths in `game/systems/audio.py` by name
    "monster":     ("sfx", "monster"),
    "success":     ("sfx", "success"),
    "zina_bark":   ("sfx", "zina_bark"),
    "zina_bite":   ("sfx", "zina_bite"),
    "level_done":  ("sfx", "level_done"),
    "hit_flesh":   ("sfx", "hit_flesh"),
    "hit_flash":   ("sfx", "hit_flesh"),   # delivered spelling; same sound
    # ...the caster/impact pair for each ranged monster, plus the one pickup
    # sound both keys and books share. `fire_cast` must be listed exactly: the
    # 'fireball' alias below does not match it, and the 'fire' prefix is too
    # greedy to add as an alias with `fire_hit` sitting next to it.
    "fire_cast":   ("sfx", "fire_cast"),
    "fire_hit":    ("sfx", "fire_hit"),
    "web_cast":    ("sfx", "web_cast"),
    "pickup":      ("sfx", "pickup"),
    "door_unlock": ("sfx", "door_unlock"),
    "potion":      ("sfx", "potion"),
    "player_hurt": ("sfx", "player_hurt"),
    "monster_die": ("sfx", "monster_die"),
    "emri_blink":  ("sfx", "emri_blink"),
    # Per-character **voice packs**: spot / throw / hit / die for one monster.
    # These are not variants of the generic effects, they replace them for the
    # character that owns them — see `AudioSystem.play_voiced`.
    "teacher_f_spotplayer": ("sfx", "teacher_f_spotplayer"),
    "teacher_f_throw":      ("sfx", "teacher_f_throw"),
    "teacher_f_throw1":     ("sfx", "teacher_f_throw"),   # delivered spelling
    "teacher_f_hit":        ("sfx", "teacher_f_hit"),
    "teacher_f_die":        ("sfx", "teacher_f_die"),
    "teacher_m_spotplayer": ("sfx", "teacher_m_spotplayer"),
    "teacher_m_throw":      ("sfx", "teacher_m_throw"),
    "teacher_m_hit":        ("sfx", "teacher_m_hit"),
    "teacher_m_die":        ("sfx", "teacher_m_die"),
    # The intro's own effects (docs/AUDIO_INTRO.md).
    "intro_gate":  ("sfx", "intro_gate"),
    "intro_run":   ("sfx", "intro_run"),
    "intro_drip":  ("sfx", "intro_drip"),
    "intro_tick":  ("sfx", "intro_tick"),
    "tiktak_tick": ("sfx", "intro_tick"),      # delivered spelling; same sound
    "tiktak_reveal": ("sfx", "tiktak_reveal"),
    "transform":   ("sfx", "transform"),
    "book_swarm":  ("sfx", "book_swarm"),
    # Talking blips, one per speaking character. Named as voice-pack takes so
    # they go through `play_voiced`, which already refuses to start a clip that
    # is still playing — which is exactly the behaviour a blip fired every 55ms
    # needs, and it costs no new code.
    "girl_talk":   ("sfx", "girl_talk"),
    "roni_talk":   ("sfx", "roni_talk"),
    "wallad_talk": ("sfx", "wallad_talk"),
}

# Music that is **not a loop** and therefore keeps its ending.
#
# `_fade_trim` exists because a looping track that fades to silence dies and
# snaps back to full volume every couple of minutes. One-shot music is the exact
# opposite case: the intro cue resolves into the title screen and the defeat
# sting is *supposed* to trail away, so trimming the fade removes the ending the
# prompt asked for. ⚠️ `victory` and `defeat` have been going through the loop
# trim since they landed, which was never right — they are one-shots too.
NO_LOOP = {"intro", "intro_a", "intro_b", "victory", "defeat"}


# Generators name a file after the prompt, not after the slot it fills:
# "Playful Wet Cartoon Monster Growl.wav" is the `monster` effect. Exact stems in
# TRACKS win; these substrings are tried afterwards, **most specific first**, and
# whatever matches is printed so a wrong guess is visible rather than silent.
ALIASES = [
    ("monster_death", ("sfx", "monster_die")),
    ("monster_die",   ("sfx", "monster_die")),
    ("growl",         ("sfx", "monster")),
    # ...and a plain "monster" last in this group, so a take named for the
    # creature rather than the sound still lands. Ordering is the whole contract
    # here: "monster_death" must be tried before "monster".
    ("monster",       ("sfx", "monster")),
    ("bark",          ("sfx", "zina_bark")),
    ("bite",          ("sfx", "zina_bite")),
    ("cheer",         ("sfx", "level_done")),
    ("thud",          ("sfx", "hit_flesh")),
    ("impact_against", ("sfx", "hit_flesh")),
    ("chime",         ("sfx", "success")),
    ("reward",        ("sfx", "success")),
    ("success",       ("sfx", "success")),
    ("level_complete", ("sfx", "level_done")),
    ("sword",         ("sfx", "sword_swing")),
    ("knife",         ("sfx", "knife_throw")),
    ("fireball",      ("sfx", "fire_cast")),
    ("web",           ("sfx", "web_cast")),
    ("unlock",        ("sfx", "door_unlock")),
    ("locker",        ("sfx", "locker_open")),
    ("potion",        ("sfx", "potion")),
    ("menu",          ("music", "menu")),
    # The intro's effects before the intro's *music*, for the same reason
    # "monster_death" comes before "monster": a take delivered as
    # "intro_gate_final.wav" contains the needle "intro", and the general rule
    # would file the gate clang as the two-minute cue.
    ("intro_gate",    ("sfx", "intro_gate")),
    ("intro_run",     ("sfx", "intro_run")),
    ("intro_drip",    ("sfx", "intro_drip")),
    ("intro_tick",    ("sfx", "intro_tick")),
    ("tiktak",        ("sfx", "tiktak_reveal")),
    ("intro",         ("music", "intro")),
]


def resolve(stem):
    """(kind, name, how) for a delivered stem, or None if nothing matches."""
    if stem in TRACKS:
        return (*TRACKS[stem], "exact")
    for needle, mapping in ALIASES:
        if needle in stem:
            return (*mapping, f"alias '{needle}'")
    return None


def _stem(filename):
    """'main_menu (2).wav' -> 'main_menu'. Take numbers and separators go too.

    Generators and re-rolls both leave marks: '(2)', a trailing '-1', 'v3'. None
    of them change which slot the sound fills, so none of them should have to be
    written down in TRACKS.
    """
    stem = os.path.splitext(filename)[0].strip().lower()
    if stem.endswith(")") and "(" in stem:
        stem = stem[:stem.rindex("(")].strip()
    stem = stem.replace(" ", "_").replace("-", "_")
    while True:
        head, _, last = stem.rpartition("_")
        if head and (last.isdigit() or (last[:1] == "v" and last[1:].isdigit())):
            stem = head
            continue
        return stem


def _rms(w, start, frames):
    import array
    import math
    w.setpos(max(0, min(start, w.getnframes() - frames - 1)))
    a = array.array("h")
    a.frombytes(w.readframes(frames))
    if not a:
        return 0.0
    return math.sqrt(sum(x * x for x in a) / len(a)) / 32768.0


def _fade_trim(src):
    """(duration_to_keep, note) for a music file, or (None, note) to keep it all.

    Only WAV is analysed — it is what the generators deliver, and reading it
    needs no dependency beyond the standard library.
    """
    import wave
    if not src.lower().endswith(".wav"):
        return None, "not a wav, left as delivered"
    with wave.open(src) as w:
        sr, n = w.getframerate(), w.getnframes()
        win = int(sr * LOOP_WINDOW)
        body = _rms(w, n // 2, win)
        if body <= 0:
            return None, "silent?"
        head, tail = _rms(w, 0, win), _rms(w, n - win - 1, win)
        if tail >= body * LOOP_FADE_RATIO:
            return None, (f"ends at {tail / body:.0%} of body level"
                          + ("" if tail > body * 0.7 else " — tapered, left alone"))
        # walk back to the last window still at full level: that is the cut
        step = int(sr * 0.1)
        pos = n - win - 1
        while pos > win and _rms(w, pos, win) < body * LOOP_FADE_RATIO:
            pos -= step
        keep = (pos + win) / sr
        return keep, (f"fade-out trimmed: {n / sr:.0f}s -> {keep:.0f}s "
                      f"(ended at {tail / body:.0%} of body, head {head / body:.0%})")


def _silence_trim(src):
    """(start, duration, note) for an effect — the sound with the padding gone.

    Leading silence matters as much as trailing: a swing sound that starts 100ms
    into its file lands 100ms after the animation, which reads as lag rather than
    as a heavy weapon.
    """
    import array
    import math
    import wave
    if not src.lower().endswith(".wav"):
        return None, None, "not a wav, left as delivered"
    with wave.open(src) as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        a = array.array("h")
        a.frombytes(w.readframes(n))
    if ch == 2:
        a = a[::2]
    peak = max((abs(x) for x in a), default=0)
    if not peak:
        return None, None, "silent?"
    win = max(1, int(sr * 0.02))
    bar = peak * SFX_SILENCE
    first, last = None, 0
    for i in range(0, len(a) - win, win):
        seg = a[i:i + win]
        if math.sqrt(sum(x * x for x in seg) / len(seg)) > bar:
            first = i if first is None else first
            last = i + win
    if first is None:
        return None, None, "no content above the noise floor"
    start = max(0.0, first / sr - SFX_LEAD)
    end = min(len(a) / sr, last / sr + SFX_TAIL)
    total = n / sr
    if total - (end - start) < 0.05:
        return None, None, f"{total:.2f}s, no padding"
    return start, end - start, f"{total:.2f}s -> {end - start:.2f}s (padding cut)"


def _ffmpeg(src, dest, quality, normalise, keep=None, start=None):
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", src]
    filters = []
    if normalise:
        filters.append("dynaudnorm=p=0.9")
    if keep is not None:
        cmd += ["-t", f"{keep:.3f}"]
        # taper both ends just enough to kill the click at the loop seam
        filters.append(f"afade=t=in:st=0:d={SEAM_TAPER}")
        filters.append(f"afade=t=out:st={keep - SEAM_TAPER:.3f}:d={SEAM_TAPER}")
    if filters:
        cmd += ["-af", ",".join(filters)]
    cmd += ["-c:a", "libvorbis", "-q:a", quality, dest]
    subprocess.run(cmd, check=True)


def deliveries():
    if not os.path.isdir(SRC_DIR):
        return []
    return sorted(f for f in os.listdir(SRC_DIR)
                  if f.lower().endswith((".wav", ".mp3", ".flac", ".ogg", ".m4a")))


def main():
    files = deliveries()
    if not files:
        raise SystemExit(f"nothing to import — put audio in {SRC_DIR}")
    if "--list" in sys.argv:
        for f in files:
            hit = resolve(_stem(f))
            print(f"  {f}  ->  " + (f"{hit[0]}/{hit[1]}  [{hit[2]}]" if hit
                                    else "UNMAPPED (add it to TRACKS)"))
        return 0

    os.makedirs(MUSIC_OUT, exist_ok=True)
    os.makedirs(SFX_OUT, exist_ok=True)

    # ⚠️ Two deliveries can resolve to the same slot — `monster_die.wav` and
    # `monster_die_v2.wav` both do, because `_stem` strips the take number on
    # purpose. Whichever sorts last then wins, silently. Re-recording a take is
    # exactly when that happens, and exactly when you want to be *told* which
    # one shipped rather than deducing it from the file order.
    claims = {}
    for f in files:
        hit = resolve(_stem(f))
        if hit:
            claims.setdefault(hit[:2], []).append(f)
    for (kind, name), takes in sorted(claims.items()):
        if len(takes) > 1:
            print(f"  ⚠️  {kind}/{name}: {len(takes)} takes — {', '.join(takes)}\n"
                  f"      keeping '{takes[-1]}' (last by name). Delete the others "
                  f"from the delivery folder to choose deliberately.")

    unmapped = []
    for f in files:
        hit = resolve(_stem(f))
        if hit is None:
            unmapped.append(f)
            continue
        kind, name, how = hit
        out_dir = MUSIC_OUT if kind == "music" else SFX_OUT
        dest = os.path.join(out_dir, name + ".ogg")
        src = os.path.join(SRC_DIR, f)
        start = None
        if kind == "music" and name in NO_LOOP:
            keep, note = None, "one-shot (NO_LOOP): ending kept as delivered"
        elif kind == "music":
            keep, note = _fade_trim(src)
        else:
            start, keep, note = _silence_trim(src)
        _ffmpeg(src, dest, MUSIC_QUALITY if kind == "music" else SFX_QUALITY,
                normalise=(kind == "sfx"), keep=keep, start=start)
        before = os.path.getsize(src) / 1e6
        after = os.path.getsize(dest) / 1e6
        print(f"  {f} -> {kind}/{name}.ogg  ({before:.1f}MB -> {after:.1f}MB)"
              + ("" if how == "exact" else f"  [matched by {how}]"))
        if note:
            print(f"      {'loop' if kind == 'music' else 'trim'}: {note}")
    for f in unmapped:
        print(f"  ⚠️  {f}: no mapping — add '{_stem(f)}' to TRACKS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
