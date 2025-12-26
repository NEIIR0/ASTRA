from __future__ import annotations

from ..config import config_path, load_config


def run(*, profile: str) -> None:
    cfg = load_config(profile=profile)
    print("USTAWIENIA")
    print(f"- profile: {cfg.profile}")
    print(f"- log_enabled: {cfg.log_enabled}")
    print(f"- config_path: {config_path(profile)}")
    print("Tip: edycja ręczna config.json (na razie bez interaktywnego input).")
