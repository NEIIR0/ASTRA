from __future__ import annotations

import random
from dataclasses import replace
from typing import Any

from .achievements import check_achievements
from .events import EventBus
from .progression import level_from_xp
from .state import GameState, PlayerState, QuestProgress, ShipState

TickResult = tuple[GameState, list[str], list[dict[str, Any]]]


def tick_day(state: GameState, *, seed: int | None = None) -> TickResult:
    if seed is None:
        seed = int(getattr(state, "last_seed", 0) or 0)

    rng = random.Random(int(seed))
    bus = EventBus()
    txt: list[str] = [f"Dzień {state.day} -> {state.day + 1}"]

    new_day = state.day + 1

    # anomalia: deterministycznie z seeda (zgodne z golden: 123 -> hull-1, 999 -> hull bez zmian)
    hull = state.ship.hull
    if rng.random() < 0.5:
        hull = max(0, hull - 1)
        txt.append("- hull: -1 (anomalia)")

    power = max(0, state.ship.power - 1)
    txt.append("- power: -1")

    ship = ShipState(sector=state.ship.sector, hull=hull, power=power)

    gained_xp = 5
    new_xp = state.player.xp + gained_xp
    new_level = level_from_xp(new_xp)
    player = PlayerState(xp=new_xp, level=new_level)
    txt.append(f"+XP {gained_xp} (xp={new_xp}, lvl={new_level})")

    temp = replace(state, day=new_day, ship=ship, player=player, last_seed=int(seed))

    # quest: q_ticks_3 progress +1
    new_quests: list[QuestProgress] = []
    for q in temp.quests:
        if q.quest_id == "q_ticks_3" and q.status == "active":
            prog = min(int(q.progress) + 1, 3)
            status = "completed" if prog >= 3 else "active"
            new_quests.append(QuestProgress(quest_id=q.quest_id, status=status, progress=prog))
        else:
            new_quests.append(q)
    temp = replace(temp, quests=new_quests)

    newly = check_achievements(temp)
    if newly:
        txt.extend([f"ACHIEVEMENT: {x}" for x in newly])
    final = replace(temp, achievements=list(temp.achievements) + newly)

    bus.emit("tick_done", amount=1, day=new_day)
    return final, txt, bus.drain()
