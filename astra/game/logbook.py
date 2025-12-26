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
    with path.open("a", encoding="utf-8", newline="\n") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
