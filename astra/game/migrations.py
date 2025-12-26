from __future__ import annotations

from typing import Any

LATEST_SCHEMA_VERSION = 3


def migrate_dict(d: dict[str, Any]) -> dict[str, Any]:
    sv = int(d.get("schema_version", 0))

    if sv == LATEST_SCHEMA_VERSION:
        return d

    if sv == 2:
        # v2 -> v3: add last_seed
        d2 = dict(d)
        d2["schema_version"] = 3
        d2.setdefault("last_seed", 0)
        return d2

    if sv == 1:
        # v1 -> v3: v1 had active_quests, but v2+ uses quests list with catalog
        d2 = dict(d)
        d2.pop("active_quests", None)
        d2["schema_version"] = 3
        d2.setdefault("quests", [])
        d2.setdefault("last_seed", 0)
        return d2

    # Unknown: fail fast
    raise ValueError(f"Unsupported schema_version={sv} (expected 1/2/3)")
