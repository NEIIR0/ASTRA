from __future__ import annotations

import random


class Rng:
    """Deterministyczny RNG – jedyne wejście do losowości w Game Core."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(int(seed))

    def randint(self, a: int, b: int) -> int:
        return int(self._rng.randint(int(a), int(b)))

    def chance(self, p: float) -> bool:
        # p w zakresie 0..1
        x = float(p)
        if x <= 0.0:
            return False
        if x >= 1.0:
            return True
        return self._rng.random() < x
