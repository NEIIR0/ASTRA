from __future__ import annotations

from dataclasses import replace
from typing import Any

from .achievements import check_achievements
from .progression import level_from_xp
from .quests import apply_event, defs_by_id
from .state import GameState, PlayerState, ShipState


def tick_day(state: GameState) -> tuple[GameState, list[str], list[dict[str, Any]]]:
    events_text: list[str] = []
    events_json: list[dict[str, Any]] = []

    events_text.append(f"Dzień {state.day} -> {state.day + 1}")
    events_json.append({"type": "tick_done", "amount": 1, "day": state.day + 1})

    new_day = state.day + 1
    new_power = max(0, state.ship.power - 1)
    new_ship = ShipState(sector=state.ship.sector, hull=state.ship.hull, power=new_power)

    gained_xp = 5
    new_xp = state.player.xp + gained_xp
    new_level = level_from_xp(new_xp)
    new_player = PlayerState(xp=new_xp, level=new_level)
    events_text.append(f"+XP {gained_xp} (xp={new_xp}, lvl={new_level})")

    temp = replace(state, day=new_day, ship=new_ship, player=new_player)

    newly = check_achievements(temp)
    if newly:
        events_text.extend([f"ACHIEVEMENT: {x}" for x in newly])

    temp2 = replace(temp, achievements=list(temp.achievements) + newly)

    qdefs = defs_by_id()
    updated = []
    for qp in temp2.quests:
        qd = qdefs.get(qp.quest_id)
        if not qd:
            updated.append(qp)
            continue
        out = qp
        for e in events_json:
            out = apply_event(out, qd, str(e["type"]), int(e.get("amount", 1)))
        updated.append(out)

    final = replace(temp2, quests=updated)
    return final, events_text, events_json
