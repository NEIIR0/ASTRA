from __future__ import annotations

from ..game.storage import load_state


def run(*, profile: str) -> None:
    s = load_state(profile=profile)
    print("TRYB GRY")
    print(f"- profile(run): {profile}")
    print(f"- day: {s.day}")
    print(f"- sector: {s.ship.sector}")
    print(f"- hull: {s.ship.hull}")
    print(f"- power: {s.ship.power}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")
    print(f"- last_seed: {getattr(s, 'last_seed', 0)}")
