from __future__ import annotations

from ..integration.airi_client import AiriClient


def run(*, profile: str) -> None:
    _ = profile
    c = AiriClient()
    s = c.status()
    print("AIRI (bridge)")
    print(f"- AIRI online (version {s.version})")
    print(f"- policy: {s.policy} (default SAFE for action=bridge_status)")
    print("- mode: stub")
