from __future__ import annotations
from pathlib import Path

V="0.0.21"  # ASTRA v0.02.1

def w(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")

# version bump
w(Path("astra_common/__init__.py"), '__version__ = "0.0.21"\n')

w(Path("pyproject.toml"), """[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "astra-airi"
version = "0.0.21"
requires-python = ">=3.12"
description = "ASTRA(HUB)+AIRI(agent) monorepo, local-first."
readme = "README.md"

[tool.setuptools.packages.find]
include = ["airi", "astra", "astra_common"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py312"
exclude = ["tools/*", "astra_airi.egg-info/*"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
""")

# --- Event bus
w(Path("astra/game/events.py"), """from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GameEvent:
    type: str
    amount: int = 1
    meta: dict[str, Any] | None = None

    def to_json(self) -> dict[str, Any]:
        return {"type": self.type, "amount": self.amount, **(self.meta or {})}


class EventBus:
    def __init__(self) -> None:
        self._events: list[GameEvent] = []

    def emit(self, e: GameEvent) -> None:
        self._events.append(e)

    def drain(self) -> list[GameEvent]:
        out = list(self._events)
        self._events.clear()
        return out
""")

# --- Engine (domain, no IO/print)
w(Path("astra/game/engine.py"), """from __future__ import annotations

import random
from dataclasses import replace
from typing import Any

from .achievements import check_achievements
from .events import GameEvent
from .progression import level_from_xp
from .quests import apply_event, defs_by_id
from .state import GameState, PlayerState, ShipState


def apply_events(state: GameState, events: list[GameEvent]) -> GameState:
    qdefs = defs_by_id()
    updated = []
    for qp in state.quests:
        qd = qdefs.get(qp.quest_id)
        if not qd:
            updated.append(qp)
            continue
        out = qp
        for e in events:
            out = apply_event(out, qd, e.type, int(e.amount))
        updated.append(out)
    return replace(state, quests=updated)


def tick_day(state: GameState, *, seed: int) -> tuple[GameState, list[str], list[dict[str, Any]]]:
    rng = random.Random(seed)

    bus: list[GameEvent] = []
    txt: list[str] = [f"Dzień {state.day} -> {state.day + 1}"]

    bus.append(GameEvent("tick_done", 1, {"day": state.day + 1}))

    # ship drift (deterministic via seed)
    power_loss = 1
    hull_loss = 1 if rng.random() < 0.10 else 0

    new_ship = ShipState(
        sector=state.ship.sector,
        hull=max(0, state.ship.hull - hull_loss),
        power=max(0, state.ship.power - power_loss),
    )
    if hull_loss:
        txt.append("- hull: -1 (anomalia)")
    txt.append(f"- power: -{power_loss}")

    gained_xp = 5
    new_xp = state.player.xp + gained_xp
    new_level = level_from_xp(new_xp)
    new_player = PlayerState(xp=new_xp, level=new_level)
    txt.append(f"+XP {gained_xp} (xp={new_xp}, lvl={new_level})")

    temp = replace(state, day=state.day + 1, ship=new_ship, player=new_player)

    newly = check_achievements(temp)
    if newly:
        txt.extend([f"ACHIEVEMENT: {x}" for x in newly])
    temp2 = replace(temp, achievements=list(temp.achievements) + newly)

    final = apply_events(temp2, bus)
    return final, txt, [e.to_json() for e in bus]


def apply_external_event(state: GameState, e: GameEvent) -> GameState:
    return apply_events(state, [e])
""")

# --- logbook uses json events
w(Path("astra/game/logbook.py"), """from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_LOGBOOK = Path("data") / "logbook.jsonl"


def append_events(events: list[dict[str, Any]], *, write: bool, path: Path = DEFAULT_LOGBOOK) -> None:
    if not write:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\\n") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\\n")
""")

# --- CLI (IO layer)
w(Path("astra/cli.py"), """from __future__ import annotations

import argparse

from .doctor import run_doctor
from .game.engine import apply_external_event, tick_day
from .game.events import GameEvent
from .game.logbook import append_events
from .game.quests import claimable, defs_by_id, mark_claimed
from .game.storage import load_state, save_state
from .router import dispatch

MENU = [
    ("1", "Ustawienia"),
    ("2", "Udaj się na mostek"),
    ("3", "Udaj się do AIRI"),
    ("4", "Uniwersum"),
    ("5", "Tryb gry"),
    ("0", "Wyjście"),
]


def _print_game_status() -> None:
    s = load_state()
    qdefs = defs_by_id()
    print("GAME STATUS")
    print(f"- day: {s.day}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")
    print(f"- ship: hull={s.ship.hull} power={s.ship.power}")
    print("- quests:")
    for q in s.quests:
        qd = qdefs.get(q.quest_id)
        title = qd.title if qd else q.quest_id
        target = qd.target_value if qd else 0
        print(f"  * {q.quest_id} :: {title} [{q.status}] {q.progress}/{target}")


def _run_game_tick(write: bool, seed: int | None) -> int:
    state = load_state()
    use_seed = int(seed if seed is not None else (state.day + 1))
    new_state, events_text, events_json = tick_day(state, seed=use_seed)

    print("GAME TICK")
    print(f"- seed: {use_seed}")
    for e in events_text:
        print(f"- {e}")

    if write:
        save_state(new_state)
        append_events(events_json, write=True)
        print("- saved: data/game_state.json")
        print("- logbook: data/logbook.jsonl")
    else:
        print("- not saved (SAFE default). Use: --write")
    return 0


def _quest_claim(quest_id: str, write: bool) -> int:
    state = load_state()
    qdefs = defs_by_id()
    qd = qdefs.get(quest_id)
    if not qd:
        print(f"! unknown quest_id: {quest_id}")
        return 2

    found = None
    rest = []
    for q in state.quests:
        if q.quest_id == quest_id:
            found = q
        else:
            rest.append(q)

    if not found or not claimable(found):
        print("! not claimable")
        return 2

    if not write:
        print("- SAFE: would mark claimed + grant XP")
        print("Use: python -m astra game quest claim <id> --write")
        return 0

    new_xp = state.player.xp + qd.reward_xp
    new_player = state.player.__class__(xp=new_xp, level=state.player.level)
    claimed = mark_claimed(found)

    new_state = state.__class__(
        schema_version=state.schema_version,
        day=state.day,
        ship=state.ship,
        player=new_player,
        achievements=state.achievements,
        quests=rest + [claimed],
    )

    save_state(new_state)
    append_events([{"type": "quest_claimed", "quest_id": quest_id, "reward_xp": qd.reward_xp}], write=True)
    print(f"- claimed: {quest_id}")
    print(f"- reward_xp: {qd.reward_xp} (xp={new_xp})")
    return 0


def _emit_hook(write: bool, e: GameEvent) -> None:
    s = load_state()
    s2 = apply_external_event(s, e)
    if write:
        save_state(s2)
        append_events([e.to_json()], write=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="astra")
    p.add_argument("--once", choices=[m[0] for m in MENU])
    p.add_argument("--write", action="store_true")

    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("doctor")

    p_game = sub.add_parser("game")
    sub_game = p_game.add_subparsers(dest="game_cmd")
    sub_game.add_parser("status")
    p_tick = sub_game.add_parser("tick")
    p_tick.add_argument("--seed", type=int)

    p_q = sub_game.add_parser("quest")
    sub_q = p_q.add_subparsers(dest="quest_cmd")
    sub_q.add_parser("list")
    p_claim = sub_q.add_parser("claim")
    p_claim.add_argument("quest_id")

    ns = p.parse_args(argv)

    if ns.cmd == "doctor":
        rc = run_doctor()
        if rc == 0:
            _emit_hook(bool(ns.write), GameEvent("doctor_ok", 1))
        return rc

    if ns.cmd == "game":
        if ns.game_cmd == "status":
            _print_game_status()
            return 0
        if ns.game_cmd == "tick":
            return _run_game_tick(bool(ns.write), ns.seed)
        if ns.game_cmd == "quest":
            if ns.quest_cmd == "list":
                _print_game_status()
                return 0
            if ns.quest_cmd == "claim":
                return _quest_claim(str(ns.quest_id), bool(ns.write))
        print("Use: python -m astra game status|tick|quest list|quest claim <id>")
        return 1

    if ns.once:
        if ns.once == "3":
            _emit_hook(bool(ns.write), GameEvent("airi_status", 1))
        return dispatch(ns.once)

    while True:
        print("=== ASTRA HUB (Sprint 2C) ===")
        for key, label in MENU:
            print(f"[{key}] {label}")
        choice = input("> ").strip()
        code = dispatch(choice)
        if choice == "0":
            return code
""")

# tests
w(Path("tests/test_engine_seed.py"), """from astra.game.engine import tick_day
from astra.game.state import default_state


def test_tick_seed_deterministic():
    s = default_state()
    a, _, _ = tick_day(s, seed=123)
    b, _, _ = tick_day(s, seed=123)
    assert a.to_dict() == b.to_dict()
""")

print("SPRINT 2C files generated.")