from __future__ import annotations

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
