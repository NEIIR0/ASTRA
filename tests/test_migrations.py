import json
from pathlib import Path

from astra.game.migrations import migrate_dict
from astra.game.state import GameState


def _read(name: str) -> dict:
    p = Path("tests/fixtures") / name
    return json.loads(p.read_text("utf-8"))


def test_migrate_v1_to_v3():
    d = _read("state_v1.json")
    out = migrate_dict(d)
    assert out["schema_version"] == 3
    assert "last_seed" in out
    s = GameState.from_dict(out)
    ids = {q.quest_id for q in s.quests}
    assert {"q_doctor_once", "q_ticks_3", "q_airi_status"} <= ids


def test_migrate_v2_to_v3():
    d = _read("state_v2.json")
    out = migrate_dict(d)
    assert out["schema_version"] == 3
    assert "last_seed" in out
    s = GameState.from_dict(out)
    assert s.schema_version == 3
