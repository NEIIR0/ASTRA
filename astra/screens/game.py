from __future__ import annotations

from ..game.storage import load_state


def run() -> None:
    s = load_state()
    print("TRYB GRY (Sprint 2A)")
    print(f"- day: {s.day}")
    print(f"- sector: {s.ship.sector}")
    print(f"- hull: {s.ship.hull}")
    print(f"- power: {s.ship.power}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")
    if s.active_quests:
        print("- quests:")
        for q in s.active_quests:
            print(f"  * {q}")
    print("Next: python -m astra game tick")
    print("Save (WRITE): python -m astra game tick --save")
