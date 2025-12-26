from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .events import EventBus
from .sectors import DEFAULT_SECTORS


@dataclass(frozen=True)
class PolicyDecision:
    ok: bool
    reason: str = ""


def check_action_allowed(*, state: Any, action: str, kwargs: dict[str, Any], bus: EventBus) -> PolicyDecision:
    if action == "move":
        target = str(kwargs.get("sector", "")).strip()
        if not target or DEFAULT_SECTORS.get(target) is None:
            bus.emit("sector_unknown", sector=target)
            return PolicyDecision(False, "unknown_sector")

    ship = getattr(state, "ship", None)
    hull = getattr(ship, "hull", None) if ship is not None else None
    if action == "tick" and hull == 0:
        bus.emit("action_blocked", action=action, reason="game_over")
        return PolicyDecision(False, "game_over")

    return PolicyDecision(True, "")
