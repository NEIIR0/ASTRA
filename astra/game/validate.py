from __future__ import annotations

import re

from .result import ActionError
from .state import GameState

_SECTOR_RE = re.compile(
    r"^[A-Za-z0-9 _\-\.\u0104\u0105\u0106\u0107\u0118\u0119\u0141\u0142\u0143\u0144"
    r"\u00D3\u00F3\u015A\u015B\u0179\u017A\u017B\u017C]+$"
)


def validate_move(*, sector: str) -> list[ActionError]:
    errs: list[ActionError] = []
    s = (sector or "").strip()

    if not s:
        errs.append(
            ActionError(
                code="invalid_sector",
                message="Sector cannot be empty.",
                field="sector",
            )
        )
        return errs

    if len(s) > 40:
        errs.append(
            ActionError(
                code="invalid_sector",
                message="Sector too long (max 40).",
                field="sector",
            )
        )

    if _SECTOR_RE.match(s) is None:
        errs.append(
            ActionError(
                code="invalid_sector",
                message="Sector has forbidden characters (allowed: letters/digits/space/_-.)",
                field="sector",
            )
        )
    return errs


def validate_tick(*, seed: int | None) -> list[ActionError]:
    if seed is None:
        return []
    if not isinstance(seed, int):
        return [ActionError(code="invalid_seed", message="Seed must be int.", field="seed")]
    if seed < 0:
        return [ActionError(code="invalid_seed", message="Seed must be >= 0.", field="seed")]
    return []


def validate_state(state: GameState) -> list[ActionError]:
    errs: list[ActionError] = []

    if state.day < 0:
        errs.append(ActionError(code="invalid_day", message="Day must be >= 0.", field="day"))

    if state.ship.hull < 0 or state.ship.hull > 100:
        errs.append(ActionError(code="invalid_hull", message="Hull must be 0..100.", field="ship.hull"))

    if state.ship.power < 0 or state.ship.power > 100:
        errs.append(ActionError(code="invalid_power", message="Power must be 0..100.", field="ship.power"))

    errs.extend(validate_move(sector=state.ship.sector))

    if state.player.xp < 0:
        errs.append(ActionError(code="invalid_xp", message="XP must be >= 0.", field="player.xp"))

    if state.player.level < 1:
        errs.append(ActionError(code="invalid_level", message="Level must be >= 1.", field="player.level"))

    if getattr(state, "last_seed", 0) < 0:
        errs.append(
            ActionError(
                code="invalid_last_seed",
                message="last_seed must be >= 0.",
                field="last_seed",
            )
        )

    return errs


__all__ = ["validate_move", "validate_tick", "validate_state"]
