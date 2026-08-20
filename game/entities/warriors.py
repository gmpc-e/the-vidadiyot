"""Playable warriors — who you take into the school, and what they can do.

Each entry is pure data: the sprite set to animate, the numbers that shape how
the character *plays*, and (optionally) an active power bound to a key.

**The numbers here drive the game.** The painted cards carry ATK/DEF/SPD, but
those are flavour — a stat that displays and does nothing is a trap (a kid
compares two warriors by ATK and is wrong). So the card's stat line is kept for
the character screen under `card`, while `speed`, `max_health` and `reach` are
the real, tuned values the simulation reads. Keep the two consistent in spirit:
Roni's SPD 22 is why she is the fast one, Wallad's ATK 32 is why his longsword
takes two pips a swing.

`weapon` is what the attack key does: "melee" sweeps an arc within `reach`,
"knife" throws a blade across the room. They are balanced against each other by
**damage per second**, not damage per hit: `damage / cooldown`. Reaching from
safety costs you roughly a third of the throughput, and every weapon is paced —
an unpaced one is worth whatever the player's mashing speed happens to be.
"""
import settings


WARRIORS = [
    {
        "id": "wallad",
        "name": "Wallad",
        "title": "The Knight",
        "blurb": ["A warrior of light and honour.",
                  "He stands between darkness and the innocent."],
        "sprites": "knight",          # assets/sprites/knight_{idle,walk,attack,hurt}.png
        "portrait": "knight_portrait",   # full-size art for the select screen
        "menu": "wallad_menu",           # the select screen's own cut-out
        "card": {"HP": 5, "ATK": 32, "DEF": 18, "SPD": 14},
        # sturdy and long-armed: the sword out-reaches everything else in the game
        "speed": 165,
        "max_health": 100,
        "reach": 52,
        "weapon": "melee",
        "damage": 2,              # ATK 32: a longsword takes two pips a swing
        "cooldown": settings.SWING_COOLDOWN,   # -> 5.6 pips/sec, in reach 52
        "power": None,
        "power_name": "Longsword",
        "power_help": "[Space] A heavy two-pip swing, the longest reach in the"
                      " game, and the deepest health bar behind it.",
    },
    {
        "id": "roni",
        "name": "Roni",
        "title": "The Warrior Princess",
        "blurb": ["A fearless princess destined to protect",
                  "the innocent and defeat the darkness."],
        "sprites": "roni",
        "portrait": "roni_portrait",
        "menu": "roni_menu",
        "card": {"HP": 5, "ATK": 30, "DEF": 18, "SPD": 22},
        # quick and glassy, and she fights at range — the trade is damage
        "speed": 196,
        "max_health": 85,
        "reach": settings.KNIFE_RANGE,
        "weapon": "knife",
        "damage": 0.68,           # ATK 30: a thrown blade. ⚠️ Was 0.85 — a 20%
                                  # trim, because range plus mobility plus Zina
                                  # was already the stronger side of the trade
        "cooldown": settings.KNIFE_COOLDOWN,   # -> 3.0 pips/sec, from 250 away
        "power": "zina",
        "power_name": "Royal Blade",
        "power_help": "[Space] Throw knives across the room — unlimited, one pip"
                      " each.  [Z] Send Zina: one bite kills, three a level.",
    },
]

BY_ID = {w["id"]: w for w in WARRIORS}
DEFAULT_ID = "wallad"


def get(warrior_id):
    return BY_ID.get(warrior_id, BY_ID[DEFAULT_ID])
