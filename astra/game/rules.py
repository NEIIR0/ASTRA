from __future__ import annotations

from dataclasses import replace
from typing import Any


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(v)))


def apply_rules(state: Any) -> tuple[Any, list[str], list[dict[str, Any]]]:
    """
    Post-rules run AFTER reducer applies an action.
    - clamp hull/power to 0..100
    - emit power_down when power==0
    - emit game_over when hull==0
    """
    txt: list[str] = []
    events: list[dict[str, Any]] = []

    ship = getattr(state, "ship", None)
    if ship is None:
        return state, txt, events

    hull0 = getattr(ship, "hull", 0)
    power0 = getattr(ship, "power", 0)

    hull = _clamp(hull0, 0, 100)
    power = _clamp(power0, 0, 100)

    if hull != hull0 or power != power0:
        txt.append("RULE: clamp hull/power -> 0..100")
        events.append(
            {
                "type": "stat_clamped",
                "hull_before": int(hull0),
                "power_before": int(power0),
                "hull": int(hull),
                "power": int(power),
            }
        )
        ship2 = replace(ship, hull=hull, power=power)
        state = replace(state, ship=ship2)

    if getattr(state.ship, "power", 0) == 0:
        events.append({"type": "power_down"})
    if getattr(state.ship, "hull", 0) == 0:
        events.append({"type": "game_over"})

    return state, txt, events
