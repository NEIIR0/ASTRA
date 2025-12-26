from dataclasses import replace
from pathlib import Path

from astra.game.replay import replay_state
from astra.game.rules import apply_rules
from astra.game.state import default_state


def test_rules_clamp_and_emit():
    s = default_state()
    s_bad = replace(s, ship=replace(s.ship, hull=-5, power=-7))

    out, _txt, events = apply_rules(s_bad)
    assert out.ship.hull == 0
    assert out.ship.power == 0

    types = {e["type"] for e in events}
    assert "stat_clamped" in types
    assert "power_down" in types
    assert "game_over" in types


def test_replay_from_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = Path("data") / "profiles" / "dev" / "logbook.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "\n".join(
            [
                '{"type":"command","action":"tick","seed":123}',
                '{"type":"command","action":"move","sector":"Sektor A-1"}',
                "",
            ]
        ),
        encoding="utf-8",
    )

    s = replay_state(profile="dev")
    assert s.ship.sector == "Sektor A-1"
