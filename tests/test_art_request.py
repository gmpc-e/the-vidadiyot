"""The art-request bridge: prompt assembly and the acceptance gates.

No network and no API key — `generate()` is the only part that talks to the
API and it is deliberately not exercised here. What *is* worth testing is the
part that rots silently: the prompt packs are markdown a human edits, and a
restructured heading would leave the tool quietly sending an empty or truncated
prompt. These tests parse the real docs for that reason.
"""
import os
import sys

import pygame
import pytest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import art_request                                              # noqa: E402


@pytest.fixture(scope="module")
def phase1():
    return art_request.load_pack("1")


@pytest.fixture(scope="module")
def phase2():
    return art_request.load_pack("2")


def test_both_packs_parse(phase1, phase2):
    assert "0" in phase1 and "0" in phase2, "§0 style block must be found"
    # Phase 1 numbers its sheets, Phase 2 titles them "Sheet N —".
    assert {"1", "2", "3", "4"} <= set(phase1)
    # ⚠️ S3 and S4 are deliberately gone: the warriors' swing and throw are now
    # *rows* inside their own character sheet (S1, S2) rather than sheets of
    # their own, because one request per character is what keeps the character
    # consistent across its animations. See §A.
    assert {"S1", "S2", "S5", "S6", "S7", "S8", "S9", "S11"} <= set(phase2)
    assert "S3" not in phase2 and "S4" not in phase2


def test_no_section_is_empty(phase1, phase2):
    for pack in (phase1, phase2):
        for sid, (_title, text) in pack.items():
            assert len(text) > 80, f"§{sid} parsed to almost nothing"


def test_commentary_outside_the_blockquote_is_not_sent(phase1):
    # §1's "image models are poor at truly seamless tiles" warning is advice to
    # us, not to the model, and lives outside the quote.
    assert "Read this first" not in phase1["1"][1]


def test_style_block_rides_on_every_request(phase1):
    prompt = art_request.build_prompt(phase1, "1")
    assert "pure black" in prompt
    assert "abandoned school" in prompt


def test_preambles_chain(phase1, phase2):
    # A re-do sheet must carry §R0's delivery format; a Phase 2 sheet §A's rules.
    assert art_request.preambles_for("R1") == ["0", "R0"]
    assert art_request.preambles_for("S3") == ["0", "A"]
    assert art_request.preambles_for("1") == ["0"]
    assert "four times its final in-game size" in art_request.build_prompt(
        phase1, "R1")


def test_no_style_omits_it(phase1):
    assert "abandoned school" not in art_request.build_prompt(
        phase1, "1", with_style=False)


def test_markdown_emphasis_is_flattened(phase1):
    assert "**" not in art_request.build_prompt(phase1, "1")


def _sheet(tmp_path, name, paint):
    surf = pygame.Surface((256, 256))
    surf.fill((0, 0, 0))
    paint(surf)
    path = str(tmp_path / name)
    pygame.image.save(surf, path)
    return path


def test_gate_passes_objects_on_black(tmp_path):
    def paint(surf):
        pygame.draw.rect(surf, (180, 170, 150), (80, 80, 96, 96))
    ok, msgs = art_request.check(_sheet(tmp_path, "ok.png", paint))
    assert ok, msgs


def test_gate_rejects_a_painted_scene(tmp_path):
    # The `level-one.png` failure: art delivered on a full scene, not on black.
    def paint(surf):
        surf.fill((90, 80, 70))
    ok, msgs = art_request.check(_sheet(tmp_path, "scene.png", paint))
    assert not ok
    assert any("near-black" in m for m in msgs)


def test_gate_rejects_a_bright_corner(tmp_path):
    # A vignette or a border reaches the corners; flat black art never does.
    def paint(surf):
        pygame.draw.rect(surf, (200, 200, 200), (0, 0, 70, 70))
    ok, msgs = art_request.check(_sheet(tmp_path, "corner.png", paint))
    assert not ok
    assert any("corners are not black" in m for m in msgs)


# ── captions and material swatches ────────────────────────────────────────
# Both gates were built against the sheets this project actually received, but
# those live in ~/Downloads and a checkout has none of them. These rebuild the
# *shape* of each delivery instead, with the numbers the real sheets measured.
def _big_sheet(tmp_path, name, paint):
    """A sheet roomy enough that content clears the 64px corner patches.

    The corner gate samples a 64px square at each corner, so on a 256px canvas a
    centred object still lands in one. Everything painted here stays inside
    x 80..240, y 80..250.
    """
    surf = pygame.Surface((320, 320))
    surf.fill((0, 0, 0))
    paint(surf)
    path = str(tmp_path / name)
    pygame.image.save(surf, path)
    return path


def test_gate_rejects_painted_captions(tmp_path):
    """Three sheets running arrived with item names painted above each object.

    The shape that matters: a thin, sparse row of content sitting on top of a
    tall, dense one. On the real sheet the caption row is 12px against 160px of
    art below it.
    """
    def paint(surf):
        for x in (80, 120, 160, 200):        # a row of "words"
            pygame.draw.rect(surf, (190, 190, 190), (x, 90, 14, 6))
        pygame.draw.rect(surf, (150, 140, 120), (80, 112, 160, 128))
    ok, msgs = art_request.check(_big_sheet(tmp_path, "captioned.png", paint))
    assert not ok
    assert any("text labels" in m for m in msgs)


def test_a_thin_prop_is_not_mistaken_for_a_caption(tmp_path):
    """A ceiling light and a radiator are legitimately thin *and* sparse. The
    guard is that a caption must be followed by art several times taller —
    without it this gate would reject the corridor sheet, where a row of thin
    fittings sits above another row of ordinary ones."""
    def paint(surf):
        for x in (80, 130, 180):
            pygame.draw.rect(surf, (190, 180, 160), (x, 90, 30, 22))
        pygame.draw.rect(surf, (170, 160, 150), (80, 140, 160, 30))
    ok, msgs = art_request.check(_big_sheet(tmp_path, "thin.png", paint))
    assert ok, msgs


def _swatch(tmp_path, name, paint):
    surf = pygame.Surface((256, 256))
    paint(surf)
    path = str(tmp_path / name)
    pygame.image.save(surf, path)
    return path


def test_material_gate_rejects_a_swatch_made_of_two_materials(tmp_path):
    """The wall slab's defect: cinderblock above a dado rail, wainscot below.
    It measured 2.28; anything over 1.6 is two materials with a boundary."""
    def paint(surf):
        surf.fill((104, 100, 92))
        pygame.draw.rect(surf, (34, 32, 30), (0, 170, 256, 86))
    ok, msgs = art_request.check(_swatch(tmp_path, "rail.png", paint), material=True)
    assert not ok
    assert any("two materials" in m for m in msgs)


def test_material_gate_passes_a_checkerboard(tmp_path):
    """The false positive that killed two earlier versions of this check. A
    checkerboard is full of hard edges and tiles perfectly — the edges are its
    pattern, not a boundary. The real corridor slab measures 1.20."""
    def paint(surf):
        surf.fill((38, 40, 46))
        for ty in range(8):
            for tx in range(8):
                if (tx + ty) % 2:
                    pygame.draw.rect(surf, (72, 74, 80), (tx * 32, ty * 32, 32, 32))
    ok, msgs = art_request.check(_swatch(tmp_path, "checks.png", paint), material=True)
    assert ok, msgs


def test_material_gate_passes_a_very_dark_swatch(tmp_path):
    """Counting dark pixels cannot tell a swatch from objects on black: the real
    flagstone is 66% "black" and is good art. The corners decide instead."""
    def paint(surf):
        surf.fill((21, 22, 24))
        for i in range(0, 256, 24):
            pygame.draw.line(surf, (30, 31, 34), (i, 0), (i, 255))
    ok, msgs = art_request.check(_swatch(tmp_path, "dark.png", paint), material=True)
    assert ok, msgs


def test_material_gate_rejects_objects_on_black(tmp_path):
    """Asked for a swatch, given a prop sheet — the art covers almost none of
    the frame, rather than filling it."""
    def paint(surf):
        surf.fill((0, 0, 0))
        pygame.draw.rect(surf, (160, 150, 140), (90, 90, 76, 76))
    ok, msgs = art_request.check(_swatch(tmp_path, "props.png", paint), material=True)
    assert not ok
    assert any("objects on a background" in m for m in msgs)


def test_material_gate_accepts_a_letterboxed_swatch_and_says_where_to_crop(tmp_path):
    """What the model actually returns: a centred square swatch with black bars.

    The art is fine — measuring it across the bars is not, because they read as
    a brightness gradient and fail the uniformity test on their own.
    """
    def paint(surf):
        surf.fill((0, 0, 0))
        pygame.draw.rect(surf, (70, 72, 78), (40, 8, 176, 240))
    ok, msgs = art_request.check(_swatch(tmp_path, "bars.png", paint), material=True)
    assert ok, msgs
    assert any("letterboxed" in m and "Sample inside" in m for m in msgs)


def test_material_sections_are_declared_not_remembered():
    """§R2 was once gated as an object sheet and rejected for being exactly what
    it was asked to be — a floor patch with no black in it."""
    assert {"1", "R1", "R2", "R3"} <= art_request.MATERIAL_SECTIONS


# ── registration: the animation-strip gate ────────────────────────────────
def _strip(tmp_path, name, bottoms, heights=None, n=4):
    """A strip of `n` figures with the given baselines, on black.

    Wide gutters and a 640px canvas so the frames are found the way a delivered
    1536px sheet's are, and so nothing lands in a corner patch.
    """
    heights = heights or [120] * n
    surf = pygame.Surface((640, 320))
    surf.fill((0, 0, 0))
    for i, (bottom, h) in enumerate(zip(bottoms, heights)):
        x = 70 + i * 130
        pygame.draw.rect(surf, (190, 180, 160), (x, bottom - h, 40, h))
    path = str(tmp_path / name)
    pygame.image.save(surf, path)
    return path


def test_registration_passes_frames_that_share_a_baseline(tmp_path):
    ok, msgs = art_request.check(
        _strip(tmp_path, "reg.png", [240, 240, 241, 240]), strip=True)
    assert ok, msgs
    assert any("registration: 4 frames" in m for m in msgs)


def test_registration_rejects_a_frame_that_floats(tmp_path):
    """The failure the teacher sheets actually had: one pose drawn higher and
    smaller than the rest, which jitters when played."""
    ok, msgs = art_request.check(
        _strip(tmp_path, "float.png", [240, 240, 240, 196]), strip=True)
    assert not ok
    assert any("do not register" in m for m in msgs)
    assert any("frame 4 of 4" in m for m in msgs), msgs


def test_registration_is_advisory_for_something_with_no_feet(tmp_path):
    """A dissipating puff legitimately drifts and shrinks — §A's baseline clause
    is about characters."""
    ok, _ = art_request.check(
        _strip(tmp_path, "puff.png", [240, 230, 214, 196]), strip=True,
        formless=True)
    assert ok


def test_a_wind_up_may_get_taller_without_being_rejected(tmp_path):
    """Arms coming up is a *height* change, not a registration failure — which
    is why the gate measures the baseline and only notes the height."""
    ok, msgs = art_request.check(
        _strip(tmp_path, "windup.png", [240] * 4, heights=[110, 120, 150, 170]),
        strip=True)
    assert ok, msgs
    assert any("height ratio" in m for m in msgs)


def test_strip_sections_are_declared_not_remembered():
    """Same lesson as MATERIAL_SECTIONS: leaving the gate to a command-line flag
    is how the wrong one gets used."""
    assert "S1" in art_request.STRIP_SECTIONS
    assert art_request.FORMLESS_STRIPS <= art_request.STRIP_SECTIONS
    assert not (art_request.STRIP_SECTIONS & art_request.MATERIAL_SECTIONS)


# ── the intro pack, and the third gate it needed ──────────────────────────
@pytest.fixture(scope="module")
def intro():
    return art_request.load_pack("3")


def test_the_intro_pack_parses(intro):
    assert "0" in intro, "§0 style block must be found"
    assert "I0" in intro, "§I0 plate format must be found"
    # Seven plates, a run cycle, a bust and the transition motif.
    assert {"I1", "I2", "I3", "I3B", "I4", "I5", "I6", "I7", "I8"} <= set(intro)
    for sid, (_title, text) in intro.items():
        assert len(text) > 80, f"§{sid} parsed to almost nothing"


def test_the_plate_format_rides_on_every_intro_sheet(intro):
    prompt = art_request.build_prompt(intro, "I2")
    assert "cinematic plate" in prompt          # §I0
    assert "abandoned school at night" in prompt  # §0
    assert "one window on the upper floor is lit" in prompt.lower()  # §I2
    # ...but §I0 does not ask for itself.
    assert art_request.preambles_for("I0") == ["0"]


def test_the_run_cycle_declares_its_frame_count(intro):
    """The gate reads the count out of the heading, so the heading is the spec."""
    assert "I3" in art_request.STRIP_SECTIONS
    assert art_request.expected_frames(intro["I3"][0]) == 4
    # The bust is not a strip and must not be gated as one.
    assert "I3B" not in art_request.STRIP_SECTIONS


def test_scene_sections_are_declared_not_remembered():
    """Same lesson as MATERIAL_SECTIONS and STRIP_SECTIONS, third time asked."""
    assert {"I1", "I2", "I4", "I7"} <= art_request.SCENE_SECTIONS
    assert not (art_request.SCENE_SECTIONS & art_request.MATERIAL_SECTIONS)
    assert not (art_request.SCENE_SECTIONS & art_request.STRIP_SECTIONS)


def _plate(tmp_path, name, paint, size=(384, 256)):
    """A full-bleed painted plate: dark, but painted to all four corners."""
    surf = pygame.Surface(size)
    surf.fill((0, 0, 0))
    paint(surf)
    path = str(tmp_path / name)
    pygame.image.save(surf, path)
    return path


def _night_scene(surf):
    """A dark scene with one bright thing in it — the §I2 brief, roughly.

    Painted at the brightness the delivered art actually comes back at: the map
    slabs measured mean luma 38-56, and a moonlit exterior sits in that band. It
    is "dark" as a painting and nowhere near black as a *number*.
    """
    w, h = surf.get_size()
    surf.fill((48, 54, 70))                     # luma ~54, well over BLACK_LUMA
    pygame.draw.rect(surf, (30, 34, 46), (0, h // 2, w, h // 2))
    pygame.draw.rect(surf, (220, 190, 110), (w // 2, h // 3, 20, 16))


def test_the_object_gate_rejects_a_plate_and_the_scene_gate_passes_it(tmp_path):
    """The two gates disagreeing on the same file is the whole point of §I0.

    A cutscene plate *is* a painted scene, which is exactly what the object gate
    exists to reject — so an intro sheet run through the default gate fails for
    being correct.
    """
    path = _plate(tmp_path, "plate.png", _night_scene)
    ok, msgs = art_request.check(path)
    assert not ok
    assert any("near-black" in m or "corners are not black" in m for m in msgs)

    ok, msgs = art_request.check(path, scene=True)
    assert ok, msgs
    assert any("plate covers" in m for m in msgs)


def test_a_very_dark_plate_slips_past_the_object_gate(tmp_path):
    """⚠️ The object gate is not a safety net for plates — in either direction.

    A night scene painted dark enough can clear both the black-fraction and the
    corner clauses and be *accepted* as objects on black, which is worse than
    being rejected: nothing says the wrong gate ran. That is why SCENE_SECTIONS
    is a declared list and not "whatever fails the default".
    """
    def paint(surf):
        w, h = surf.get_size()
        surf.fill((26, 30, 44))                 # luma ~30: under the corner cut
        pygame.draw.rect(surf, (14, 16, 26), (0, h // 2, w, h // 2))
    ok, _ = art_request.check(_plate(tmp_path, "verydark.png", paint))
    assert ok, "if this starts failing, the note above is out of date"


def test_the_scene_gate_rejects_a_letterboxed_plate(tmp_path):
    """The failure a plate actually has: art padded with black bars.

    The camera pushes across this image, so a bar at an edge is a bar that
    slides into shot.
    """
    def paint(surf):
        w, h = surf.get_size()
        inner = surf.subsurface((0, 40, w, h - 80))
        _night_scene(inner)
    ok, msgs = art_request.check(_plate(tmp_path, "bars.png", paint), scene=True)
    assert not ok
    assert any("does not reach the frame edges" in m for m in msgs)


def test_the_scene_gate_still_catches_a_painted_caption(tmp_path):
    """A caption in a plate is a subtitle the game did not write."""
    def paint(surf):
        w, h = surf.get_size()
        surf.fill((8, 9, 14))
        pygame.draw.rect(surf, (200, 200, 200), (60, 20, 90, 10))   # the label
        pygame.draw.rect(surf, (40, 44, 60), (20, 60, w - 40, h - 80))
    ok, msgs = art_request.check(_plate(tmp_path, "caption.png", paint),
                                 scene=True)
    assert not ok
    assert any("text looks painted into the plate" in m for m in msgs)
