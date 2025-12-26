from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .context import GameContext
from .reducer import reduce
from .result import ActionResult


@dataclass(frozen=True)
class Rule:
    name: str
    write_allowed: bool = True


RULES: dict[str, Rule] = {
    "tick": Rule("tick", True),
    "move": Rule("move", True),
}


def run(state: Any, action: str, *, ctx: GameContext, **kw: Any) -> ActionResult:
    rule = RULES.get(action)
    if rule is None:
        return reduce(state, "unknown", action=action)

    if action == "tick" and "seed" not in kw:
        kw["seed"] = ctx.seed

    return reduce(state, action, **kw)
