from astra.game.context import GameContext
from astra.game.registry import run
from astra.game.state import default_state


def test_registry_tick_seed_passthrough():
    s0 = default_state()
    r = run(s0, "tick", ctx=GameContext(seed=123))
    assert r.ok is True
    assert any(e.get("type") == "tick_done" for e in r.events)
