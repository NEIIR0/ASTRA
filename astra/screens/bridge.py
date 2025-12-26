from __future__ import annotations

from ..game.storage import load_state


def run(*, profile: str) -> None:
    s = load_state(profile=profile)
    print("MOSTEK (Ship Status)")
    print(f"- profile(run): {profile}")
    print(f"- day: {s.day}")
    print(f"- ship: hull={s.ship.hull} power={s.ship.power} sector={s.ship.sector}")
    print("Next: python -m astra --profile dev game status")
