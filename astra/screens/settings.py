from __future__ import annotations

from ..config import load_config


def run(*, profile: str) -> None:
    cfg = load_config()
    print("USTAWIENIA")
    print(f"- profile(run): {profile}")
    print(f"- config.profile(default): {cfg.profile}")
    print(f"- config.log_enabled: {cfg.log_enabled}")
    print("Tip: profile to save-slot. Użyj: --profile dev/test/default")
