from __future__ import annotations

from ..integration import airi_bridge


def run(*, profile: str) -> None:
    print("AIRI (bridge)")
    print(f"- profile(run): {profile}")
    airi_bridge.run()
