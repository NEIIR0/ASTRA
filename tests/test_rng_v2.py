from astra.game.rng import Rng


def test_rng_deterministic():
    a = Rng(123).randint(1, 100)
    b = Rng(123).randint(1, 100)
    assert a == b
