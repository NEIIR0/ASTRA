from __future__ import annotations
from pathlib import Path

def w(p: str, s: str) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(s, encoding="utf-8", newline="\n")

w("astra/game/context.py", """from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class GameContext:
    profile: str = "offline"
    write: bool = False
    seed: int | None = None
""")

w("astra/game/registry.py", """from __future__ import annotations
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
""")

w("tests/test_registry.py", """from astra.game.context import GameContext
from astra.game.registry import run
from astra.game.state import default_state

def test_registry_tick_seed_passthrough():
    s0 = default_state()
    r = run(s0, "tick", ctx=GameContext(seed=123))
    assert r.ok is True
    assert any(e.get("type") == "tick_done" for e in r.events)
""")

print("SPRINT 2J applied: GameContext + Registry + tests.")
