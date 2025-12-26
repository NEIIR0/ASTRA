from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .reducer import reduce
from .result import ActionResult


@dataclass(frozen=True)
class TickDay:
    seed: int | None = None


@dataclass(frozen=True)
class MoveSector:
    sector: str


def run_action(state: Any, action: Any) -> ActionResult:
    if isinstance(action, TickDay):
        return reduce(state, "tick", seed=action.seed)
    if isinstance(action, MoveSector):
        return reduce(state, "move", sector=action.sector)
    return reduce(state, "unknown")


def apply_action(state: Any, action: str, **kwargs: Any) -> tuple[Any, list[str], list[dict[str, Any]]]:
    # Backward-compatible API: returns (state, text, events)
    r = reduce(state, action, **kwargs)
    return r.state, r.text, r.events


__all__ = ["TickDay", "MoveSector", "run_action", "apply_action"]
