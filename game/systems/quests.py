"""QuestManager: data-driven objectives, wired through the EventBus.

Subscribes to gameplay events (item_collected today; book_returned, door_unlocked
later), increments per-quest counters, and emits quest_completed. The HUD reads
objective state from here. Adding Chapter 2 means adding JSON, not code (§3.6).
"""
import json

from game.systems.eventbus import Events


class QuestManager:
    def __init__(self, bus, defs, lang="en"):
        self.bus = bus
        self.defs = defs            # ordered dict: quest_id -> definition
        self.lang = lang
        self.state = {qid: {"progress": 0, "done": False} for qid in defs}

        self._unsubs = [bus.on(Events.ITEM_COLLECTED, self._on_item_collected),
                        bus.on(Events.BOOK_RETURNED, self._on_book_returned)]

        for qid in defs:
            if self._is_active(qid):
                bus.emit(Events.QUEST_STARTED, quest_id=qid)

    @classmethod
    def from_file(cls, bus, path, lang="en"):
        with open(path) as f:
            return cls(bus, json.load(f), lang=lang)

    def dispose(self):
        """Unsubscribe from the bus. The bus outlives a run, this manager doesn't."""
        for off in self._unsubs:
            off()
        self._unsubs = []

    # ── event handlers ───────────────────────────────────────────────────--
    def _on_item_collected(self, item_type, **_):
        self._advance("collect", item_type)

    def _on_book_returned(self, **_):
        self._advance("deliver", "book")

    def _advance(self, qtype, item):
        """Bump any active, matching quest of `qtype` for `item` by one."""
        for qid, d in self.defs.items():
            if d.get("type") != qtype or d.get("item") != item:
                continue
            if not self._is_active(qid) or self.state[qid]["done"]:
                continue
            st = self.state[qid]
            st["progress"] += 1
            if st["progress"] >= d["required"]:
                st["done"] = True
                self.bus.emit(Events.QUEST_COMPLETED, quest_id=qid)

    # ── queries ────────────────────────────────────────────────────────────
    def _is_active(self, qid):
        """A quest is active once its prerequisite (if any) is complete."""
        req = self.defs[qid].get("unlocked_by")
        return req is None or self.state.get(req, {}).get("done", False)

    def _title(self, qid):
        d = self.defs[qid]
        return d.get(f"title_{self.lang}") or d.get("title_en") or qid

    def objectives(self):
        """Active/visible objectives for the HUD, in definition order."""
        out = []
        for qid, d in self.defs.items():
            if not self._is_active(qid):
                continue
            st = self.state[qid]
            out.append({
                "id": qid,
                "title": self._title(qid),
                "progress": st["progress"],
                "required": d.get("required", 1),
                "done": st["done"],
            })
        return out

    def get(self, qid):
        """(progress, required) for a quest — for HUD counters."""
        st = self.state[qid]
        return st["progress"], self.defs[qid].get("required", 1)

    def is_done(self, qid):
        return self.state.get(qid, {}).get("done", False)

    @property
    def all_complete(self):
        return all(s["done"] for s in self.state.values())
