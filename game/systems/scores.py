"""Persistent leaderboard — top players by completion time (fastest first).

Stored as JSON in data/scores.json. Names are unique (case-insensitive) and each
player appears once — but a returning player **keeps their best run**, rather
than being turned away.

That last part was a fix, not the original design. Rejecting a known name meant
a player who beat their own time had no way to record it, so the real board
filled up with "Elad", "Eladi" — the same person working around the block one
character at a time. Letting a better time replace a worse one removes the
reason to do that, and is what "one entry per player" was trying to achieve
anyway.
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


ADDED, IMPROVED, SLOWER, INVALID = "added", "improved", "slower", "invalid"


def add(name, seconds):
    """Record a run. Returns one of ADDED / IMPROVED / SLOWER / INVALID.

    Callers want to *say* which happened — "new best!" and "your record stands"
    are different messages — so this reports the outcome rather than a bare bool.
    """
    name = name.strip()
    if not name:
        return INVALID
    seconds = round(float(seconds), 2)
    entries = load()
    key = name.lower()
    for entry in entries:
        if entry["name"].strip().lower() == key:
            if seconds >= entry["time"]:
                return SLOWER
            entry["time"] = seconds
            entry["name"] = name          # keep the spelling they just typed
            entries.sort(key=lambda e: e["time"])
            _save(entries)
            return IMPROVED
    entries.append({"name": name, "time": seconds})
    entries.sort(key=lambda e: e["time"])
    _save(entries)
    return ADDED


def best_time(name):
    """The stored time for `name`, or None."""
    key = name.strip().lower()
    for e in load():
        if e["name"].strip().lower() == key:
            return e["time"]
    return None


def top(n=8):
    return load()[:n]
