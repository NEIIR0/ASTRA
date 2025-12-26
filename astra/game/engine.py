from __future__ import annotations

import random
from dataclasses import replace
from typing import Any

from .achievements import check_achievements
from .events import GameEvent
from .progression import level_from_xp
from .quests import apply_event, defs_by_id
from .state import GameState, PlayerState, ShipState


def apply_events(state: GameState, events: list[GameEvent]) -> GameState:
    qdefs = defs_by_id()
    updated = []
    for qp in state.quests:
        qd = qdefs.get(qp.quest_id)
        if not qd:
            updated.append(qp)
            continue
        out = qp
        for e in events:
            out = apply_event(out, qd, e.type, int(e.amount))
        updated.append(out)
    return replace(state, quests=updated)


def tick_day(state: GameState, *, seed: int) -> tuple[GameState, list[str], list[dict[str, Any]]]:
    rng = random.Random(seed)

    bus: list[GameEvent] = []
    txt: list[str] = [f"Dzień {state.day} -> {state.day + 1}"]

    bus.append(GameEvent("tick_done", 1, {"day": state.day + 1}))

    # ship drift (deterministic via seed)
    power_loss = 1
    hull_loss = 1 if rng.random() < 0.10 else 0

    new_ship = ShipState(
        sector=state.ship.sector,
        hull=max(0, state.ship.hull - hull_loss),
        power=max(0, state.ship.power - power_loss),
    )
    if hull_loss:
        txt.append("- hull: -1 (anomalia)")
    txt.append(f"- power: -{power_loss}")

    gained_xp = 5
    new_xp = state.player.xp + gained_xp
    new_level = level_from_xp(new_xp)
    new_player = PlayerState(xp=new_xp, level=new_level)
    txt.append(f"+XP {gained_xp} (xp={new_xp}, lvl={new_level})")

    temp = replace(state, day=state.day + 1, ship=new_ship, player=new_player)

    newly = check_achievements(temp)
    if newly:
        txt.extend([f"ACHIEVEMENT: {x}" for x in newly])
    temp2 = replace(temp, achievements=list(temp.achievements) + newly)

    final = apply_events(temp2, bus)
    return final, txt, [e.to_json() for e in bus]


def apply_external_event(state: GameState, e: GameEvent) -> GameState:
    return apply_events(state, [e])
