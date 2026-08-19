"""AudioSystem: a procedurally synthesized, funky chiptune loop.

We synthesize the music instead of shipping a .mid because reliable MIDI playback
needs a soundfont that isn't guaranteed on the target machine. This builds a
raw 16-bit mono buffer (square-wave bass + vibrato lead + kick/hi-hat) and loops
it — eerie and funky, fitting the abandoned-school vibe. Toggle with M.
"""
import array
import math
import os
import random

import pygame

from game.core.assets import ASSETS

SR = 22050
BPM = 110
MUSIC_VOLUME = 0.4
SFX_DIR = os.path.join(ASSETS, "sfx")

# one-bar patterns, sixteenth-note steps. 0 = rest. Deliberately syncopated and
# a little dissonant so it reads as "weird funky" rather than clean chiptune.
BASS = [45, 0, 45, 48,  0, 45, 43, 45,  40, 0, 40, 43,  45, 0, 48, 50]
LEAD = [69, 0,  0, 72,  0, 76,  0, 72,  71, 0, 74,  0,  79, 0, 76,  0]


def _midi_freq(n):
    return 440.0 * 2 ** ((n - 69) / 12.0)


def _synth_fanfare():
    """A short triumphant rising arpeggio + held major chord (~1.3s)."""
    seq = [60, 64, 67, 72]                          # C major arpeggio up
    note_samples = int(0.11 * SR)
    buf = array.array("h")
    for m in seq:                                    # quick rising notes
        f = _midi_freq(m)
        for s in range(note_samples):
            t = s / SR
            env = min(1.0, s / (0.004 * SR)) * max(0.0, 1.0 - s / note_samples)
            v = (1 if math.sin(2 * math.pi * f * t) >= 0 else -1) * env
            buf.append(max(-32768, min(32767, int(v * 10000))))
    chord = [_midi_freq(m) for m in (60, 64, 67, 72)]   # held C major
    hold = int(0.8 * SR)
    for s in range(hold):
        t = s / SR
        env = min(1.0, s / (0.004 * SR)) * max(0.0, 1.0 - s / hold)
        v = sum(1 if math.sin(2 * math.pi * f * t) >= 0 else -1 for f in chord) / len(chord)
        buf.append(max(-32768, min(32767, int(v * env * 11000))))
    return buf.tobytes()


def _tri(f, t):
    """Triangle wave — softer and bell-like next to the squares used elsewhere."""
    x = (f * t) % 1.0
    return 4.0 * abs(x - 0.5) - 1.0


def _synth_success():
    """Book-returned chime: a quick rising arpeggio, ~0.45s (roadmap §6).

    Deliberately shorter, higher and softer than `_synth_fanfare` so the payoff
    beat never blurs into the victory sting. Drop assets/sfx/success.(wav|ogg)
    to override it with a real sound.
    """
    seq = [76, 81, 88]                               # E - A - E, an open rising lift
    buf = array.array("h")
    for i, m in enumerate(seq):
        last = (i == len(seq) - 1)
        f = _midi_freq(m)
        n = int((0.24 if last else 0.075) * SR)
        for s in range(n):
            t = s / SR
            frac = s / n
            attack = min(1.0, s / (0.003 * SR))
            env = attack * (math.exp(-4.5 * frac) if last else 1.0 - frac)
            v = _tri(f, t) + 0.3 * _tri(f * 2, t)    # octave shimmer on top
            buf.append(max(-32768, min(32767, int(v * env * 8500))))
    return buf.tobytes()


def _synth_bark(seed=0):
    """Zina's bark: a short two-part yap — bright attack, quick downward tail."""
    buf = array.array("h")
    for part, (f0, f1, dur, amp) in enumerate(
            ((520, 300, 0.075, 1.0), (430, 210, 0.085, 0.75))):
        n = int(dur * SR)
        for s in range(n):
            t = s / n
            f = f0 + (f1 - f0) * t
            env = min(1.0, s / (0.002 * SR)) * (1.0 - t) ** 1.4
            tone = math.sin(2 * math.pi * f * (s / SR))
            noise = random.random() * 2 - 1
            v = (0.72 * tone + 0.28 * noise) * env * amp
            buf.append(max(-32768, min(32767, int(v * 12000))))
    return buf.tobytes()


def _synth_bite():
    """The kill: a hard snap of teeth, then a short low crunch."""
    buf = array.array("h")
    n = int(0.045 * SR)                         # the snap
    for s in range(n):
        t = s / n
        env = (1.0 - t) ** 0.6
        buf.append(max(-32768, min(32767, int((random.random() * 2 - 1) * env * 20000))))
    n = int(0.13 * SR)                          # the crunch under it
    for s in range(n):
        t = s / n
        env = min(1.0, s / (0.003 * SR)) * (1.0 - t) ** 1.8
        f = 130 - 60 * t
        v = 0.6 * math.sin(2 * math.pi * f * (s / SR)) + 0.4 * (random.random() * 2 - 1)
        buf.append(max(-32768, min(32767, int(v * env * 16000))))
    return buf.tobytes()


def _synth_level_done():
    """The level-complete sting: a rising cheer that curdles into a laugh.

    Deliberately not the victory fanfare — this marks *a level*, not the run, so
    it has to be recognisably its own thing. The laugh is a low tone under heavy
    amplitude tremolo ("aw-ha-ha-ha"), detuned against itself so it never sounds
    clean, which is what makes it read as horror rather than triumph.
    """
    buf = array.array("h")
    for m, dur in ((55, 0.16), (58, 0.16), (62, 0.20)):     # three rising steps
        f = _midi_freq(m)
        n = int(dur * SR)
        for s in range(n):
            t = s / SR
            frac = s / n
            env = min(1.0, s / (0.006 * SR)) * (1.0 - 0.45 * frac)
            v = (math.sin(2 * math.pi * f * t)
                 + 0.5 * math.sin(2 * math.pi * f * 1.005 * t)      # detune beat
                 + 0.3 * math.sin(2 * math.pi * f * 0.5 * t))
            buf.append(max(-32768, min(32767, int(v * env * 6200))))
    # the laugh: one held low note chopped into syllables by tremolo
    n = int(1.15 * SR)
    f0 = _midi_freq(50)
    for s in range(n):
        t = s / SR
        frac = s / n
        f = f0 * (1.0 - 0.18 * frac)                        # sagging pitch
        syl = 0.5 + 0.5 * math.sin(2 * math.pi * 6.5 * t) ** 2   # "ha-ha-ha"
        env = min(1.0, s / (0.01 * SR)) * (1.0 - frac) ** 0.8
        v = (math.sin(2 * math.pi * f * t)
             + 0.45 * math.sin(2 * math.pi * f * 1.008 * t)
             + 0.25 * (random.random() * 2 - 1))
        buf.append(max(-32768, min(32767, int(v * syl * env * 7000))))
    return buf.tobytes()


def _synth_growl():
    """Placeholder monster growl: low pitch-bending, noisy, a bit menacing.

    Replace by dropping a real file at assets/sfx/monster.wav (or .ogg) — the
    audio system prefers that file over this synth automatically.
    """
    dur = 0.7
    n = int(dur * SR)
    buf = array.array("h")
    for s in range(n):
        t = s / n
        f = 95 - 42 * t                     # pitch bends downward
        env = min(1.0, s / (0.03 * SR)) * (1.0 - t) ** 1.2
        tone = math.sin(2 * math.pi * f * (s / SR))
        growl = 0.6 * tone + 0.4 * (random.random() * 2 - 1)   # noise adds grit
        trem = 0.75 + 0.25 * math.sin(2 * math.pi * 18 * (s / SR))
        buf.append(max(-32768, min(32767, int(growl * trem * env * 15000))))
    return buf.tobytes()


def _synth_loop():
    step_samples = int(60.0 / BPM / 4 * SR)     # one sixteenth note
    buf = array.array("h")
    for i, (bn, ln) in enumerate(zip(BASS, LEAD)):
        fb = _midi_freq(bn) if bn else 0.0
        fl = _midi_freq(ln) if ln else 0.0
        kick = (i % 8 == 0)                      # downbeat thump
        hat = (i % 2 == 1)                       # offbeat tick
        for s in range(step_samples):
            t = s / SR
            env = min(1.0, s / (0.005 * SR)) * max(0.0, 1.0 - s / step_samples)
            val = 0.0
            if fb:  # square bass
                val += 0.32 * (1 if math.sin(2 * math.pi * fb * t) >= 0 else -1) * env
            if fl:  # square lead with vibrato -> the "weird" wobble
                vib = 1.0 + 0.03 * math.sin(2 * math.pi * 7 * t)
                val += 0.20 * (1 if math.sin(2 * math.pi * fl * vib * t) >= 0 else -1) * env
            if kick and s < step_samples * 0.5:
                ke = 1.0 - s / (step_samples * 0.5)
                val += 0.5 * math.sin(2 * math.pi * 70 * t) * ke
            if hat and s < step_samples * 0.15:
                he = 1.0 - s / (step_samples * 0.15)
                val += 0.15 * (random.random() * 2 - 1) * he
            buf.append(max(-32768, min(32767, int(val * 11000))))
    return buf.tobytes()


# ── the sound registry ────────────────────────────────────────────────────
# name -> synth fallback. Every entry can be overridden at any time by dropping
# a real file at assets/sfx/<name>.(wav|ogg) — no code change. Characters refer
# to sounds by name ("zina_bark"), so adding a voice to a new character is one
# synth plus one line here.
SYNTHS = {
    "monster":   _synth_growl,
    "success":   _synth_success,
    "zina_bark": _synth_bark,
    "zina_bite": _synth_bite,
    "level_done": _synth_level_done,
}


class AudioSystem:
    def __init__(self):
        self.available = False
        self.enabled = True
        self._sound = None
        self._fanfare = None
        self._sfx = {}          # name -> Sound cache
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=SR, size=-16, channels=1)
            self.available = True
        except pygame.error:
            self.available = False

    def start_music(self):
        """Synthesize (once) and start the looping track."""
        if not self.available or self._sound is not None:
            return
        try:
            self._sound = pygame.mixer.Sound(buffer=_synth_loop())
            self._sound.set_volume(MUSIC_VOLUME)
            self._sound.play(loops=-1)
        except pygame.error:
            self.available = False

    def play_fanfare(self):
        """One-shot victory sting. Held on the instance so it isn't GC'd mid-play."""
        if not self.available:
            return
        try:
            if self._fanfare is None:
                self._fanfare = pygame.mixer.Sound(buffer=_synth_fanfare())
            self._fanfare.set_volume(0.7 if self.enabled else 0.0)
            self._fanfare.play()
        except pygame.error:
            pass

    def _get_sfx(self, name, synth_fallback):
        """Return a Sound for `name`, preferring assets/sfx/<name>.(wav|ogg).

        Drop a real audio file there and it overrides the synth automatically —
        the intended path for provided audio going forward.
        """
        if name in self._sfx:
            return self._sfx[name]
        snd = None
        for ext in (".wav", ".ogg"):
            path = os.path.join(SFX_DIR, name + ext)
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                except pygame.error:
                    snd = None
                break
        if snd is None:
            snd = pygame.mixer.Sound(buffer=synth_fallback())
        self._sfx[name] = snd
        return snd

    def play(self, name, volume=1.0):
        """Play a registered sound by name. Unknown names are ignored, not fatal —
        a missing sound must never take the game down mid-fight."""
        if not self.available or not self.enabled:
            return
        synth = SYNTHS.get(name)
        if synth is None:
            return
        try:
            snd = self._get_sfx(name, synth)
            snd.set_volume(volume)
            snd.play()
        except pygame.error:
            pass

    def play_success(self):
        """Book returned. Uses assets/sfx/success.* if present."""
        self.play("success")

    def play_scare(self):
        """Monster spotting the player. Uses assets/sfx/monster.* if present."""
        self.play("monster")

    def toggle(self):
        self.enabled = not self.enabled
        if self._sound:
            self._sound.set_volume(MUSIC_VOLUME if self.enabled else 0.0)
        return self.enabled
