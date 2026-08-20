"""Difficulty presets — multipliers applied to a few gameplay dials.

Kept tiny and data-only so tuning is one edit. PlayState reads the current
preset (chosen in the menu, stored on Game.difficulty) and scales contact damage,
the per-kill speed ramp, potion healing, monster health and health regen.
"""
ORDER = ["Easy", "Normal", "Hard"]

# Three dials, and they pull in different directions on purpose:
#
# - `dps`   how hard monsters hit.
# - `hp`    how much punishment monsters *take*. ⚠️ New: Normal was too easy,
#           and the reason was that difficulty only ever changed incoming
#           damage — a monster died in the same number of swings whatever you
#           picked, so the level was the same length on Hard as on Easy. Normal
#           is +20% on the tuned base and the other two are set around it.
# - `regen` how fast the player heals back up. Health regeneration was doing
#           most of the work of an easy mode by itself; slowing it is what makes
#           a fight *cost* something after it ends.
PRESETS = {
    "Easy":   {"dps": 0.5, "speed_step": 1.0, "potion": 1.0, "hp": 0.85, "regen": 1.4},
    "Normal": {"dps": 1.0, "speed_step": 1.0, "potion": 1.0, "hp": 1.20, "regen": 1.0},
    "Hard":   {"dps": 1.6, "speed_step": 1.0, "potion": 1.0, "hp": 1.45, "regen": 0.6},
}


def get(name):
    return PRESETS.get(name, PRESETS["Normal"])


def cycle(name, direction):
    i = (ORDER.index(name) + direction) % len(ORDER) if name in ORDER else 1
    return ORDER[i]
