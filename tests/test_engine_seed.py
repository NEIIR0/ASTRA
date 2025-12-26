from astra.game.engine import tick_day
from astra.game.state import default_state


def test_tick_seed_deterministic():
    s = default_state()
    a, _, _ = tick_day(s, seed=123)
    b, _, _ = tick_day(s, seed=123)
    assert a.to_dict() == b.to_dict()
