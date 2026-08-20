"""EventBus, Inventory, QuestManager, difficulty, scores."""
import pytest

from game.systems import difficulty, scores
from game.systems.eventbus import EventBus, Events
from game.systems.inventory import Inventory
from game.systems.quests import QuestManager


# ── EventBus ──────────────────────────────────────────────────────────────
def test_emit_reaches_every_subscriber_with_the_payload():
    bus = EventBus()
    seen = []
    bus.on("thing", lambda **kw: seen.append(("a", kw)))
    bus.on("thing", lambda **kw: seen.append(("b", kw)))
    bus.emit("thing", value=3)
    assert seen == [("a", {"value": 3}), ("b", {"value": 3})]


def test_emit_with_no_subscribers_is_not_an_error():
    EventBus().emit("nobody_listens", x=1)


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    seen = []
    off = bus.on("thing", lambda **_: seen.append(1))
    bus.emit("thing")
    off()
    bus.emit("thing")
    assert seen == [1]


def test_a_subscriber_may_unsubscribe_during_dispatch():
    """Dispatch iterates a copy; without that this mutates the list mid-loop."""
    bus = EventBus()
    seen = []

    def once(**_):
        seen.append(1)
        off()

    off = bus.on("thing", once)
    bus.on("thing", lambda **_: seen.append(2))
    bus.emit("thing")
    bus.emit("thing")
    assert seen == [1, 2, 2]


# ── Inventory ─────────────────────────────────────────────────────────────
def test_inventory_fills_to_capacity_then_refuses():
    inv = Inventory(2)
    assert inv.add("key") and inv.add("key")
    assert not inv.add("key")
    assert inv.is_full and inv.count("key") == 2


def test_remove_matches_variant_exactly():
    inv = Inventory(4)
    inv.add("book", "red")
    inv.add("book", "blue")
    assert not inv.remove("book", "green")
    assert inv.remove("book", "blue")
    assert inv.items == [("book", "red")]


def test_remove_without_a_variant_takes_any():
    inv = Inventory(4)
    inv.add("book", "red")
    assert inv.remove("book")
    assert inv.items == []


def test_find_returns_minus_one_when_absent():
    assert Inventory(2).find("key") == -1


def test_drop_random_never_drops_more_than_it_holds():
    inv = Inventory(4)
    inv.add("key")
    dropped = inv.drop_random(3)
    assert len(dropped) == 1 and inv.items == []


# ── QuestManager ──────────────────────────────────────────────────────────
DEFS = {
    "find_keys": {"type": "collect", "item": "key", "required": 2, "title_en": "Keys"},
    "return_books": {"type": "deliver", "item": "book", "required": 2,
                     "title_en": "Books", "unlocked_by": "find_keys"},
}


def test_collecting_advances_the_matching_quest_only():
    bus = EventBus()
    q = QuestManager(bus, dict(DEFS))
    bus.emit(Events.ITEM_COLLECTED, item_type="key")
    bus.emit(Events.ITEM_COLLECTED, item_type="health")
    assert q.get("find_keys") == (1, 2)


def test_quest_completes_and_announces_once():
    bus = EventBus()
    done = []
    bus.on(Events.QUEST_COMPLETED, lambda quest_id, **_: done.append(quest_id))
    q = QuestManager(bus, dict(DEFS))
    for _ in range(3):                       # one more than required
        bus.emit(Events.ITEM_COLLECTED, item_type="key")
    assert q.is_done("find_keys")
    assert done == ["find_keys"], "a finished quest must not re-fire"


def test_a_locked_quest_ignores_progress_until_its_prerequisite_is_done():
    bus = EventBus()
    q = QuestManager(bus, dict(DEFS))
    bus.emit(Events.BOOK_RETURNED)
    assert q.get("return_books") == (0, 2), "books shouldn't count before keys"
    for _ in range(2):
        bus.emit(Events.ITEM_COLLECTED, item_type="key")
    bus.emit(Events.BOOK_RETURNED)
    assert q.get("return_books") == (1, 2)


def test_objectives_hides_locked_quests():
    bus = EventBus()
    q = QuestManager(bus, dict(DEFS))
    assert [o["id"] for o in q.objectives()] == ["find_keys"]


def test_dispose_detaches_from_a_bus_that_outlives_the_run():
    bus = EventBus()
    q = QuestManager(bus, dict(DEFS))
    q.dispose()
    bus.emit(Events.ITEM_COLLECTED, item_type="key")
    assert q.get("find_keys") == (0, 2)


# ── difficulty ────────────────────────────────────────────────────────────
def test_hard_hits_harder_than_easy():
    assert difficulty.get("Easy")["dps"] < difficulty.get("Hard")["dps"]


def test_unknown_difficulty_falls_back_to_normal():
    assert difficulty.get("Nightmare") == difficulty.get("Normal")


@pytest.mark.parametrize("start,d,expected", [
    ("Easy", 1, "Normal"), ("Hard", 1, "Easy"),        # wraps forward
    ("Easy", -1, "Hard"),                              # and backward
])
def test_cycle_wraps(start, d, expected):
    assert difficulty.cycle(start, d) == expected


def test_cycle_from_an_unknown_name_lands_somewhere_valid():
    assert difficulty.cycle("???", 1) in difficulty.ORDER


# ── scores (redirected to tmp by the autouse fixture) ─────────────────────
def test_board_starts_empty_and_sorts_by_time():
    assert scores.load() == []
    scores.add("Slow", 90.0)
    scores.add("Fast", 12.5)
    assert [e["name"] for e in scores.top()] == ["Fast", "Slow"]


def test_a_player_keeps_one_row_and_their_best_time():
    """One entry per player, but a better run replaces a worse one.

    Refusing a known name outright is what filled the real board with "Elad" and
    "Eladi" — the same player working around the block to record a faster run.
    """
    assert scores.add("Roni", 30) == scores.ADDED
    assert scores.add("  roni  ", 10) == scores.IMPROVED, "a faster run counts"
    assert len(scores.load()) == 1, "still one row for that player"
    assert scores.best_time("RONI") == 10
    assert scores.add("Roni", 45) == scores.SLOWER, "a worse run must not count"
    assert scores.best_time("Roni") == 10


def test_blank_names_are_refused():
    assert scores.add("   ", 10) == scores.INVALID


def test_top_limits_the_rows():
    for i in range(5):
        scores.add(f"p{i}", i)
    assert len(scores.top(3)) == 3


def test_a_corrupt_score_file_reads_as_empty(monkeypatch, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    monkeypatch.setattr(scores, "SCORES_PATH", str(bad))
    assert scores.load() == []


# ── audio: streamed music with synth fallbacks ────────────────────────────
def test_music_is_found_by_name_and_missing_tracks_report_nothing(tmp_path, monkeypatch):
    from game.systems import audio
    monkeypatch.setattr(audio, "MUSIC_DIR", str(tmp_path))
    assert audio.music_path("menu") is None
    (tmp_path / "menu.ogg").write_bytes(b"not really ogg")
    assert audio.music_path("menu") == str(tmp_path / "menu.ogg")


def test_synth_buffers_are_converted_to_the_mixer_format():
    """The synths are mono at 22050 and the mixer runs stereo at 44100. A raw
    buffer is read in the *mixer's* format, so an unconverted one plays at half
    speed in one ear."""
    import array
    from game.systems import audio
    mono = array.array("h", [1000, -1000, 500]).tobytes()
    out = array.array("h")
    out.frombytes(audio._fit_mixer(mono))
    ratio = audio.MIXER_SR // audio.SR
    assert len(out) == 3 * ratio * audio.MIXER_CHANNELS
    assert out[0] == out[1] == 1000, "each sample lands on both channels"


def test_asking_for_a_track_that_does_not_exist_leaves_the_music_alone(monkeypatch):
    """States request tracks before those tracks have been written. Falling back
    to the chiptune there would drop it *on top* of whatever is streaming."""
    from game.systems import audio
    a = audio.AudioSystem.__new__(audio.AudioSystem)
    a.available, a.enabled, a._sound, a._track = True, True, None, "level_one"
    monkeypatch.setattr(audio, "music_path", lambda name: None)
    a.play_music("victory")
    assert a._track == "level_one", "the playing track must survive"
    assert a._sound is None, "and no synth loop underneath it"


# ── audio import: filename matching ───────────────────────────────────────
# Delivered audio is named after the prompt that made it, not after the slot it
# fills, and re-rolls add take numbers. These are the shapes actually received.
def _import_audio():
    import os
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "tools"))
    import import_audio
    return import_audio


@pytest.mark.parametrize("filename,expected", [
    ("main_menu.wav", "main_menu"),
    ("main_menu (2).wav", "main_menu"),
    ("level-1-background-music.wav", "level_1_background_music"),
    ("monster-grawl-1.wav", "monster_grawl"),          # take number stripped
    ("Playful Wet Cartoon Monster Growl.wav", "playful_wet_cartoon_monster_growl"),
    ("bark_v2.wav", "bark"),
])
def test_delivered_filenames_reduce_to_a_stem(filename, expected):
    assert _import_audio()._stem(filename) == expected


@pytest.mark.parametrize("stem,kind,name", [
    ("main_menu", "music", "menu"),
    ("level_1_background_music", "music", "level_one"),
    ("monster_grawl", "sfx", "monster"),               # typo, caught by alias
    ("playful_wet_cartoon_monster_growl", "sfx", "monster"),
])
def test_a_delivered_stem_resolves_to_a_slot(stem, kind, name):
    hit = _import_audio().resolve(stem)
    assert hit is not None, f"{stem} matched nothing"
    assert (hit[0], hit[1]) == (kind, name)


def test_alias_order_puts_the_specific_before_the_general():
    """'monster_death' must beat 'monster', or the death sound becomes the growl."""
    ia = _import_audio()
    needles = [n for n, _ in ia.ALIASES]
    assert needles.index("monster_death") < needles.index("monster")
    assert ia.resolve("monster_death_puff")[1] == "monster_die"


@pytest.mark.parametrize("stem,kind,name", [
    ("intro", "music", "intro"),                  # the cutscene cue
    ("intro_music", "music", "intro"),            # ...delivered under a title
    ("intro_gate_final", "sfx", "intro_gate"),    # ...and its effects
    ("tiktak_reveal_v2", "sfx", "tiktak_reveal"),
    ("girl_talk", "sfx", "girl_talk"),
])
def test_the_intro_audio_has_somewhere_to_land(stem, kind, name):
    """`docs/AUDIO_INTRO.md` tells the generator what to name a file; TRACKS is
    the other half of that contract, and a stem with no entry is skipped."""
    hit = _import_audio().resolve(stem)
    assert hit is not None, f"{stem} matched nothing"
    assert (hit[0], hit[1]) == (kind, name)


def test_the_intro_effects_beat_the_intro_music_in_the_alias_list():
    """The 'monster_death before monster' lesson, second time: 'intro_gate_final'
    contains the needle 'intro', so the general rule would file a gate clang as
    the two-minute cue."""
    ia = _import_audio()
    needles = [n for n, _ in ia.ALIASES]
    for specific in ("intro_gate", "intro_run", "intro_drip", "intro_tick"):
        assert needles.index(specific) < needles.index("intro")


def test_one_shot_music_keeps_its_ending():
    """⚠️ `_fade_trim` is right for a loop and wrong for a one-shot.

    A loop that fades to silence dies and snaps back every couple of minutes, so
    the trim exists. The intro cue resolves *into the title screen* and the
    defeat sting is meant to trail away — trimming those removes the ending the
    prompt asked for. Declared, so adding a one-shot is a decision.
    """
    ia = _import_audio()
    assert {"intro", "victory", "defeat"} <= ia.NO_LOOP
    # ...and the looping tracks are emphatically not in it.
    assert not ({"menu", "level_one", "duel"} & ia.NO_LOOP)


def test_an_unknown_delivery_is_reported_not_guessed():
    assert _import_audio().resolve("some_track_nobody_mapped") is None


# ── audio coverage ────────────────────────────────────────────────────────
# Every sound the game asks for that has neither a file nor a synth behind it.
# A silent name is legitimate — call sites are deliberately written before the
# audio for them exists — but it has to be *declared*, so that adding one is a
# decision rather than an accident, and so `docs/AUDIO_BOOK.md` has one place to
# stay in sync with. Delete a line here the moment the file lands.
PENDING_AUDIO = {
    "tome_cast",     # generic fallback: only used by a caster with no voice pack
    "tome_hit",      # the teachers' book landing on the player
    "web_hit",       # the web landing, before the wrap closes in
    "web_stuck",     # being caught
    "web_break",     # mashing free
    "locker_open",   # the payoff of the whole loop (§5)
}


def _requested_sound_names():
    """Every name passed to `audio.play`, or set as a hit/sound request."""
    import os
    import re
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game")
    pattern = re.compile(r'(?:play\(|hit_sound\s*=\s*|sound_request\s*=\s*)"([a-z_]+)"')
    names = set()
    for base, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(base, f)) as fh:
                    names |= set(pattern.findall(fh.read()))
    # the cast table is a dict literal, not a call
    from game.core.play_state import CAST_SOUND
    return names | set(CAST_SOUND.values())


def test_every_sound_the_game_asks_for_is_either_installed_or_declared_pending(game):
    """A silent sound must be a listed decision, not a surprise."""
    silent = {n for n in _requested_sound_names() if game.audio._get_sfx(n) is None}
    assert silent == PENDING_AUDIO, (
        f"missing but undeclared: {sorted(silent - PENDING_AUDIO)}; "
        f"declared but now installed (delete them): {sorted(PENDING_AUDIO - silent)}")


def test_a_pending_sound_is_ignored_rather_than_fatal(game):
    """The contract that lets a call site exist before its audio does."""
    for name in PENDING_AUDIO:
        game.audio.play(name)          # must not raise


# ── voice packs ───────────────────────────────────────────────────────────
def test_both_teachers_have_a_voice_and_it_resolves(game):
    """A voice pack is per character: `<voice>_<event>`."""
    from game.entities.monster import make_teacher
    assert make_teacher(0, 0).voice == "teacher_f"
    assert make_teacher(0, 0, female=False).voice == "teacher_m"
    for voice, events in (("teacher_f", ("throw", "hit", "die")),
                          ("teacher_m", ("throw", "hit", "die", "spotplayer"))):
        for e in events:
            assert game.audio._get_sfx(f"{voice}_{e}") is not None, f"{voice}_{e}"


def test_a_missing_voice_line_falls_back_to_the_generic_effect(game):
    """The female teacher has no `spotplayer` take yet — she must still growl."""
    assert game.audio._get_sfx("teacher_f_spotplayer") is None
    game.audio.play_voiced("teacher_f", "spotplayer", default="monster")
    game.audio.play_voiced(None, "die", default="monster_die")      # no pack at all
    game.audio.play_voiced("nobody", "die")                          # no default


def test_a_voice_never_talks_over_itself(game):
    """⚠️ `teacher_f_hit` is 1.59s and a sword swings every 0.36s. Without this,
    a flurry of four hits stacks four copies of the same yelp — the mistake
    `zina_bark` made at 1.85s against a 0.42s retrigger."""
    plays = []

    class _Busy:
        """A Sound that reports itself busy once it has been started."""
        def play(self, *a, **k):
            plays.append(1)

        def get_num_channels(self):
            return len(plays)

        def set_volume(self, v):
            pass

    game.audio._sfx["teacher_f_hit"] = _Busy()   # the cache `_get_sfx` reads
    for _ in range(4):
        game.audio.play_voiced("teacher_f", "hit")
    assert len(plays) == 1, "the yelp stacked on itself"
