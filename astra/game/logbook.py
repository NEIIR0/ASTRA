from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_LOGBOOK = Path("data") / "logbook.jsonl"


def append_events(
    events: list[dict[str, Any]], *, write: bool, path: Path = DEFAULT_LOGBOOK
) -> None:
    if not write:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events)
    path.write_text(path.read_text("utf-8") + lines if path.exists() else lines, encoding="utf-8")
