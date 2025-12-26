from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def w(path: str, text: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


w(
    "astra/game/rng.py",
    """from __future__ import annotations

import random


class Rng:
    \"\"\"Deterministyczny RNG – jedyne wejście do losowości w Game Core.\"\"\"

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(int(seed))

    def randint(self, a: int, b: int) -> int:
        return int(self._rng.randint(int(a), int(b)))

    def chance(self, p: float) -> bool:
        # p w zakresie 0..1
        x = float(p)
        if x <= 0.0:
            return False
        if x >= 1.0:
            return True
        return self._rng.random() < x
""",
)

w(
    "astra/game/validate.py",
    """from __future__ import annotations

from .state import GameState


def validate_state(state: GameState) -> list[str]:
    errs: list[str] = []

    if getattr(state, "day", 0) < 0:
        errs.append("state.day < 0")

    ship = getattr(state, "ship", None)
    if ship is None:
        errs.append("state.ship missing")
        return errs

    hull = int(getattr(ship, "hull", -1))
    power = int(getattr(ship, "power", -1))
    if not (0 <= hull <= 100):
        errs.append(f"ship.hull out of range: {hull}")
    if not (0 <= power <= 100):
        errs.append(f"ship.power out of range: {power}")

    player = getattr(state, "player", None)
    if player is None:
        errs.append("state.player missing")
        return errs

    xp = int(getattr(player, "xp", -1))
    lvl = int(getattr(player, "level", -1))
    if xp < 0:
        errs.append(f"player.xp < 0: {xp}")
    if lvl < 1:
        errs.append(f"player.level < 1: {lvl}")

    return errs
""",
)

w(
    "astra/game/actions.py",
    """from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .events import EventBus
from .state import GameState
from .validate import validate_state


class Action(Protocol):
    def validate(self, state: GameState) -> list[str]: ...
    def apply(self, state: GameState) -> tuple[GameState, list[dict]]: ...


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    state: GameState
    events: list[dict]
    errors: list[str]


@dataclass(frozen=True)
class TickDay:
    \"\"\"V2 Action: TickDay (w środku może używać legacy engine dla zgodności).\"\"\"

    seed: int | None = None

    def validate(self, state: GameState) -> list[str]:
        # Na razie brak twardych reguł akcji; rozszerzymy w kolejnych sprintach.
        return []

    def apply(self, state: GameState) -> tuple[GameState, list[dict]]:
        # Adapter: użyj istniejącej logiki tick_day, ale zwróć eventy przez EventBus.
        from .engine import tick_day as legacy_tick_day

        new_state, _txt, legacy_events = legacy_tick_day(state, seed=self.seed)
        bus = EventBus()
        for ev in legacy_events:
            et = str(ev.get("type", "unknown"))
            payload = dict(ev)
            payload.pop("type", None)
            amount = payload.pop("amount", None)
            bus.emit(et, amount, **payload)
        return new_state, bus.drain()


def run_action(state: GameState, action: Action) -> ActionResult:
    errors: list[str] = []
    errors.extend(validate_state(state))
    errors.extend(action.validate(state))

    if errors:
        bus = EventBus()
        bus.emit("invalid_action", None, errors=list(errors))
        return ActionResult(ok=False, state=state, events=bus.drain(), errors=errors)

    new_state, events = action.apply(state)
    return ActionResult(ok=True, state=new_state, events=events, errors=[])
""",
)

w(
    "tests/test_actions_v2.py",
    """from astra.game.actions import TickDay, run_action
from astra.game.engine import tick_day as legacy_tick_day
from astra.game.state import default_state


def test_action_tick_matches_legacy_seed_123():
    s0 = default_state()
    s1, _txt, legacy_events = legacy_tick_day(s0, seed=123)

    res = run_action(s0, TickDay(seed=123))
    assert res.ok is True
    assert res.state.to_dict() == s1.to_dict()
    assert res.events == legacy_events
""",
)

w(
    "tests/test_validate_v2.py",
    """from astra.game.state import default_state
from astra.game.validate import validate_state


def test_validate_default_ok():
    assert validate_state(default_state()) == []
""",
)

w(
    "tests/test_rng_v2.py",
    """from astra.game.rng import Rng


def test_rng_deterministic():
    a = Rng(123).randint(1, 100)
    b = Rng(123).randint(1, 100)
    assert a == b
""",
)

print("SPRINT 2F generated: rng/validate/actions + tests (no overwrites).")
