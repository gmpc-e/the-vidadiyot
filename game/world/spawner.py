"""Spawner: turn map spawn objects into live pickups and monsters.

Reads the objects placed in the .tmx. A monster with a `guards` property protects
the book of that variant (flagged `guarded`, uncollectable until it dies). A
monster's `kind` selects the class: "melee" (green Vidadiya) or "caster" (the
fireball-throwing Little Terror).
"""
from game.entities.pickup import Pickup
from game.entities.monster import Monster, make_fire_caster, make_web_caster


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


def spawn_monsters(tilemap, pickups, sprites):
    """sprites: dict {"melee": Surface, "caster": Surface}."""
    monsters = []
    for obj in tilemap.objects():
        if getattr(obj, "type", None) != "monster":
            continue
        guards = obj.properties.get("guards")
        kind = obj.properties.get("kind", "melee")
        hits = obj.properties.get("hits")
        hits = int(hits) if hits is not None else None
        sprite = sprites.get(kind, sprites.get("melee"))
        if kind == "caster":
            monsters.append(make_fire_caster(obj.x, obj.y, hits=hits, guards=guards, sprite=sprite))
        elif kind == "webber":
            monsters.append(make_web_caster(obj.x, obj.y, hits=hits, guards=guards, sprite=sprite))
        else:
            monsters.append(Monster(obj.x, obj.y, hits=hits, guards=guards, sprite=sprite))
        if guards:
            for p in pickups:
                if p.item_type == "book" and p.variant == guards:
                    p.guarded = True
    return monsters
