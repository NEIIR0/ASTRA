from __future__ import annotations

import json
from pathlib import Path

from .state import GameState, default_state

DEFAULT_PATH = Path("data") / "game_state.json"


def load_state(path: Path = DEFAULT_PATH) -> GameState:
    if not path.exists():
        return default_state()
    data = json.loads(path.read_text("utf-8"))
    return GameState.from_dict(data)


def save_state(state: GameState, path: Path = DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state.to_dict(), ensure_ascii=False, indent=2) + "\n"
    path.write_text(payload, encoding="utf-8")
