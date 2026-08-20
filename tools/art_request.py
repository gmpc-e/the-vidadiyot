"""Ask an image model for a sheet from the prompt pack, and gate what comes back.

The art pipeline was automated on both sides of one manual step: a human pasted
a prompt from `docs/ART_PROMPTS*.md` into a chat window, downloaded the PNG into
`~/Downloads/the-vidadiyot/`, and `extract_*.py` did the rest. This closes that
gap by calling the OpenAI Images API directly.

Three decisions worth knowing before editing this file:

**The prompt pack is the source of truth, not this file.** Sections are parsed
out of the markdown at run time — `## §N Title` heading, prompt body in the
blockquote under it. Unquoted paragraphs in a section are notes *to us* (the
"image models cannot paint a seamless tile" warning in §1, for one) and are
deliberately not sent. Edit the doc, not a copy of the doc here.

**§0 is prepended to every request**, and so is any preamble the pack says to
paste with every sheet — §R0's delivery format for the re-do sections, §A's
animation rules for the Phase 2 sheets. That is what the packs mean by "paste
this first, every time", and it is the only thing keeping sheet 4 looking like
sheet 1. `--no-style` exists for debugging and will drift the style if used for
real.

**What comes back is not trusted.** `check()` runs before the art is written
anywhere the extractors can see it, because the two failures this pipeline has
actually suffered are both cheap to detect and expensive to discover late: art
delivered on a painted scene instead of flat black (`level-one.png`, which then
needed a bespoke alpha curve), and painted text labels that a cutout tool
mistook for the subject. A sheet that fails is still written — to `--out` with a
`.rejected.png` suffix — so it can be looked at rather than silently thrown away.

Run:  ./venv/bin/python tools/art_request.py --list
      ./venv/bin/python tools/art_request.py 1 --dry-run
      ./venv/bin/python tools/art_request.py 1 --out map/tiles/slabs_v2.png
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritelib import SOURCE_ROOTS                              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(ROOT, ".env")
PROMPT_DOCS = {
    "1": os.path.join(ROOT, "docs", "ART_PROMPTS.md"),
    "2": os.path.join(ROOT, "docs", "ART_PROMPTS_PHASE2.md"),
    "3": os.path.join(ROOT, "docs", "ART_PROMPTS_INTRO.md"),
}

KEY_NAMES = ("OPENAI_API_KEY", "OPEN_AI_API", "OPEN_AI_KEY")

API_URL = "https://api.openai.com/v1/images/generations"
MODEL = "gpt-image-1"

# 1536x1024 is what the prompt pack asks for and what `manifest.json` records as
# the source resolution — the extractors' crop coordinates are in these pixels,
# so changing it invalidates every hard-coded crop in `extract_map_art.py`.
DEFAULT_SIZE = "1536x1024"
DEFAULT_QUALITY = "high"

# Image generation is slow; the default urllib timeout gives up long before a
# high-quality 1536x1024 render finishes.
TIMEOUT = 300

# ── acceptance gates ──────────────────────────────────────────────────────
# There are two kinds of sheet in the packs and they want opposite checks.
#
# **Object sheets** (most of them) arrive as isolated things on #000000, and the
# failure is a painted scene: loosen BLACK_FRACTION and scene art reaches the
# keyer, which will happily key the middle out of a floor.
#
# **Material sheets** (§1, §R1, §R3 — floor and wall swatches) are the exact
# inverse: they are asked to fill the frame edge to edge with no black at all,
# and running the object gate on one rejects perfectly good art. The delivered
# `classroom_floor_slab.png` fails it at 22% black, which is how this was found.
# Their failure mode is different too, and it has already cost us a tile: the
# wall slab arrived with a dado rail and a skirting board painted across it, so
# it tiles into stripes. `_bands()` looks for exactly that.
BLACK_LUMA = 24                  # luma at or under this counts as "background"
BLACK_FRACTION = 0.25            # at least this share of an object sheet is black
CORNER_LUMA = 40                 # every corner patch must average under this
CORNER_PATCH = 64                # px square sampled at each corner

# Telling a *swatch* from *objects on black* by counting dark pixels does not
# work: the delivered flagstone is 66% "black" by pixel count and is good art,
# while the brief is literally "dark and desaturated". The corners settle it
# instead — a full-bleed swatch has material in all four, objects-on-black has
# nothing in any.
MATERIAL_CORNER_LUMA = 12        # all four corners under this = not a swatch
MATERIAL_MARGIN = 16             # px ignored at each edge: crops carry a border
MATERIAL_MIN_COVER = 0.35        # below this the "swatch" is objects on a background
MATERIAL_FULL_COVER = 0.75       # below this it is usable but letterboxed

# Which sections ask for a **material swatch** rather than objects on black, and
# therefore want the opposite gate. Declared here rather than left to a --material
# flag on the command line, because the one time it was left to hand, §R2 was
# gated as an object sheet and rejected for being exactly what it was asked to
# be: a floor patch filling the frame with no black in it at all.
MATERIAL_SECTIONS = {"1", "R1", "R2", "R3"}

# ── scene plates (the intro) ──────────────────────────────────────────────
# A third kind of sheet, and it breaks the rule the other two share. An intro
# plate is a **full-bleed painted scene**: no black background to key against
# and a deliberate focal point. Both existing gates reject it, each for being
# exactly what it was asked to be —
#
#   * the object gate fails it at "this looks like a painted scene", which is
#     the correct description of a cutscene plate;
#   * `--material` fails it on uniformity, because a scene *has* a composition
#     and a swatch must not.
#
# What a plate can actually get wrong is arriving letterboxed — the model paints
# a centred 3:2-ish picture and pads it with black bars, and the bars then get
# cropped into the frame the camera pushes across. So the check is coverage, via
# the same content box `--material` uses. It is deliberately generous: a bounding
# box is a box, so even a dark night scene with moonlight spread across it fills
# nearly all of one. Below 0.90 something is genuinely missing from an edge.
SCENE_MIN_COVER = 0.90
SCENE_SECTIONS = {"I1", "I2", "I4", "I7"}
# Whether a swatch is **one material**, which is what §R1 actually asks for:
# "every part interchangeable with every other part". Compare the mean brightness
# of the swatch in thirds, along both axes. This replaced two earlier attempts at
# edge-detection, and the reason is worth keeping: looking for a hard edge finds
# the checkerboard's own squares, and looking for an outlier step finds them too.
# The wall's defect was never the edge, it was that the material *changes* across
# it — cinderblock above the dado rail, wainscot below — and a swatch made of two
# materials cannot tile whichever way you cut it.
#
# Measured on the four delivered slabs: parquet 1.16, corridor checkerboard 1.20,
# flagstone 1.33, and the rail-bearing wall **2.28**. The gap is wide enough that
# the exact threshold barely matters.
UNIFORM_MAX_RATIO = 1.6

# Captions. Three sheets running have arrived with item names painted above each
# object, despite §0 and §R0 both forbidding it in the same words — and a label
# is what `extract_props.py` has to dodge by hand, because a cutout tool will
# happily mistake one for the subject. A caption is a *thin, sparse* row of
# content sitting above a *tall, dense* one; on the sheets we have, caption rows
# run 13-16px at a tenth of the density of the item rows below them. That
# separation is not marginal, so it is worth gating on.
CAPTION_MAX_H = 26               # px: taller than this and it is art, not a label
CAPTION_MAX_DENSITY = 0.40       # share of the row's width that is lit
# ...0.40 because a *row of captions* spread across a whole sheet lights up a
# third of its width — density alone barely separates a label row (0.33) from an
# item row (0.59). Height is the real signal: 12-16px against 160-220px. The
# rule below also demands the next run be three times taller, which is what stops
# a genuinely thin row of props reading as a caption.
CONTENT_MIN_DENSITY = 0.002      # below this a row counts as empty

# ── registration (animation strips) ───────────────────────────────────────
# §A of the Phase 2 pack opens with "Registration is the whole game": if the
# subject shifts or changes size between frames the animation jitters, and there
# is no fixing it afterwards — not in the extractor, not in code.
#
# ⚠️ **The pack has said so all along and the model ignored it twice**, on the
# four-pose teacher sheets, which are an *easier* problem than a cycle. §R8 asked
# for "one common ground line, whole body visible in every one of the four";
# roll one cropped a pose at the waist, roll two drew it a quarter smaller. So
# this is gated rather than merely asked for.
#
# **What is measured is the baseline, not the height.** A wind-up legitimately
# gets taller when the arms come up, so height is only advisory — but the feet
# do not move, and that is the clause §A actually states. Measured on the sheets
# we have, as a fraction of sheet height: the two good four-pose sheets sit at
# 0.002 and 0.011, and the two failures at **0.043 and 0.054**. The gap is wide.
BASELINE_SPREAD = 0.02           # of sheet height, across all frames
STRIP_HEIGHT_RATIO = 1.35        # advisory: tallest frame vs shortest
STRIP_GUTTER = 20                # px of black between two frames

# Sections that deliver an animation **strip** and therefore want the check.
# Phase 2's sheets are parsed as S1..S10.
STRIP_SECTIONS = {f"S{i}" for i in range(1, 10)} | {"I3"}
# How many frames a sheet should hold is read out of its own **heading** —
# "Wallad's walk cycle (4 frames)" — rather than kept in a table here, so the doc
# stays the single source of truth. The first delivered strip came back with
# **three** frames instead of four and passed every other check, which is how
# this came to exist: registration was perfect, the sheet was simply short.
# A heading saying "one strip each" describes several strips stacked on one
# sheet, where a single row of columns means nothing — those are skipped.
FRAME_COUNT_RE = re.compile(r"\((\d+)\s+frames?", re.I)
# ...and the ones with no feet, where a baseline is meaningless and a subject
# that shrinks is the intended effect. Advisory only for these.
FORMLESS_STRIPS = {"S7", "S9"}


def load_key():
    """The API key, from `.env` at the repo root or the environment.

    `.env` is gitignored. Several spellings are accepted: this repo's file has
    used both `OPEN_AI_API` and `OPEN_AI_KEY`, while the wider world uses
    `OPENAI_API_KEY`. A key present under an unrecognised name reads exactly like
    no key at all, which is a silly way to lose ten minutes.
    """
    for name in KEY_NAMES:
        if os.environ.get(name):
            return os.environ[name].strip()

    if not os.path.exists(ENV_FILE):
        raise SystemExit(
            f"no API key: set {KEY_NAMES[0]}, or put it in {ENV_FILE} as\n"
            f"  OPEN_AI_API=sk-...\n"
            f"(.env is gitignored — never commit the key)")

    with open(ENV_FILE) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            if name.strip() in KEY_NAMES:
                return value.strip().strip('"').strip("'")
    raise SystemExit(f"{ENV_FILE} has none of: {', '.join(KEY_NAMES)}")


def parse_prompts(path):
    """`{section_id: (title, prompt)}` from one prompt-pack markdown file.

    Two heading shapes, because the two packs were written differently: Phase 1
    numbers its sections `## §N Title`, Phase 2 lists `## Sheet N — Title` (kept
    here as `S1`…`S10`). A section's prompt is every blockquote line beneath its
    heading, with blank lines between quote blocks preserved as paragraph
    breaks. Prose outside the quotes is commentary for humans and is dropped.
    """
    sections, sid, title, body = {}, None, None, []

    def flush():
        if sid is not None:
            text = "\n".join(body).strip()
            text = re.sub(r"\n{3,}", "\n\n", text)
            if text:
                sections[sid] = (title, text)

    with open(path) as fh:
        for line in fh:
            heading = re.match(r"^##\s+§(\S+)\s*(.*)", line.rstrip())
            sheet = re.match(r"^##\s+Sheet\s+(\d+)\s*[—-]\s*(.*)", line.rstrip())
            if heading or sheet:
                flush()
                if heading:
                    sid, title = heading.group(1), heading.group(2)
                else:
                    sid, title = "S" + sheet.group(1), sheet.group(2)
                body = []
                continue
            if sid is None:
                continue
            if line.startswith(">"):
                body.append(re.sub(r"^>\s?", "", line.rstrip()))
            elif not line.strip() and body:
                body.append("")
    flush()
    return sections


def load_pack(phase):
    path = PROMPT_DOCS[phase]
    if not os.path.exists(path):
        raise SystemExit(f"prompt pack missing: {path}")
    return parse_prompts(path)


# Emphasis that *wraps across a line* still has to be flattened. `.` does not
# match a newline, so the first version left literal asterisks in any bold run
# long enough to wrap — which is most of the emphatic ones, since those are the
# sentences worth emphasising. The prompt still worked, so nothing pointed at
# it; it was found by reading a --dry-run. A blank line still ends a run, so an
# unclosed `**` cannot swallow the rest of the sheet.
_WRAPS = r"((?:(?!\n\n)[\s\S])+?)"


def strip_markdown(text):
    """Flatten `**bold**` and heading marks — the model reads prose, not md."""
    text = re.sub(r"\*\*" + _WRAPS + r"\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)" + _WRAPS + r"(?<!\*)\*(?!\*)", r"\1", text)
    return re.sub(r"`" + _WRAPS + r"`", r"\1", text)


def preambles_for(section):
    """Section ids that must be pasted ahead of `section`, in order.

    The packs say so in their own headings: §0 goes on everything, §R0's
    delivery format goes on every re-do sheet, §A's animation rules go on every
    Phase 2 sheet, and §I0's plate format goes on every intro sheet. Sending a sheet without its preamble is how you get art
    at the wrong resolution or a walk cycle whose frames do not register.
    """
    ids = ["0"]
    if section.startswith("R") and section != "R0":
        ids.append("R0")
    if section.startswith("S"):
        ids.append("A")
    if section.startswith("I") and section != "I0":
        ids.append("I0")
    return ids


def build_prompt(pack, section, with_style=True):
    if section not in pack:
        raise SystemExit(f"no §{section} in this pack; try --list")
    parts = []
    if with_style:
        parts += [pack[i][1] for i in preambles_for(section) if i in pack]
    parts.append(pack[section][1])
    return strip_markdown("\n\n".join(parts))


def generate(prompt, key, size, quality, background):
    """POST to the Images API, return PNG bytes.

    Stdlib only, deliberately: the venv is five packages and this tool is not a
    good enough reason to make it six.
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
    }
    if background != "opaque":
        payload["background"] = background

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:800]
        raise SystemExit(f"API error {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"could not reach the API: {exc.reason}")

    try:
        return base64.b64decode(body["data"][0]["b64_json"])
    except (KeyError, IndexError):
        raise SystemExit(f"unexpected API response: {json.dumps(body)[:800]}")


def _luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _row_density(img, w, h, step=4):
    """Share of each sampled row that is lit, top to bottom."""
    out = []
    cols = len(range(0, w, step))
    for y in range(0, h, step):
        lit = sum(1 for x in range(0, w, step)
                  if _luma(img.get_at((x, y))) > BLACK_LUMA)
        out.append(lit / cols)
    return out


def _captions(img, w, h, step=4):
    """Rows that look like painted text labels sitting above artwork.

    A caption is thin and sparse; the art under it is tall and dense. Requiring
    *both* is what keeps a genuinely thin prop — a ceiling light, a radiator —
    from being reported as a label.
    """
    density = _row_density(img, w, h, step)
    runs, start = [], None
    for i, d in enumerate(density + [0.0]):
        if d > CONTENT_MIN_DENSITY and start is None:
            start = i
        elif d <= CONTENT_MIN_DENSITY and start is not None:
            runs.append((start, i))
            start = None
    found = []
    for n, (a, b) in enumerate(runs):
        height = (b - a) * step
        peak = max(density[a:b])
        if height > CAPTION_MAX_H or peak > CAPTION_MAX_DENSITY:
            continue
        nxt = runs[n + 1] if n + 1 < len(runs) else None
        if nxt and (nxt[1] - nxt[0]) * step > height * 3:
            found.append(a * step)
    return found


def _content_box(img, w, h, step=4):
    """The bounding box of everything that isn't background.

    A model asked for a full-bleed swatch tends to paint a *centred square* on
    the 3:2 canvas and letterbox it with black bars. The art is fine; measuring
    it across the whole frame is not, because the bars read as a brightness
    gradient and fail the uniformity test on their own. So: find the art first,
    judge it second, and tell the caller where to crop.
    """
    xs, ys = [], []
    for y in range(0, h, step):
        for x in range(0, w, step):
            if _luma(img.get_at((x, y))) > BLACK_LUMA:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs) - min(xs) + step, max(ys) - min(ys) + step)


def _uniformity(img, w, h, step=4, box=None):
    """How far a material swatch is from being one material, and where.

    Returns `(ratio, axis)` — the worst brightness ratio between thirds of the
    swatch, and whether it runs top-to-bottom or left-to-right. The outer
    `MATERIAL_MARGIN` is skipped: a crop off a larger sheet carries that sheet's
    black gutter at its edge, and that is not a property of the material.
    """
    def mean(x0, x1, y0, y1):
        vals = [_luma(img.get_at((x, y)))
                for y in range(y0, y1, step) for x in range(x0, x1, step)]
        return sum(vals) / max(1, len(vals))

    bx, by, bw, bh = box or (0, 0, w, h)
    x0, x1 = bx + MATERIAL_MARGIN, max(bx + MATERIAL_MARGIN + 3, bx + bw - MATERIAL_MARGIN)
    y0, y1 = by + MATERIAL_MARGIN, max(by + MATERIAL_MARGIN + 3, by + bh - MATERIAL_MARGIN)
    tw, th = (x1 - x0) // 3, (y1 - y0) // 3
    rows = [mean(x0, x1, y0 + i * th, y0 + (i + 1) * th) for i in range(3)]
    cols = [mean(x0 + i * tw, x0 + (i + 1) * tw, y0, y1) for i in range(3)]
    down = max(rows) / max(1.0, min(rows))
    across = max(cols) / max(1.0, min(cols))
    return ((down, "top to bottom") if down >= across else (across, "left to right"))


def _strip_frames(img, w, h):
    """(left, right, top, bottom) of the lit content in each frame of a strip."""
    lit_col = [any(_luma(img.get_at((x, y))) > BLACK_LUMA for y in range(0, h, 3))
               for x in range(w)]
    spans, run, empty = [], None, 0
    for x in range(w):
        if lit_col[x]:
            run, empty = (x if run is None else run), 0
        elif run is not None:
            empty += 1
            if empty >= STRIP_GUTTER:
                spans.append((run, x - empty))
                run = None
    if run is not None:
        spans.append((run, w - 1))
    spans = [sp for sp in spans if sp[1] - sp[0] >= 24]

    out = []
    for x0, x1 in spans:
        rows = [y for y in range(0, h, 2)
                if any(_luma(img.get_at((x, y))) > BLACK_LUMA
                       for x in range(x0, x1, 3))]
        if rows:
            out.append((x0, x1, rows[0], rows[-1]))
    return out


def expected_frames(title):
    """How many frames the section's own heading asks for, or None."""
    if not title or "each" in title.lower():
        return None                    # several strips on one sheet
    m = FRAME_COUNT_RE.search(title)
    return int(m.group(1)) if m else None


def _registration(img, w, h, formless=False, expect=None):
    """(ok, messages) for an animation strip. See BASELINE_SPREAD above."""
    frames = _strip_frames(img, w, h)
    if expect and len(frames) != expect:
        return False, [
            f"registration: found {len(frames)} frames, the sheet asks for "
            f"{expect}",
            f"FAIL wrong frame count. Too few means the model simply drew fewer "
            f"than it was told, or two frames are touching and merged — §A wants "
            f"a wide black gutter and nothing touching. Too many means a frame "
            f"broke apart. Re-roll the sheet"]
    if len(frames) < 2:
        return True, [f"registration: only {len(frames)} frame(s) found — "
                      f"not checked (is this a strip?)"]
    bottoms = [f[3] for f in frames]
    heights = [f[3] - f[2] for f in frames]
    spread = max(bottoms) - min(bottoms)
    ratio = max(heights) / max(1, min(heights))
    msgs = [f"registration: {len(frames)} frames, baseline spread {spread}px "
            f"({spread / h:.1%}), height ratio {ratio:.2f}"]
    ok = True
    if ratio > STRIP_HEIGHT_RATIO:
        msgs.append(f"NOTE frame heights vary {ratio:.2f}x — fine for a wind-up "
                    f"that reaches overhead, wrong for a walk cycle")
    if not formless and spread > h * BASELINE_SPREAD:
        ok = False
        # The odd one out is the frame furthest from where *most* frames sit,
        # so compare against the median. Comparing against the minimum names
        # whichever frame is lowest — which on a strip with one floating frame
        # is one of the three correct ones.
        mid = sorted(bottoms)[len(bottoms) // 2]
        worst = bottoms.index(max(bottoms, key=lambda b: abs(b - mid)))
        msgs.append(
            f"FAIL the frames do not register: their baselines differ by "
            f"{spread}px, worst at frame {worst + 1} of {len(frames)}. §A's "
            f"clause is 'the subject's feet must sit on the same horizontal "
            f"line in all frames' — played back, this jitters, and no extractor "
            f"can correct it. Re-roll the sheet")
    return ok, msgs


def check(path, material=False, strip=False, formless=False, expect=None,
          scene=False):
    """Gate a sheet against the failures this pipeline has actually had.

    Returns `(ok, [messages])`. Cheap statistics only — but they cover the three
    that have cost real time: art delivered on a painted scene, captions painted
    into the image, and a material swatch with a feature running across it.
    """
    import pygame                                    # local: keeps --dry-run free
    pygame.init()
    pygame.display.set_mode((1, 1))
    img = pygame.image.load(path).convert_alpha()
    w, h = img.get_size()
    luma = _luma

    # Sample rather than walk every pixel: 1536x1024 is 1.5M get_at calls, and a
    # background this large does not hide in a 4x grid.
    step = 4
    dark = total = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            total += 1
            if luma(img.get_at((x, y))) <= BLACK_LUMA:
                dark += 1
    fraction = dark / total

    corners = {}
    for name, (ox, oy) in {
        "top-left": (0, 0),
        "top-right": (w - CORNER_PATCH, 0),
        "bottom-left": (0, h - CORNER_PATCH),
        "bottom-right": (w - CORNER_PATCH, h - CORNER_PATCH),
    }.items():
        acc = n = 0
        for y in range(oy, oy + CORNER_PATCH, 2):
            for x in range(ox, ox + CORNER_PATCH, 2):
                acc += luma(img.get_at((x, y)))
                n += 1
        corners[name] = acc / n

    msgs = [f"size {w}x{h}", f"background {fraction:.0%} of frame"]
    ok = True

    if scene:
        # A plate is judged on whether it reaches the edges, and on captions —
        # never on how much black it holds, which for a night scene is most of
        # it. Everything below this branch would reject it for being a painting.
        box = _content_box(img, w, h)
        if box is None:
            return False, msgs + ["FAIL the plate is empty"]
        bx, by, bw, bh = box
        covers = (bw * bh) / float(w * h)
        msgs.append(f"plate covers {covers:.0%} of the frame")
        if covers < SCENE_MIN_COVER:
            ok = False
            msgs.append(
                f"FAIL the painting does not reach the frame edges — it covers "
                f"{covers:.0%}, inside ({bx}, {by}, {bw}, {bh}). This is a "
                f"letterboxed or bordered picture, and §I0 asks for a full "
                f"bleed: the camera pushes across this plate, so a black bar at "
                f"an edge is a black bar that slides into shot")
        captions = _captions(img, w, h)
        if captions:
            ok = False
            msgs.append(
                "FAIL text looks painted into the plate at y="
                + ", ".join(str(c) for c in captions)
                + " — §0 forbids it, and a caption in a cutscene plate is a "
                  "subtitle the game did not write")
        return ok, msgs

    if material:
        box = _content_box(img, w, h)
        if box is None:
            return False, msgs + ["FAIL the sheet is empty"]
        bx, by, bw, bh = box
        covers = (bw * bh) / float(w * h)
        if covers < MATERIAL_MIN_COVER:
            ok = False
            msgs.append(
                f"FAIL the art covers only {covers:.0%} of the frame — this is "
                f"objects on a background, not a material swatch")
        elif covers < MATERIAL_FULL_COVER:
            # Usable, but the extractor has to crop — so say exactly where.
            msgs.append(
                f"NOTE the swatch does not fill the frame ({covers:.0%}); it is "
                f"letterboxed. Sample inside ({bx}, {by}, {bw}, {bh})")
        ratio, axis = _uniformity(img, w, h, box=box)
        msgs.append(f"uniformity {ratio:.2f} ({axis})")
        if ratio > UNIFORM_MAX_RATIO:
            ok = False
            msgs.append(
                f"FAIL the swatch is {ratio:.1f}x brighter at one end than the "
                f"other, {axis} — it is two materials with a boundary (a dado "
                f"rail, a skirting board, a floor strip), not one patch. It "
                f"cannot be tiled whichever way it is cut; this is the exact "
                f"defect §R1 exists to fix")
        return ok, msgs

    if strip:
        reg_ok, reg_msgs = _registration(img, w, h, formless=formless,
                                         expect=expect)
        msgs += reg_msgs
        ok = ok and reg_ok

    captions = _captions(img, w, h)
    if captions:
        ok = False
        msgs.append(
            "FAIL text labels look painted into the sheet at y="
            + ", ".join(str(c) for c in captions)
            + " — §0 and §R0 both forbid captions; a cutout tool mistakes them "
              "for the subject")

    if fraction < BLACK_FRACTION:
        ok = False
        msgs.append(
            f"FAIL only {fraction:.0%} of the sheet is near-black (want "
            f"{BLACK_FRACTION:.0%}+) — this looks like a painted scene, not "
            f"objects on #000000")
    bright = {k: v for k, v in corners.items() if v > CORNER_LUMA}
    if bright:
        ok = False
        msgs.append(
            "FAIL corners are not black: "
            + ", ".join(f"{k} luma {v:.0f}" for k, v in bright.items()))
    return ok, msgs


def dest_path(out):
    """Absolute path in the painted-source tree for a tree-relative `--out`."""
    if os.path.isabs(out):
        return out
    return os.path.join(SOURCE_ROOTS[0], out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("section", nargs="?",
                    help="section id from the pack, e.g. 1, R1, or S3")
    ap.add_argument("--phase", default="1", choices=sorted(PROMPT_DOCS),
                    help="which prompt pack (1 = map, 2 = animation)")
    ap.add_argument("--list", action="store_true",
                    help="show the sections in the pack and exit")
    ap.add_argument("--out", help="destination, relative to the source art tree")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the request and exit — no key, no network, no cost")
    ap.add_argument("--check", metavar="FILE",
                    help="run the acceptance gates on an existing file and exit")
    ap.add_argument("--strip", action="store_true",
                    help="force the animation-registration gate. Sections in "
                         "STRIP_SECTIONS already use it automatically")
    ap.add_argument("--formless", action="store_true",
                    help="with --strip: the subject has no feet (a puff, a "
                         "projectile), so baseline drift is advisory not fatal")
    ap.add_argument("--scene", action="store_true",
                    help="gate as a full-bleed cutscene plate (see "
                         "SCENE_SECTIONS)")
    ap.add_argument("--material", action="store_true",
                    help="force the material-swatch gate. Sections in "
                         "MATERIAL_SECTIONS already use it automatically")
    ap.add_argument("--size", default=DEFAULT_SIZE)
    ap.add_argument("--quality", default=DEFAULT_QUALITY,
                    choices=["low", "medium", "high", "auto"])
    ap.add_argument("--background", default="opaque",
                    choices=["opaque", "transparent", "auto"],
                    help="opaque is right for this pipeline: the extractors key "
                         "flat black, and a transparent PNG has nothing to key")
    ap.add_argument("--no-style", action="store_true",
                    help="omit the §0 style block (debugging only — drifts style)")
    args = ap.parse_args()

    if args.check:
        ok, msgs = check(args.check, material=args.material,
                         strip=args.strip, formless=args.formless,
                         scene=args.scene)

        print("\n".join(f"  {m}" for m in msgs))
        print("PASS" if ok else "REJECTED")
        return 0 if ok else 1

    pack = load_pack(args.phase)
    if args.list or not args.section:
        print(f"{os.path.relpath(PROMPT_DOCS[args.phase], ROOT)}:")
        # Natural order, so S10 lands after S2 rather than after S1.
        def order(item):
            sid = item[0]
            digits = re.match(r"\D*(\d+)", sid)
            return (not sid[0].isdigit(), sid[0],
                    int(digits.group(1)) if digits else 0, sid)

        for sid, (title, text) in sorted(pack.items(), key=order):
            print(f"  §{sid:<3} {title}   ({len(text)} chars)")
        return 0

    prompt = build_prompt(pack, args.section, not args.no_style)

    if args.dry_run:
        payload = {"model": MODEL, "prompt": prompt, "size": args.size,
                   "quality": args.quality, "n": 1}
        if args.background != "opaque":
            payload["background"] = args.background
        print(f"POST {API_URL}")
        print("Authorization: Bearer <key from .env>")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if not args.out:
        raise SystemExit("--out is required (path relative to the source tree)")

    key = load_key()
    print(f"§{args.section} {pack[args.section][0]}")
    print(f"  {len(prompt)} chars, {args.size}, quality={args.quality} …")
    png = generate(prompt, key, args.size, args.quality, args.background)

    path = dest_path(args.out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(png)
    print(f"  wrote {path} ({len(png) // 1024} KB)")

    sec = args.section.upper()
    ok, msgs = check(path, material=sec in MATERIAL_SECTIONS,
                     scene=args.scene or sec in SCENE_SECTIONS,
                     strip=args.strip or sec in STRIP_SECTIONS,
                     formless=args.formless or sec in FORMLESS_STRIPS,
                     expect=expected_frames(pack[args.section][0]))
    print("\n".join(f"  {m}" for m in msgs))
    if not ok:
        rejected = path.replace(".png", ".rejected.png")
        os.replace(path, rejected)
        print(f"  REJECTED — kept at {rejected} so you can look at it")
        return 1
    print("  PASS — now look at it for painted text before extracting")
    return 0


if __name__ == "__main__":
    sys.exit(main())
