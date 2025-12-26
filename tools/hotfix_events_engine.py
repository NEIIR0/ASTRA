from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()

def write_utf8(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")

# 1) FIX: events.py (GameEvent kompatybilny z engine: type + amount + payload)
events_py = """from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GameEvent:
    \"""Canonical event used by engine/UI/AIRI.\"""\"
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
"""
write_utf8(ROOT / "astra/game/events.py", events_py)

# 2) FIX: engine.py (seed opcjonalny -> domyślnie last_seed/0)
p = ROOT / "astra/game/engine.py"
src = p.read_text("utf-8")

src = re.sub(
    r"def tick_day\(([^)]*)\*,\s*seed:\s*int\s*\)",
    r"def tick_day(\1*, seed: int | None = None)",
    src,
    count=1,
)

if "seed: int | None = None" in src and "if seed is None:" not in src:
    # wstaw po definicji funkcji pierwszą inicjalizację seed
    src = re.sub(
        r"(def tick_day\([^\n]*\):\n)",
        r"\1    if seed is None:\n        seed = int(getattr(state, 'last_seed', 0) or 0)\n\n",
        src,
        count=1,
    )

write_utf8(p, src)

print("HOTFIX applied: GameEvent signature + engine seed default")
