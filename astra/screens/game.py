from __future__ import annotations

from ..game.quests import defs_by_id
from ..game.storage import load_state


def run() -> None:
    s = load_state()
    print("TRYB GRY (v0.02.0)")
    print(f"- day: {s.day}")
    print(f"- sector: {s.ship.sector}")
    print(f"- hull: {s.ship.hull}")
    print(f"- power: {s.ship.power}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")

    qdefs = defs_by_id()
    print("- quests:")
    for q in s.quests:
        qd = qdefs.get(q.quest_id)
        title = qd.title if qd else q.quest_id
        target = qd.target_value if qd else 0
        print(f"  * {title} [{q.status}] {q.progress}/{target}")

    print("Next: python -m astra game status")
    print("Tick SAFE: python -m astra game tick")
    print("Tick+SAVE (WRITE): python -m astra game tick --write")
