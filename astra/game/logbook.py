from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PROFILES_ROOT = Path("data") / "profiles"


def safe_profile(name: str) -> str:
    name = (name or "default").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", name):
        return "default"
    return name


def logbook_path(profile: str) -> Path:
    p = safe_profile(profile)
    return PROFILES_ROOT / p / "logbook.jsonl"


def append_events(events: list[dict[str, Any]], *, write: bool, profile: str) -> None:
    if not write:
        return
    path = logbook_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
