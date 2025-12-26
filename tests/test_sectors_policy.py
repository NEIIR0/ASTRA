from astra.game.actions import apply_action
from astra.game.state import default_state


def test_move_unknown_sector_blocked():
    s0 = default_state()
    s1, txt, events = apply_action(s0, "move", sector="NOPE-404")
    # state should remain unchanged
    assert s1.ship.sector == s0.ship.sector
    assert any(e["type"] == "sector_unknown" for e in events) or any(e["type"] == "action_blocked" for e in events)
    assert any("policy blocked" in t.lower() for t in txt)
