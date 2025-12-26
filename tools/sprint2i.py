from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()

def w(path: str, text: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")

# 1) Result contract
w(
    "astra/game/result.py",
    """from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ActionError:
    code: str
    message: str
    field: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.field is not None:
            d["field"] = self.field
        return d


@dataclass(frozen=True)
class ActionResult:
    state: Any
    text: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    errors: list[ActionError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def ok(state: Any, *, text: list[str] | None = None, events: list[dict[str, Any]] | None = None) -> ActionResult:
    return ActionResult(state=state, text=list(text or []), events=list(events or []), errors=[])


def fail(
    state: Any,
    *,
    text: list[str] | None = None,
    events: list[dict[str, Any]] | None = None,
    errors: list[ActionError] | None = None,
) -> ActionResult:
    return ActionResult(state=state, text=list(text or []), events=list(events or []), errors=list(errors or []))
""",
)

# 2) Validation
w(
    "astra/game/validate.py",
    """from __future__ import annotations

import re

from .result import ActionError


_SECTOR_RE = re.compile(r"^[A-Za-z0-9 _\\-\\.]+$")


def validate_move(*, sector: str) -> list[ActionError]:
    errs: list[ActionError] = []
    s = (sector or "").strip()

    if not s:
        errs.append(ActionError(code="invalid_sector", message="Sector cannot be empty.", field="sector"))
        return errs

    if len(s) > 40:
        errs.append(ActionError(code="invalid_sector", message="Sector too long (max 40).", field="sector"))

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
""",
)

# 3) Reducer
w(
    "astra/game/reducer.py",
    """from __future__ import annotations

from dataclasses import replace
from typing import Any

from .engine import tick_day
from .events import EventBus
from .result import ActionError, ActionResult, fail, ok
from .validate import validate_move, validate_tick


def reduce(state: Any, action: str, **kwargs: Any) -> ActionResult:
    a = (action or "").strip().lower()

    if a == "tick":
        seed = kwargs.get("seed", None)
        errs = validate_tick(seed=seed)
        if errs:
            return fail(state, errors=errs, text=["ERROR: tick validation failed."])

        # tick_day is deterministic by seed; if None, engine will use last_seed/0 (your current behavior)
        s1, txt, events = tick_day(state, seed=seed)
        return ok(s1, text=txt, events=events)

    if a == "move":
        sector = str(kwargs.get("sector", ""))
        errs = validate_move(sector=sector)
        if errs:
            return fail(state, errors=errs, text=["ERROR: move validation failed."])

        old = getattr(getattr(state, "ship", None), "sector", "Unknown")
        ship = getattr(state, "ship", None)
        if ship is None:
            return fail(state, errors=[ActionError("invalid_state", "State has no ship.", "state")])

        new_ship = replace(ship, sector=sector.strip())
        s1 = replace(state, ship=new_ship)
        txt = [f"SECTOR MOVE: {old} -> {sector.strip()}"]
        events = [{"type": "sector_moved", "sector": sector.strip()}]
        return ok(s1, text=txt, events=events)

    return fail(
        state,
        errors=[ActionError(code="unknown_action", message=f"Unknown action: {action}", field="action")],
        text=["ERROR: unknown action."],
    )
""",
)

# 4) Actions API (compat + single entry)
w(
    "astra/game/actions.py",
    """from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .reducer import reduce
from .result import ActionResult


@dataclass(frozen=True)
class TickDay:
    seed: int | None = None


@dataclass(frozen=True)
class MoveSector:
    sector: str


def run_action(state: Any, action: Any) -> ActionResult:
    if isinstance(action, TickDay):
        return reduce(state, "tick", seed=action.seed)
    if isinstance(action, MoveSector):
        return reduce(state, "move", sector=action.sector)
    return reduce(state, "unknown")


def apply_action(state: Any, action: str, **kwargs: Any) -> tuple[Any, list[str], list[dict[str, Any]]]:
    # Backward-compatible API: returns (state, text, events)
    r = reduce(state, action, **kwargs)
    return r.state, r.text, r.events


__all__ = ["TickDay", "MoveSector", "run_action", "apply_action"]
""",
)

# 5) Fix tests that were importing TickDay/run_action previously (safe overwrite)
w(
    "tests/test_actions_v2.py",
    """from astra.game.actions import MoveSector, TickDay, run_action
from astra.game.state import default_state


def test_actions_v2_tick_and_move():
    s0 = default_state()

    r1 = run_action(s0, TickDay(seed=123))
    assert r1.ok is True
    assert any(e.get("type") == "tick_done" for e in r1.events)

    r2 = run_action(r1.state, MoveSector(sector="Sektor A-1"))
    assert r2.ok is True
    assert any(e.get("type") == "sector_moved" for e in r2.events)
""",
)

print("SPRINT 2I generated: result/validate/reducer + actions compat + test fix.")
