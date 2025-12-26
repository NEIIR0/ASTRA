from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameContext:
    profile: str = "offline"
    write: bool = False
    seed: int | None = None
