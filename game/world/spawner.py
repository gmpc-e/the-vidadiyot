"""Spawner: turn map spawn objects into live pickups and monsters.

Reads the objects placed in the .tmx. A monster with a `drops` property is
**carrying** that classroom's book and lets go of it where it dies (§5); the
older `guards` property instead unlocks a book already lying on the floor, and
is kept for maps that still place one.

A monster's `kind` selects the class: "melee" (green Vidadiya), "caster" (the
fireball-throwing Little Terror), "webber" (Little Snir), or "teacher_f" /
"teacher_m" (the two tome-throwing staff who hold the classrooms).
"""
from game.core.assets import load
from game.entities.pickup import Pickup
from game.entities.monster import (Monster, make_fire_caster, make_teacher,
                                   make_web_caster)


def _pose(prefix, name):
    """One extra stance, as a **strip if there is one** and a single pose if not.

    `assets.load` returns None for a missing file — deliberately, since
    `assets/` is regenerated from source that lives outside the repo — and
    `set_frames` drops a None pose. So a checkout that has never run the
    extractors degrades to "this monster does not animate", not to a crash.

    ⚠️ `prefix` is the **art** name, not the map's `kind`. They differ: the map
    says "caster", the files say `terror_`. Deriving one from the other is what
    broke the select screen when a warrior was renamed, so it is passed in.
    """
    strip = []
    while True:
        frame = load(f"sprites/{prefix}_{name}_{len(strip)}.png")
        if frame is None:
            break
        strip.append(frame)
    return strip or load(f"sprites/{prefix}_{name}.png")


def spawn_pickups(tilemap):
    pickups = []
    for obj in tilemap.objects():
        if getattr(obj, "type", None) != "spawn":
            continue
        item = obj.properties.get("item")
        if item:
            variant = obj.properties.get("variant")
            pickups.append(Pickup(obj.x, obj.y, item, variant))
    return pickups


def spawn_monsters(tilemap, pickups, sprites, poses=None):
    """sprites: dict keyed by the same `kind` strings the map uses.

    `poses` optionally maps a map `kind` to `(art_prefix, stance_names)` — each
    stance loaded as `sprites/<prefix>_<name>_<i>.png` (a strip) or
    `sprites/<prefix>_<name>.png` (one pose). A kind with no entry keeps its
    single sprite and never changes stance, which is what every monster did
    before the teachers arrived.
    """
    monsters = []
    for obj in tilemap.objects():
        if getattr(obj, "type", None) != "monster":
            continue
        guards = obj.properties.get("guards")
        drops = obj.properties.get("drops")
        kind = obj.properties.get("kind", "melee")
        hits = obj.properties.get("hits")
        hits = int(hits) if hits is not None else None
        sprite = sprites.get(kind, sprites.get("melee"))
        if kind == "caster":
            monsters.append(make_fire_caster(obj.x, obj.y, hits=hits, guards=guards,
                                             sprite=sprite, drops=drops))
        elif kind == "webber":
            monsters.append(make_web_caster(obj.x, obj.y, hits=hits, guards=guards,
                                            sprite=sprite, drops=drops))
        elif kind in ("teacher_f", "teacher_m"):
            monsters.append(make_teacher(obj.x, obj.y, female=kind.endswith("_f"),
                                         hits=hits, guards=guards, sprite=sprite,
                                         drops=drops))
        else:
            monsters.append(Monster(obj.x, obj.y, hits=hits, guards=guards,
                                    sprite=sprite, drops=drops))
        prefix, extra = (poses or {}).get(kind, (None, ()))
        if extra:
            monsters[-1].set_frames(idle=sprite, **{
                name: _pose(prefix, name) for name in extra})
        if guards:
            for p in pickups:
                if p.item_type == "book" and p.variant == guards:
                    p.guarded = True
    return monsters
