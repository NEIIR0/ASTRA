import json
from pathlib import Path

from astra.game.engine import tick_day
from astra.game.state import default_state


def _load(name: str) -> dict:
    p = Path(__file__).parent / name
    return json.loads(p.read_text("utf-8"))


def test_golden_tick_seed_123():
    gold = _load("tick_seed_123.json")
    s0 = default_state()
    s1, _txt, events = tick_day(s0, seed=123)
    assert events == gold["events"]
    assert s1.to_dict() == gold["state"]


def test_golden_tick_seed_999():
    gold = _load("tick_seed_999.json")
    s0 = default_state()
    s1, _txt, events = tick_day(s0, seed=999)
    assert events == gold["events"]
    assert s1.to_dict() == gold["state"]
