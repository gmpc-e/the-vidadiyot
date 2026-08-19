"""Inventory: what the player is currently carrying.

Items are stored as (type, variant) records so books keep their color (§2.8).
Bounded by CARRY_CAPACITY — a full inventory forces return trips (§3.10). Distinct
from quest progress: the QuestManager counts *events* so using/dropping an item
doesn't undo an objective.
"""
import random


class Inventory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = []           # list of (type, variant) tuples

    @property
    def is_full(self):
        return len(self.items) >= self.capacity

    def add(self, item_type, variant=None):
        if self.is_full:
            return False
        self.items.append((item_type, variant))
        return True

    def count(self, item_type):
        return sum(1 for t, _ in self.items if t == item_type)

    def find(self, item_type, variant=None):
        """Index of the first matching item, or -1. variant=None matches any."""
        for i, (t, v) in enumerate(self.items):
            if t == item_type and (variant is None or v == variant):
                return i
        return -1

    def remove(self, item_type, variant=None):
        """Remove one matching item; returns True if removed."""
        idx = self.find(item_type, variant)
        if idx < 0:
            return False
        self.items.pop(idx)
        return True

    def drop_random(self, n):
        """Remove up to n random items; returns the list dropped (for catch)."""
        dropped = []
        for _ in range(min(n, len(self.items))):
            dropped.append(self.items.pop(random.randrange(len(self.items))))
        return dropped
