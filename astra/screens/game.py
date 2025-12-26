from __future__ import annotations

from ..game.storage import load_state


def run() -> None:
    profile = "default"  # --once nie przekazuje profilu; default musi działać stabilnie
    s = load_state(profile=profile)

    print("TRYB GRY (Sprint 2D)")
    print(f"- profile: {profile}")
    print(f"- day: {s.day}")
    print(f"- sector: {s.ship.sector}")
    print(f"- hull: {s.ship.hull}")
    print(f"- power: {s.ship.power}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")
    print(f"- last_seed: {s.last_seed}")

    print("Next:")
    print("  python -m astra --profile dev game status")
    print("  python -m astra --profile dev game tick --seed 123")
    print("WRITE:")
    print("  python -m astra --profile dev --write game tick --seed 123")
