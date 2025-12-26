from astra.game.state import default_state
from astra.game.validate import validate_state


def test_validate_default_ok():
    assert validate_state(default_state()) == []
