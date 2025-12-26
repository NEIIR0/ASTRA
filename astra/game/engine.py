from __future__ import annotations

from dataclasses import replace
from typing import Any

from .balance import load_balance
from .rng import rng_raw15


def _quest_to_dict(q: Any) -> dict[str, Any] | None:
    # dict-style
    if isinstance(q, dict):
        return {
            "quest_id": str(q.get("quest_id", "")),
            "status": str(q.get("status", "")),
            "progress": int(q.get("progress", 0)),
        }

    # object/dataclass-style
    if hasattr(q, "quest_id") and hasattr(q, "status") and hasattr(q, "progress"):
        return {
            "quest_id": str(getattr(q, "quest_id")),
            "status": str(getattr(q, "status")),
            "progress": int(getattr(q, "progress")),
        }

    return None


def _quest_tick_progress(state: Any) -> Any:
    qs = getattr(state, "quests", [])
    out: list[dict[str, Any]] = []

    for q in qs:
        qd = _quest_to_dict(q)
        if qd is None:
            continue

        if qd["quest_id"] == "q_ticks_3" and qd["status"] == "active":
            p = int(qd.get("progress", 0)) + 1
            qd["progress"] = 3 if p >= 3 else p
            qd["status"] = "completed" if p >= 3 else "active"

        out.append(qd)

    return replace(state, quests=out)


def _award_first_day(state: Any) -> Any:
    ach = getattr(state, "achievements", None)
    if not isinstance(ach, list):
        return state
    if "Pierwszy dzień" in ach:
        return state
    return replace(state, achievements=[*ach, "Pierwszy dzień"])


def tick_day(state: Any, *, seed: int | None = None, profile: str = "offline"):
    """
    Deterministic tick by seed.
    Balance (xp/anomaly) is loaded per profile.
    Golden-compat: hull and power anomaly are rolled independently from raw15 bits.
    """
    cfg = load_balance(profile=profile)

    last_seed = int(getattr(state, "last_seed", 0))
    use_seed = int(last_seed if seed is None else seed)

    day0 = int(getattr(state, "day", 0))
    day1 = day0 + 1

    ship = state.ship
    player = state.player

    raw15 = rng_raw15(use_seed)
    hull_roll = raw15 & 1
    power_roll = (raw15 >> 2) & 1

    hull = int(getattr(ship, "hull", 100))
    power = int(getattr(ship, "power", 100))

    txt: list[str] = [f"Dzień {day0} -> {day1}"]
    if hull_roll == 1:
        hull -= cfg.anomaly_hull_loss
        txt.append(f"- hull: -{cfg.anomaly_hull_loss} (anomalia)")
    if power_roll == 1:
        power -= cfg.anomaly_power_loss
        txt.append(f"- power: -{cfg.anomaly_power_loss}")

    xp0 = int(getattr(player, "xp", 0))
    lvl0 = int(getattr(player, "level", 1))
    xp1 = xp0 + cfg.xp_per_tick
    txt.append(f"+XP {cfg.xp_per_tick} (xp={xp1}, lvl={lvl0})")

    lvl1 = max(1, (xp1 // 10) + 1)
    if lvl1 > lvl0:
        txt.append(f"ACHIEVEMENT: Awans: Poziom {lvl1}")

    ship1 = replace(ship, hull=hull, power=power)
    player1 = replace(player, xp=xp1, level=lvl1)
    state1 = replace(state, day=day1, ship=ship1, player=player1, last_seed=use_seed)

    if day0 == 0:
        state1 = _award_first_day(state1)

    # golden expectations: quests must be dicts with only quest_id/status/progress
    state1 = _quest_tick_progress(state1)

    events = [{"type": "tick_done", "amount": 1, "day": day1}]
    return state1, txt, events


__all__ = ["tick_day"]
