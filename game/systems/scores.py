"""Persistent leaderboard — top players by completion time (fastest first).

Stored as JSON in data/scores.json. Names are unique (case-insensitive): a name
already on the board is rejected, so each player appears once.
"""
import json
import os
import sys


def _user_data_dir():
    """A per-user writable dir (each profile keeps its own leaderboard).

    The app bundle itself is read-only, so scores can't live beside it.
    """
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/Vidadiyot")
    elif os.name == "nt":
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Vidadiyot")
    else:
        base = os.path.expanduser("~/.local/share/Vidadiyot")
    return base


SCORES_PATH = os.path.join(_user_data_dir(), "scores.json")


def load():
    try:
        with open(SCORES_PATH) as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(entries):
    os.makedirs(os.path.dirname(SCORES_PATH), exist_ok=True)
    with open(SCORES_PATH, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def name_taken(name):
    key = name.strip().lower()
    return any(e["name"].strip().lower() == key for e in load())


def add(name, seconds):
    """Add a result. Returns True if saved, False if the name already exists."""
    name = name.strip()
    if not name or name_taken(name):
        return False
    entries = load()
    entries.append({"name": name, "time": round(float(seconds), 2)})
    entries.sort(key=lambda e: e["time"])
    _save(entries)
    return True


def top(n=8):
    return load()[:n]
