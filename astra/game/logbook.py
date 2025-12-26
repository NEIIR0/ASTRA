from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def _logbook_path(*, profile: str) -> Path:
    return Path("data") / "profiles" / profile / "logbook.jsonl"


def _append_line(*, profile: str, obj: dict[str, Any]) -> None:
    p = _logbook_path(profile=profile)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def iter_logbook(profile: str) -> Iterator[dict[str, Any]]:
    p = _logbook_path(profile=profile)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            yield obj


def append_events(profile: str, events: list[dict[str, Any]]) -> None:
    for ev in events:
        if isinstance(ev, dict):
            _append_line(profile=profile, obj=ev)


def append_command(profile: str, action: str, **kwargs: Any) -> None:
    obj: dict[str, Any] = {"type": "command", "action": action}
    obj.update(kwargs)
    _append_line(profile=profile, obj=obj)


def append_snapshot(profile: str, state: Any) -> None:
    payload: Any = state.to_dict() if hasattr(state, "to_dict") else state
    _append_line(profile=profile, obj={"type": "snapshot", "state": payload})


def append_tx(profile: str, action: str, events: list[dict[str, Any]], **kwargs: Any) -> None:
    # Back-compat for older CLI: append_tx(profile, action, events, seed=..., sector=...)
    append_command(profile, action, **kwargs)
    append_events(profile, events)


__all__ = [
    "iter_logbook",
    "append_events",
    "append_command",
    "append_snapshot",
    "append_tx",
]
