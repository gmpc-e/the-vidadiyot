"""AudioSystem: streamed music tracks, with synthesized fallbacks for everything.

Two layers, and they work differently on purpose.

**Music is streamed** through `pygame.mixer.music` from `assets/music/<track>.ogg`
— one track at a time, changed by whichever state is on top. Streaming matters:
the delivered menu track is 3.5 minutes, which is 40MB as a WAV and would sit in
RAM as a `Sound`. Each state asks for its track by name and the system does
nothing if it is already playing, so pushing a pause screen doesn't restart the
music.

**Sound effects are synthesized** (`SYNTHS`) unless a real file is dropped at
`assets/sfx/<name>.(wav|ogg)`, which overrides the synth with no code change.

Both layers fall back rather than fail: no track file plays the built-in
chiptune loop, no audio device at all disables the system quietly. A missing
sound must never take the game down mid-fight.

⚠️ **The synths generate mono at 22050Hz and the mixer runs stereo at 44100**,
because real music through a mono 22kHz mixer sounds like a phone call. Raw
buffers handed to `pygame.mixer.Sound` are interpreted in the *mixer's* format,
so `_fit_mixer()` converts them on the way in. Change `SR` or `MIXER_SR` and
that conversion is what has to keep up.
"""
import array
import math
import os
import random

import pygame

from game.core.assets import ASSETS

SR = 22050                  # the synths' native rate
MIXER_SR = 44100            # what the device runs at, for the streamed music
MIXER_CHANNELS = 2
BPM = 110
MUSIC_VOLUME = 0.35         # music sits *under* the effects, never over them
SFX_DIR = os.path.join(ASSETS, "sfx")
MUSIC_DIR = os.path.join(ASSETS, "music")
MUSIC_EXTS = (".ogg", ".wav")

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


def _fit_mixer(pcm):
    """Convert a mono `SR` buffer to the mixer's rate and channel count.

    The synths predate the mixer being stereo at 44100 and there is no reason to
    rewrite six of them: an integer rate ratio means each sample is simply held
    for `MIXER_SR // SR` output frames, and written once per channel.
    """
    ratio = MIXER_SR // SR
    if ratio == 1 and MIXER_CHANNELS == 1:
        return pcm
    mono = array.array("h")
    mono.frombytes(pcm)
    out = array.array("h")
    for sample in mono:
        for _ in range(ratio):
            for _ in range(MIXER_CHANNELS):
                out.append(sample)
    return out.tobytes()


def music_path(track):
    """Path to a music file for `track`, or None if it isn't installed."""
    for ext in MUSIC_EXTS:
        path = os.path.join(MUSIC_DIR, track + ext)
        if os.path.exists(path):
            return path
    return None


# ── the sound registry ────────────────────────────────────────────────────
# name -> synth fallback. Every entry can be overridden at any time by dropping
# a real file at assets/sfx/<name>.(wav|ogg) — no code change. Characters refer
# to sounds by name ("zina_bark"), so adding a voice to a new character is one
# synth plus one line here.
# Placeholders only. A sound needs an entry here *only* if it must be audible
# before its real file exists; anything delivered as a file plays without one.
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
        self._sound = None          # the synthesized fallback loop, if in use
        self._track = None          # name of the track currently playing
        self._fanfare = None
        self._sfx = {}              # name -> Sound cache
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=MIXER_SR, size=-16,
                              channels=MIXER_CHANNELS)
            self.available = True
        except pygame.error:
            self.available = False

    # ── music ────────────────────────────────────────────────────────────--
    def play_music(self, track):
        """Stream `track` on a loop, or keep the synth loop if it isn't there.

        Called by whichever state owns the screen. Asking for the track that is
        already playing is a no-op, so pushing pause or the leaderboard over the
        level does not restart the music.
        """
        if not self.available or track == self._track:
            return
        path = music_path(track)
        if path is None:
            # Not installed yet. Only fall back to the chiptune if nothing is
            # playing at all — otherwise asking for a track that hasn't been
            # written yet would drop the synth loop *on top* of the one that is
            # already streaming. States can request tracks that don't exist.
            if self._track is None and self._sound is None:
                self._start_synth_loop()
            return
        try:
            self._stop_synth_loop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME if self.enabled else 0.0)
            pygame.mixer.music.play(loops=-1)
            self._track = track
        except pygame.error:
            self._start_synth_loop()

    def _start_synth_loop(self):
        """The built-in chiptune, for a checkout with no music files."""
        if self._sound is not None:
            return
        try:
            self._sound = pygame.mixer.Sound(buffer=_fit_mixer(_synth_loop()))
            self._sound.set_volume(MUSIC_VOLUME if self.enabled else 0.0)
            self._sound.play(loops=-1)
            self._track = None
        except pygame.error:
            self.available = False

    def _stop_synth_loop(self):
        if self._sound is not None:
            self._sound.stop()
            self._sound = None

    def stop_music(self):
        self._stop_synth_loop()
        if self.available:
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass
        self._track = None

    def start_music(self):
        """Backwards-compatible entry point: start whatever the menu plays."""
        self.play_music("menu")

    def play_fanfare(self):
        """One-shot victory sting. Held on the instance so it isn't GC'd mid-play."""
        if not self.available:
            return
        try:
            if self._fanfare is None:
                self._fanfare = pygame.mixer.Sound(buffer=_fit_mixer(_synth_fanfare()))
            self._fanfare.set_volume(0.7 if self.enabled else 0.0)
            self._fanfare.play()
        except pygame.error:
            pass

    def _get_sfx(self, name):
        """A Sound for `name`: the file if there is one, else the synth, else None.

        Both halves are optional and that is the point. A *placeholder* sound has
        a synth and no file, and gains one silently the moment `import_audio`
        drops it in. A *new* sound arrives as a file with no synth ever written —
        which the first version of this refused to play, because it looked the
        name up in `SYNTHS` before looking on disk.
        """
        if name in self._sfx:
            return self._sfx[name]
        snd = None
        for ext in (".ogg", ".wav"):
            path = os.path.join(SFX_DIR, name + ext)
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                except pygame.error:
                    snd = None
                break
        if snd is None and name in SYNTHS:
            snd = pygame.mixer.Sound(buffer=_fit_mixer(SYNTHS[name]()))
        self._sfx[name] = snd
        return snd

    def play(self, name, volume=1.0):
        """Play a sound by name. A name with neither a file nor a synth behind it
        is ignored, not fatal — call sites are allowed to be written before the
        audio for them exists, and a missing sound must never take the game down
        mid-fight."""
        if not self.available or not self.enabled:
            return
        try:
            snd = self._get_sfx(name)
            if snd is None:
                return
            snd.set_volume(volume)
            snd.play()
        except pygame.error:
            pass

    def play_voiced(self, voice, event, default=None, volume=1.0):
        """Play one character's own take on `event`, or fall back.

        A **voice pack** is a set of sounds belonging to one character —
        `teacher_f_spotplayer`, `teacher_f_throw`, `teacher_f_hit`,
        `teacher_f_die`. They are not variants of the generic effects; they
        replace them for the character that owns them, and `default` covers the
        characters that have no pack (or the events a pack is still missing —
        the female teacher has no `spotplayer` take yet and falls back to the
        generic growl, which is fine and audibly so).

        ⚠️ **A voice never overlaps itself.** The delivered `teacher_f_hit` is
        1.59s and a sword swings every 0.36s, so a flurry of four hits would
        stack four copies of the same yelp — the mistake `zina_bark` made at
        1.85s against a 0.42s retrigger. Rather than tuning a cooldown per
        sound, this asks pygame whether the clip is *still playing* and skips
        it if so, which needs no numbers and stays right when a take is
        re-recorded at a different length.
        """
        if not self.available or not self.enabled:
            return
        name = f"{voice}_{event}" if voice else None
        snd = self._get_sfx(name) if name else None
        if snd is None:
            if default:
                self.play(default, volume)
            return
        try:
            if snd.get_num_channels():        # this voice is mid-sentence
                return
            snd.set_volume(volume)
            snd.play()
        except pygame.error:
            pass

    def stop(self, name):
        """Cut a sound short. Used when the screen that owns it goes away."""
        snd = self._sfx.get(name)
        if snd is not None:
            try:
                snd.fadeout(180)        # not stop(): an abrupt cut clicks
            except pygame.error:
                pass

    def play_success(self):
        """Book returned. Uses assets/sfx/success.* if present."""
        self.play("success")

    def play_scare(self):
        """Monster spotting the player. Uses assets/sfx/monster.* if present."""
        self.play("monster")

    def toggle(self):
        """M — mute/unmute. Silences the streamed track and the synth loop alike."""
        self.enabled = not self.enabled
        level = MUSIC_VOLUME if self.enabled else 0.0
        if self._sound:
            self._sound.set_volume(level)
        if self.available:
            try:
                pygame.mixer.music.set_volume(level)
            except pygame.error:
                pass
        return self.enabled
