from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


def _step(seed: int) -> tuple[int, int]:
    """
    Classic C LCG (31-bit), compatible with legacy golden tests.
    Returns: (new_seed, raw15) where raw15 is like (rand() >> 16) & 0x7fff.
    """
    s = int(seed) & 0x7FFFFFFF
    s = (1103515245 * s + 12345) & 0x7FFFFFFF
    raw15 = (s >> 16) & 0x7FFF
    return s, raw15


def next_seed(seed: int) -> int:
    s, _ = _step(seed)
    return s


def rng_raw15(seed: int) -> int:
    _, raw15 = _step(int(seed))
    return raw15


def rng_int(seed: int, lo: int, hi: int) -> int:
    """Deterministic int in [lo, hi] inclusive (no mutation)."""
    lo_i = int(lo)
    hi_i = int(hi)
    if hi_i < lo_i:
        lo_i, hi_i = hi_i, lo_i
    span = hi_i - lo_i + 1
    raw15 = rng_raw15(int(seed))
    return lo_i + (raw15 % span)


def rng_float01(seed: int) -> float:
    """Deterministic float in [0,1)."""
    return rng_raw15(int(seed)) / 32768.0


def rng_choice[T](seed: int, items: Iterable[T]) -> T:
    seq = list(items)
    if not seq:
        raise ValueError("rng_choice: empty sequence")
    idx = rng_int(seed, 0, len(seq) - 1)
    return seq[idx]


@dataclass
class Rng:
    """Small deterministic RNG (stateful)."""

    seed: int

    def randint(self, lo: int, hi: int) -> int:
        self.seed, raw15 = _step(self.seed)
        lo_i = int(lo)
        hi_i = int(hi)
        if hi_i < lo_i:
            lo_i, hi_i = hi_i, lo_i
        span = hi_i - lo_i + 1
        return lo_i + (raw15 % span)

    def random(self) -> float:
        self.seed, raw15 = _step(self.seed)
        return raw15 / 32768.0

    def choice(self, items: Iterable[T]) -> T:
        seq = list(items)
        if not seq:
            raise ValueError("choice: empty sequence")
        idx = self.randint(0, len(seq) - 1)
        return seq[idx]


# Back-compat aliases
rand_int = rng_int
det_int = rng_int
roll_int = rng_int

__all__ = [
    "Rng",
    "next_seed",
    "rng_raw15",
    "rng_int",
    "rng_float01",
    "rng_choice",
    "rand_int",
    "det_int",
    "roll_int",
]
