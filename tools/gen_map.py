"""Generate the vertical-slice school map: a tileset PNG + a Tiled .tmx.

We generate the .tmx programmatically so we're not blocked on the Tiled editor.
The layout is the slice defined in the design doc §2.10:
entrance + corridor + 3 classrooms + electrical room.

The tiles themselves are **not** built here — `extract_map_art.py` cuts them out
of the painted material slabs, and this tool calls it so that one run still
produces a matching PNG and .tmx. That pairing matters: the .tmx hard-codes the
tile count and which tile ids are solid, so a tileset built by a different tool
run at a different time is how you get a map with invisible walls.

Collision stays data-driven: solid tiles carry `solid=true`, which `tilemap.py`
reads to build the collision grid.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/gen_map.py
"""
import os
import random
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_map_art import (TILE, FLOOR, WALL, CORR, DOOR, STONE,           # noqa: E402
                             FLOOR_CRACK, FLOOR_STAIN, FLOOR_ROT,
                             TILE_NAMES, SOLID_TILES, build_tileset)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMX_PATH = os.path.join(ROOT, "assets", "maps", "school_slice.tmx")

W, H = 50, 34

# How much of a classroom floor is a damaged variant rather than clean parquet.
# Seeded, so a room looks the same on every run — the same rule `world/decor.py`
# follows for furniture, and for the same reason: a floor that reshuffles every
# time you enter reads as a bug.
WEAR_CHANCE = 0.09
WEAR_SEED = 20260819
WEAR_TILES = (FLOOR_CRACK, FLOOR_STAIN, FLOOR_ROT)


def build_grid():
    rng = random.Random(WEAR_SEED)
    grid = [[WALL] * W for _ in range(H)]

    def carve(x0, y0, x1, y1, val):  # inclusive-exclusive
        for y in range(y0, y1):
            for x in range(x0, x1):
                grid[y][x] = val

    # central horizontal corridor (rows 15-18)
    carve(2, 15, 48, 19, CORR)
    # three classrooms along the top (rows 2-13)
    carve(3, 2, 16, 14, FLOOR)     # classroom A
    carve(19, 2, 32, 14, FLOOR)    # classroom B
    carve(35, 2, 48, 14, FLOOR)    # classroom C
    # entrance hall (bottom-center), opens straight up into the corridor
    carve(21, 19, 30, 32, FLOOR)
    # electrical room (bottom-left) — bare stone, so leaving the teaching wing
    # is legible underfoot rather than only on the map
    carve(3, 20, 14, 31, STONE)

    # doorways: punch the wall row between each classroom and the corridor
    for dx in (9, 25, 41):
        grid[14][dx] = DOOR
        grid[14][dx + 1] = DOOR
    # electrical room door up into the corridor
    grid[19][7] = DOOR
    grid[19][8] = DOOR

    # scatter damaged parquet through the classrooms so the floor stops reading
    # as wallpaper. Corridor and stone are left alone: the checkerboard already
    # carries its own variation, and the variants are parquet.
    for y in range(H):
        for x in range(W):
            if grid[y][x] == FLOOR and rng.random() < WEAR_CHANCE:
                grid[y][x] = rng.choice(WEAR_TILES)

    return grid


# object layer: player start + room regions. Classrooms carry a color for the
# book-matching system (§2.8); other rooms have no color.
# fields: name, room_type, tx, ty, tw, th, color
ROOMS = [
    ("classroom_a",   "classroom",  3,  2, 13, 12, "red"),
    ("classroom_b",   "classroom", 19,  2, 13, 12, "blue"),
    ("classroom_c",   "classroom", 35,  2, 13, 12, "green"),
    ("entrance",      "entrance",  21, 19,  9, 13, None),
    ("electrical",    "utility",    3, 20, 11, 11, None),
    ("corridor",      "corridor",   2, 15, 46,  4, None),
]
PLAYER_START = (25, 25)   # tile coords, inside the entrance

# locked classroom doors: room_id, color, doorway tile (top-left), width in tiles
# each occupies the 2-tile gap punched in row 14 above the corridor
DOORS = [
    ("classroom_a", "red",   9, 14, 2),
    ("classroom_b", "blue", 25, 14, 2),
    ("classroom_c", "green",41, 14, 2),
]

# item spawn points. fields: item, variant, tx, ty
#
# ⚠️ **No keys here either**, since 2026-08-20: the first three monsters killed
# hand one over (`settings.KEYS_FROM_KILLS`). Picking three keys off the floor
# was an errand done before the game started; now the door is opened by the
# fight, not by the walk.
#
# ⚠️ **No books here.** They used to lie in the corridor behind a "guarded" flag,
# which meant the objective was visible and inert from the first minute and the
# fight that freed it happened somewhere else entirely. A book is now *carried by
# the teacher* who holds its classroom and drops where that teacher dies — so the
# reward appears in the room, at the moment the room is won, and the walk to the
# locker is the victory lap. Keys still live in accessible areas, never behind a
# locked classroom door (§3.7.1).
SPAWNS = [
    # ⚠️ **One potion in the whole level.** There were three, and with health
    # regenerating on top of them a run never really ran out of health — the
    # bar was a formality. One makes it a decision: spend it now, or carry it to
    # the room you know is coming.
    ("health", None,  8, 25),  # the only potion — hidden in the electrical room
]

# monsters. fields: drops(book variant or None), kind, hits(strength), tx, ty
# A monster with `drops` is carrying that classroom's book and lets go of it when
# it dies. The corridor pair carry nothing — they are the toll on the way there.
# ranged monsters (no melee; contact is harmless — only their casts hurt).
# guards may be None: those just occupy their spot as a threat.
# Every book is guarded, so each of the three is a fight before it is a delivery
# — the level used to be finishable in about a minute with one book unguarded.
# ⚠️ **Who lives where is a range decision, not a flavour one.** The fire and web
# casters reach 250-260px and kite away below 120; a classroom is barely wider
# than that, so indoors they spend the fight backed into a corner with nothing
# to kite into. The teachers reach 190 and shuffle, which is a fight a room can
# hold. So: teachers inside, Snir and Little Terror out in the corridors where
# the range they were tuned for finally has somewhere to go.
MONSTERS = [
    (None,    "webber", 5, 13, 17),  # Little Snir works the corridor, left
    (None,    "caster", 5, 33, 17),  # Little Terror works the corridor, right
    (None,    "webber", 5, 25, 26),  # Little Snir again, in the entrance
    # ⚠️ The electrical room, bottom-left, held a potion and nothing else — the
    # one room on the map you could walk into and out of for free. A caster
    # posted here means the potion has to be *taken*.
    (None,    "caster", 5,  8, 25),  # Little Terror guards the electrical room
    ("red",   "teacher_f", 5,  9,  7),  # the teacher holds classroom A — and its book
    ("blue",  "teacher_m", 5, 25,  7),  # the schoolmaster holds classroom B
    ("green", "teacher_f", 5, 41,  7),  # ...and the teacher again in classroom C
]


def write_tmx(grid, ts_w, ts_h):
    tile_count = len(TILE_NAMES)
    # tile *ids* are 0-based; the grid's GIDs are 1-based
    solid_tiles = "\n".join(
        f'  <tile id="{gid - 1}">\n'
        f'   <properties>\n'
        f'    <property name="solid" type="bool" value="true"/>\n'
        f'   </properties>\n'
        f'  </tile>' for gid in SOLID_TILES)
    csv = ",\n".join(",".join(str(g) for g in row) for row in grid)

    objs = []
    oid = 1
    px, py = PLAYER_START[0] * TILE, PLAYER_START[1] * TILE
    objs.append(f'  <object id="{oid}" name="player_start" type="spawn" x="{px}" y="{py}"/>')
    oid += 1
    for name, rtype, tx, ty, tw, th, color in ROOMS:
        props = [f'<property name="room_type" value="{rtype}"/>']
        if color:
            props.append(f'<property name="color" value="{color}"/>')
        objs.append(
            f'  <object id="{oid}" name="{name}" type="room" '
            f'x="{tx*TILE}" y="{ty*TILE}" width="{tw*TILE}" height="{th*TILE}">\n'
            f'   <properties>{"".join(props)}</properties>\n'
            f'  </object>'
        )
        oid += 1
    for room_id, color, tx, ty, tw in DOORS:
        objs.append(
            f'  <object id="{oid}" name="door_{room_id}" type="door" '
            f'x="{tx*TILE}" y="{ty*TILE}" width="{tw*TILE}" height="{TILE}">\n'
            f'   <properties>'
            f'<property name="room_id" value="{room_id}"/>'
            f'<property name="color" value="{color}"/>'
            f'</properties>\n'
            f'  </object>'
        )
        oid += 1
    for item, variant, tx, ty in SPAWNS:
        cx, cy = tx * TILE + TILE // 2, ty * TILE + TILE // 2
        props = [f'<property name="item" value="{item}"/>']
        if variant:
            props.append(f'<property name="variant" value="{variant}"/>')
        objs.append(
            f'  <object id="{oid}" name="spawn_{item}" type="spawn" x="{cx}" y="{cy}">\n'
            f'   <point/>\n'
            f'   <properties>{"".join(props)}</properties>\n'
            f'  </object>'
        )
        oid += 1
    for drops, kind, hits, tx, ty in MONSTERS:
        cx, cy = tx * TILE + TILE // 2, ty * TILE + TILE // 2
        props = [f'<property name="kind" value="{kind}"/>',
                 f'<property name="hits" type="int" value="{hits}"/>']
        if drops:
            props.insert(0, f'<property name="drops" value="{drops}"/>')
        objs.append(
            f'  <object id="{oid}" name="monster_{drops or kind}" type="monster" x="{cx}" y="{cy}">\n'
            f'   <point/>\n'
            f'   <properties>{"".join(props)}</properties>\n'
            f'  </object>'
        )
        oid += 1
    objects = "\n".join(objs)

    tmx = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{W}" height="{H}" tilewidth="{TILE}" tileheight="{TILE}" infinite="0" nextlayerid="3" nextobjectid="{oid}">
 <tileset firstgid="1" name="school" tilewidth="{TILE}" tileheight="{TILE}" tilecount="{tile_count}" columns="{tile_count}">
  <image source="../tilesets/school.png" width="{ts_w}" height="{ts_h}"/>
{solid_tiles}
 </tileset>
 <layer id="1" name="ground" width="{W}" height="{H}">
  <data encoding="csv">
{csv}
</data>
 </layer>
 <objectgroup id="2" name="meta">
{objects}
 </objectgroup>
</map>
'''
    os.makedirs(os.path.dirname(TMX_PATH), exist_ok=True)
    with open(TMX_PATH, "w") as f:
        f.write(tmx)


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))         # extraction needs convert_alpha()
    ts_w, ts_h = build_tileset()[:2]
    grid = build_grid()
    write_tmx(grid, ts_w, ts_h)
    print(f"wrote the tileset ({ts_w}x{ts_h}, {len(TILE_NAMES)} tiles)")
    print(f"wrote {TMX_PATH} ({W}x{H} tiles = {W*TILE}x{H*TILE}px)")


if __name__ == "__main__":
    main()
