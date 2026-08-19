"""Difficulty presets — multipliers applied to a few gameplay dials.

Kept tiny and data-only so tuning is one edit. PlayState reads the current
preset (chosen in the menu, stored on Game.difficulty) and scales contact damage,
the per-kill speed ramp, and potion healing.
"""
ORDER = ["Easy", "Normal", "Hard"]

# Kept deliberately simple: difficulty just scales how much damage monsters deal
# (contact + fireballs). Everything else stays the same across difficulties.
PRESETS = {
    "Easy":   {"dps": 0.5, "speed_step": 1.0, "potion": 1.0},
    "Normal": {"dps": 1.0, "speed_step": 1.0, "potion": 1.0},
    "Hard":   {"dps": 1.6, "speed_step": 1.0, "potion": 1.0},
}


def get(name):
    return PRESETS.get(name, PRESETS["Normal"])


def cycle(name, direction):
    i = (ORDER.index(name) + direction) % len(ORDER) if name in ORDER else 1
    return ORDER[i]
