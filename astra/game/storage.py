from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .migrations import migrate_dict
from .state import GameState, default_state

PROFILES_ROOT = Path("data") / "profiles"


def safe_profile(name: str) -> str:
    name = (name or "default").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", name):
        return "default"
    return name


def state_path(profile: str) -> Path:
    p = safe_profile(profile)
    return PROFILES_ROOT / p / "game_state.json"


def load_state(*, profile: str) -> GameState:
    path = state_path(profile)
    if not path.exists():
        return default_state()
    raw: dict[str, Any] = json.loads(path.read_text("utf-8"))
    migrated = migrate_dict(raw)
    return GameState.from_dict(migrated)


def save_state(state: GameState, *, profile: str) -> None:
    path = state_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state.to_dict(), ensure_ascii=False, indent=2) + "\n"
    path.write_text(payload, encoding="utf-8")
