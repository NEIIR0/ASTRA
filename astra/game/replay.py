from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from .actions import apply_action
from .logbook import iter_logbook
from .state import default_state


def _dc_base(proto: Any) -> dict[str, Any]:
    # IMPORTANT: for dataclasses, prefer fields() over to_dict()
    # because to_dict() often flattens nested dataclasses into dicts.
    if is_dataclass(proto):
        return {f.name: getattr(proto, f.name) for f in fields(proto)}
    if hasattr(proto, "to_dict"):
        d = proto.to_dict()
        return d if isinstance(d, dict) else {}
    return {}


def _dc_from_dict(proto: Any, data: dict[str, Any]) -> Any:
    if not is_dataclass(proto):
        return data

    base = _dc_base(proto)
    kwargs: dict[str, Any] = {}

    for k, v in data.items():
        if k not in base:
            continue

        cur = base.get(k)

        if is_dataclass(cur) and isinstance(v, dict):
            kwargs[k] = _dc_from_dict(cur, v)
            continue

        if isinstance(cur, list) and isinstance(v, list):
            if cur and is_dataclass(cur[0]) and all(isinstance(x, dict) for x in v):
                kwargs[k] = [_dc_from_dict(cur[0], x) for x in v]
            else:
                kwargs[k] = v
            continue

        kwargs[k] = v

    return proto.__class__(**{**base, **kwargs})


def replay_state(*, profile: str):
    items = list(iter_logbook(profile))

    last_snap_state: dict[str, Any] | None = None
    start_idx = 0
    for i, obj in enumerate(items):
        if obj.get("type") == "snapshot" and isinstance(obj.get("state"), dict):
            last_snap_state = obj["state"]
            start_idx = i + 1

    proto = default_state()
    state = _dc_from_dict(proto, last_snap_state) if last_snap_state else proto

    for obj in items[start_idx:]:
        if obj.get("type") != "command":
            continue

        action = obj.get("action")
        if action == "tick":
            state, _txt, _events = apply_action(state, "tick", seed=obj.get("seed"))
        elif action == "move":
            state, _txt, _events = apply_action(state, "move", sector=obj.get("sector", "Mostek"))

    return state
