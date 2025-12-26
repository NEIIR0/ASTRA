from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GameEvent:
    """Canonical event used by engine/UI/AIRI."""

    type: str
    amount: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": self.type}
        if self.amount is not None:
            d["amount"] = self.amount
        d.update(self.payload)
        return d


Event = GameEvent


class EventBus:
    """In-memory event buffer. Engine emits, UI/AIRI drains."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def emit(self, event_type: str, amount: int | None = None, **payload: Any) -> None:
        self._events.append(GameEvent(event_type, amount, dict(payload)).to_dict())

    def emit_event(self, ev: GameEvent) -> None:
        self._events.append(ev.to_dict())

    def drain(self) -> list[dict[str, Any]]:
        out = list(self._events)
        self._events.clear()
        return out

    def peek(self) -> list[dict[str, Any]]:
        return list(self._events)


__all__ = ["GameEvent", "Event", "EventBus"]
