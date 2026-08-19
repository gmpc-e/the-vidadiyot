"""EventBus, Inventory, QuestManager, difficulty, scores."""
import pytest

from game.systems import difficulty, scores
from game.systems.eventbus import EventBus, Events
from game.systems.inventory import Inventory
from game.systems.quests import QuestManager


# ── EventBus ──────────────────────────────────────────────────────────────
def test_emit_reaches_every_subscriber_with_the_payload():
    bus = EventBus()
    seen = []
    bus.on("thing", lambda **kw: seen.append(("a", kw)))
    bus.on("thing", lambda **kw: seen.append(("b", kw)))
    bus.emit("thing", value=3)
    assert seen == [("a", {"value": 3}), ("b", {"value": 3})]


def test_emit_with_no_subscribers_is_not_an_error():
    EventBus().emit("nobody_listens", x=1)


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    seen = []
    off = bus.on("thing", lambda **_: seen.append(1))
    bus.emit("thing")
    off()
    bus.emit("thing")
    assert seen == [1]


def test_a_subscriber_may_unsubscribe_during_dispatch():
    """Dispatch iterates a copy; without that this mutates the list mid-loop."""
    bus = EventBus()
    seen = []

    def once(**_):
        seen.append(1)
        off()

    off = bus.on("thing", once)
    bus.on("thing", lambda **_: seen.append(2))
    bus.emit("thing")
    bus.emit("thing")
    assert seen == [1, 2, 2]


# ── Inventory ─────────────────────────────────────────────────────────────
def test_inventory_fills_to_capacity_then_refuses():
    inv = Inventory(2)
    assert inv.add("key") and inv.add("key")
    assert not inv.add("key")
    assert inv.is_full and inv.count("key") == 2


def test_remove_matches_variant_exactly():
    inv = Inventory(4)
    inv.add("book", "red")
    inv.add("book", "blue")
    assert not inv.remove("book", "green")
    assert inv.remove("book", "blue")
    assert inv.items == [("book", "red")]


def test_remove_without_a_variant_takes_any():
    inv = Inventory(4)
    inv.add("book", "red")
    assert inv.remove("book")
    assert inv.items == []


def test_find_returns_minus_one_when_absent():
    assert Inventory(2).find("key") == -1


def test_drop_random_never_drops_more_than_it_holds():
    inv = Inventory(4)
    inv.add("key")
    dropped = inv.drop_random(3)
    assert len(dropped) == 1 and inv.items == []


# ── QuestManager ──────────────────────────────────────────────────────────
DEFS = {
    "find_keys": {"type": "collect", "item": "key", "required": 2, "title_en": "Keys"},
    "return_books": {"type": "deliver", "item": "book", "required": 2,
                     "title_en": "Books", "unlocked_by": "find_keys"},
}


def test_collecting_advances_the_matching_quest_only():
    bus = EventBus()
    q = QuestManager(bus, dict(DEFS))
    bus.emit(Events.ITEM_COLLECTED, item_type="key")
    bus.emit(Events.ITEM_COLLECTED, item_type="health")
    assert q.get("find_keys") == (1, 2)


def test_quest_completes_and_announces_once():
    bus = EventBus()
    done = []
    bus.on(Events.QUEST_COMPLETED, lambda quest_id, **_: done.append(quest_id))
    q = QuestManager(bus, dict(DEFS))
    for _ in range(3):                       # one more than required
        bus.emit(Events.ITEM_COLLECTED, item_type="key")
    assert q.is_done("find_keys")
    assert done == ["find_keys"], "a finished quest must not re-fire"


def test_a_locked_quest_ignores_progress_until_its_prerequisite_is_done():
    bus = EventBus()
    q = QuestManager(bus, dict(DEFS))
    bus.emit(Events.BOOK_RETURNED)
    assert q.get("return_books") == (0, 2), "books shouldn't count before keys"
    for _ in range(2):
        bus.emit(Events.ITEM_COLLECTED, item_type="key")
    bus.emit(Events.BOOK_RETURNED)
    assert q.get("return_books") == (1, 2)


def test_objectives_hides_locked_quests():
    bus = EventBus()
    q = QuestManager(bus, dict(DEFS))
    assert [o["id"] for o in q.objectives()] == ["find_keys"]


def test_dispose_detaches_from_a_bus_that_outlives_the_run():
    bus = EventBus()
    q = QuestManager(bus, dict(DEFS))
    q.dispose()
    bus.emit(Events.ITEM_COLLECTED, item_type="key")
    assert q.get("find_keys") == (0, 2)


# ── difficulty ────────────────────────────────────────────────────────────
def test_hard_hits_harder_than_easy():
    assert difficulty.get("Easy")["dps"] < difficulty.get("Hard")["dps"]


def test_unknown_difficulty_falls_back_to_normal():
    assert difficulty.get("Nightmare") == difficulty.get("Normal")


@pytest.mark.parametrize("start,d,expected", [
    ("Easy", 1, "Normal"), ("Hard", 1, "Easy"),        # wraps forward
    ("Easy", -1, "Hard"),                              # and backward
])
def test_cycle_wraps(start, d, expected):
    assert difficulty.cycle(start, d) == expected


def test_cycle_from_an_unknown_name_lands_somewhere_valid():
    assert difficulty.cycle("???", 1) in difficulty.ORDER


# ── scores (redirected to tmp by the autouse fixture) ─────────────────────
def test_board_starts_empty_and_sorts_by_time():
    assert scores.load() == []
    scores.add("Slow", 90.0)
    scores.add("Fast", 12.5)
    assert [e["name"] for e in scores.top()] == ["Fast", "Slow"]


def test_names_are_unique_case_insensitively():
    assert scores.add("Roni", 30)
    assert not scores.add("  roni  ", 10), "same name must be refused"
    assert len(scores.load()) == 1


def test_blank_names_are_refused():
    assert not scores.add("   ", 10)


def test_top_limits_the_rows():
    for i in range(5):
        scores.add(f"p{i}", i)
    assert len(scores.top(3)) == 3


def test_a_corrupt_score_file_reads_as_empty(monkeypatch, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    monkeypatch.setattr(scores, "SCORES_PATH", str(bad))
    assert scores.load() == []
