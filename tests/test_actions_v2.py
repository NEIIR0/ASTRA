from astra.game.actions import MoveSector, TickDay, run_action
from astra.game.state import default_state


def test_actions_v2_tick_and_move():
    s0 = default_state()

    r1 = run_action(s0, TickDay(seed=123))
    assert r1.ok is True
    assert any(e.get("type") == "tick_done" for e in r1.events)

    r2 = run_action(r1.state, MoveSector(sector="Sektor A-1"))
    assert r2.ok is True
    assert any(e.get("type") == "sector_moved" for e in r2.events)
