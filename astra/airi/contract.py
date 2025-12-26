from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ActionProposal:
    action: str
    kwargs: dict[str, Any]
    reason: str
    confidence: float = 0.5


class AiriAgent(Protocol):
    def propose(self, *, state: Any) -> list[ActionProposal]: ...


__all__ = ["ActionProposal", "AiriAgent"]
