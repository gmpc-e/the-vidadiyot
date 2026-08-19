"""Generate the vertical-slice school map: a tileset PNG + a Tiled .tmx.

We generate the .tmx programmatically so we're not blocked on the Tiled editor.
The layout is the slice defined in the design doc §2.10:
entrance + corridor + 3 classrooms + electrical room.

Tiles are simple flat colors — art comes later. Collision is data-driven: the
WALL tile carries a `solid=true` property that `tilemap.py` reads.

Run:  SDL_VIDEODRIVER=dummy ./venv/bin/python tools/gen_map.py
"""
import os
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILESET_PNG = os.path.join(ROOT, "assets", "tilesets", "school.png")
TMX_PATH = os.path.join(ROOT, "assets", "maps", "school_slice.tmx")

TILE = 32
W, H = 50, 34

# tile GIDs (1-based, matching tileset column order below)
FLOOR, WALL, CORR, DOOR = 1, 2, 3, 4

COLORS = {
    FLOOR: (46, 46, 54),    # classroom / room floor
    WALL:  (74, 70, 82),    # solid
    CORR:  (38, 40, 50),    # corridor floor (a touch darker)
    DOOR:  (122, 92, 58),   # doorway threshold (walkable)
}


def draw_tileset():
    """A 4-tile horizontal strip, 32px each."""
    surf = pygame.Surface((TILE * 4, TILE), pygame.SRCALPHA)
    for gid, color in COLORS.items():
        x = (gid - 1) * TILE
        rect = pygame.Rect(x, 0, TILE, TILE)
        surf.fill(color, rect)
        if gid == WALL:
            # bevel: lighter top edge, darker bottom, for a bit of depth
            pygame.draw.line(surf, (96, 92, 104), (x, 0), (x + TILE - 1, 0))
            pygame.draw.line(surf, (52, 48, 60), (x, TILE - 1), (x + TILE - 1, TILE - 1))
        else:
            # subtle inner border so floor tiles read as a grid
            pygame.draw.rect(surf, tuple(max(0, c - 8) for c in color), rect, 1)
    os.makedirs(os.path.dirname(TILESET_PNG), exist_ok=True)
    pygame.image.save(surf, TILESET_PNG)
    return surf.get_width(), surf.get_height()


def build_grid():
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
    # electrical room (bottom-left)
    carve(3, 20, 14, 31, FLOOR)

    # doorways: punch the wall row between each classroom and the corridor
    for dx in (9, 25, 41):
        grid[14][dx] = DOOR
        grid[14][dx + 1] = DOOR
    # electrical room door up into the corridor
    grid[19][7] = DOOR
    grid[19][8] = DOOR

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

# item spawn points. Keys + books live in ACCESSIBLE areas (corridor/entrance),
# never behind a locked classroom door (§3.7.1). fields: item, variant, tx, ty
SPAWNS = [
    ("key",  None,   5, 17),   # corridor, far left
    ("key",  None,  45, 17),   # corridor, far right
    ("key",  None,  25, 29),   # entrance
    ("book", "red",  30, 17),  # -> classroom A (corridor, right)
    ("book", "blue", 10, 17),  # -> classroom B (corridor, left)
    ("book", "green", 25, 22), # -> classroom C (entrance, on the way in)
    ("health", None, 20, 16),  # potion in the corridor
    ("health", None, 38, 17),  # potion in the corridor, right side
    ("health", None,  8, 25),  # potion in the electrical room
]

# guardian monsters. Each guards a book (by variant) and won't let it be taken
# until killed. fields: guards(variant), kind(melee|caster), hits(strength), tx, ty
# ranged monsters (no melee; contact is harmless — only their casts hurt).
# guards may be None: those just occupy their spot as a threat.
# Every book is guarded, so each of the three is a fight before it is a delivery
# — the level used to be finishable in about a minute with one book unguarded.
MONSTERS = [
    ("blue",  "webber", 5, 13, 17),  # Little Snir (webs) guards the blue book (corridor left)
    ("red",   "caster", 5, 33, 17),  # Little Terror (fireballs) guards the red book (corridor right)
    ("green", "webber", 5, 25, 26),  # Little Snir guards the green book (entrance)
    (None,    "caster", 5,  9,  7),  # fireball monster inside classroom A
    (None,    "caster", 5, 25,  7),  # fireball monster inside classroom B
    (None,    "caster", 5, 41,  7),  # fireball monster inside classroom C
]


def write_tmx(grid, ts_w, ts_h):
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
    for guards, kind, hits, tx, ty in MONSTERS:
        cx, cy = tx * TILE + TILE // 2, ty * TILE + TILE // 2
        props = [f'<property name="kind" value="{kind}"/>',
                 f'<property name="hits" type="int" value="{hits}"/>']
        if guards:
            props.insert(0, f'<property name="guards" value="{guards}"/>')
        objs.append(
            f'  <object id="{oid}" name="monster_{guards or kind}" type="monster" x="{cx}" y="{cy}">\n'
            f'   <point/>\n'
            f'   <properties>{"".join(props)}</properties>\n'
            f'  </object>'
        )
        oid += 1
    objects = "\n".join(objs)

    tmx = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{W}" height="{H}" tilewidth="{TILE}" tileheight="{TILE}" infinite="0" nextlayerid="3" nextobjectid="{oid}">
 <tileset firstgid="1" name="school" tilewidth="{TILE}" tileheight="{TILE}" tilecount="4" columns="4">
  <image source="../tilesets/school.png" width="{ts_w}" height="{ts_h}"/>
  <tile id="1">
   <properties>
    <property name="solid" type="bool" value="true"/>
   </properties>
  </tile>
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
    ts_w, ts_h = draw_tileset()
    grid = build_grid()
    write_tmx(grid, ts_w, ts_h)
    print(f"wrote {TILESET_PNG} ({ts_w}x{ts_h})")
    print(f"wrote {TMX_PATH} ({W}x{H} tiles = {W*TILE}x{H*TILE}px)")


if __name__ == "__main__":
    main()
