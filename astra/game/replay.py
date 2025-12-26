from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from .actions import apply_action
from .logbook import iter_logbook
from .state import default_state


def _dc_from_dict(proto: Any, data: dict[str, Any]) -> Any:
    """Rebuild dataclass tree from dict using proto as schema/defaults."""
    if not is_dataclass(proto):
        return data

    out: dict[str, Any] = {}
    for f in fields(proto):
        cur = getattr(proto, f.name)
        if f.name in data:
            v = data[f.name]
            if is_dataclass(cur) and isinstance(v, dict):
                out[f.name] = _dc_from_dict(cur, v)
            else:
                out[f.name] = v
        else:
            out[f.name] = cur
    return proto.__class__(**out)


def replay_state(*, profile: str):
    items = list(iter_logbook(profile))

    last_snap: dict[str, Any] | None = None
    start_idx = 0
    for i, obj in enumerate(items):
        if obj.get("type") == "snapshot" and isinstance(obj.get("state"), dict):
            last_snap = obj["state"]
            start_idx = i + 1

    proto = default_state()
    state = _dc_from_dict(proto, last_snap) if last_snap else proto

    for obj in items[start_idx:]:
        if obj.get("type") != "command":
            continue

        action = obj.get("action")
        if action == "tick":
            state, _txt, _events = apply_action(state, "tick", seed=obj.get("seed"))
        elif action == "move":
            state, _txt, _events = apply_action(state, "move", sector=obj.get("sector", "Mostek"))

    return state


__all__ = ["replay_state"]
