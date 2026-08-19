"""Pub/sub EventBus — the glue between every system. See design doc §3.4.

Almost every feature is "X happens -> several unrelated systems react."
Wiring that with direct references rots fast; instead systems emit named
events and subscribe to the ones they care about, knowing nothing of each other.
"""
from collections import defaultdict


class Events:
    """Canonical event names. Use these constants, never raw strings."""
    ITEM_COLLECTED   = "item_collected"
    BOOK_RETURNED    = "book_returned"
    DOOR_UNLOCKED    = "door_unlocked"
    FUSE_INSERTED    = "fuse_inserted"
    POWER_RESTORED   = "power_restored"
    ALARM_TRIGGERED  = "alarm_triggered"
    NOISE_MADE       = "noise_made"
    PLAYER_SPOTTED   = "player_spotted"
    PLAYER_CAUGHT    = "player_caught"
    PLAYER_HIDDEN    = "player_hidden"
    QUEST_STARTED    = "quest_started"
    QUEST_COMPLETED  = "quest_completed"
    PA_ACTIVATED     = "pa_activated"
    GATE_OPENED      = "gate_opened"
    RANDOM_EVENT_FIRED = "random_event_fired"


class EventBus:
    def __init__(self):
        self._subs = defaultdict(list)

    def on(self, event_name, callback):
        """Subscribe callback to an event. Returns an unsubscribe function."""
        self._subs[event_name].append(callback)
        return lambda: self._subs[event_name].remove(callback)

    def emit(self, event_name, **payload):
        # iterate a copy so subscribers may safely unsubscribe during dispatch
        for cb in list(self._subs[event_name]):
            cb(**payload)
