from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GameEvent:
    type: str
    amount: int = 1
    meta: dict[str, Any] | None = None

    def to_json(self) -> dict[str, Any]:
        return {"type": self.type, "amount": self.amount, **(self.meta or {})}


class EventBus:
    def __init__(self) -> None:
        self._events: list[GameEvent] = []

    def emit(self, e: GameEvent) -> None:
        self._events.append(e)

    def drain(self) -> list[GameEvent]:
        out = list(self._events)
        self._events.clear()
        return out
