from __future__ import annotations

import json
from pathlib import Path

V = "0.0.22"  # ASTRA v0.02.2


def w(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")


# --- version bump
w(Path("astra_common/__init__.py"), '__version__ = "0.0.22"\n')

w(
    Path("pyproject.toml"),
    """[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "astra-airi"
version = "0.0.22"
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
""",
)


# --- migrations
w(
    Path("astra/game/migrations.py"),
    """from __future__ import annotations

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
""",
)


# --- state v3 (adds last_seed)
w(
    Path("astra/game/state.py"),
    """from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .quests import QuestProgress, ensure_progress

SCHEMA_VERSION = 3


@dataclass(frozen=True)
class ShipState:
    sector: str = "Mostek"
    hull: int = 100
    power: int = 100


@dataclass(frozen=True)
class PlayerState:
    xp: int = 0
    level: int = 1


@dataclass(frozen=True)
class GameState:
    schema_version: int = SCHEMA_VERSION
    day: int = 0
    ship: ShipState = field(default_factory=ShipState)
    player: PlayerState = field(default_factory=PlayerState)
    achievements: list[str] = field(default_factory=list)
    quests: list[QuestProgress] = field(default_factory=list)
    last_seed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "day": self.day,
            "ship": {"sector": self.ship.sector, "hull": self.ship.hull, "power": self.ship.power},
            "player": {"xp": self.player.xp, "level": self.player.level},
            "achievements": list(self.achievements),
            "quests": [q.to_dict() for q in self.quests],
            "last_seed": self.last_seed,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GameState":
        sv = int(d.get("schema_version", 0))

        ship_d = d.get("ship", {}) or {}
        player_d = d.get("player", {}) or {}

        base = GameState(
            schema_version=SCHEMA_VERSION,
            day=int(d.get("day", 0)),
            ship=ShipState(
                sector=str(ship_d.get("sector", "Mostek")),
                hull=int(ship_d.get("hull", 100)),
                power=int(ship_d.get("power", 100)),
            ),
            player=PlayerState(
                xp=int(player_d.get("xp", 0)),
                level=int(player_d.get("level", 1)),
            ),
            achievements=[str(x) for x in (d.get("achievements", []) or [])],
            quests=[],
            last_seed=int(d.get("last_seed", 0) or 0),
        )

        if sv in (1, 2, 3):
            raw = d.get("quests", []) or []
            quests = [QuestProgress.from_dict(x) for x in raw if isinstance(x, dict)]
            return GameState(
                schema_version=SCHEMA_VERSION,
                day=base.day,
                ship=base.ship,
                player=base.player,
                achievements=base.achievements,
                quests=ensure_progress(quests),
                last_seed=base.last_seed,
            )

        raise ValueError(f"Unsupported schema_version={sv} (expected 1/2/3)")


def default_state() -> GameState:
    return GameState(quests=ensure_progress([]))
""",
)


# --- logbook per-profile
w(
    Path("astra/game/logbook.py"),
    """from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PROFILES_ROOT = Path("data") / "profiles"


def safe_profile(name: str) -> str:
    name = (name or "default").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", name):
        return "default"
    return name


def logbook_path(profile: str) -> Path:
    p = safe_profile(profile)
    return PROFILES_ROOT / p / "logbook.jsonl"


def append_events(events: list[dict[str, Any]], *, write: bool, profile: str) -> None:
    if not write:
        return
    path = logbook_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\\n") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\\n")
""",
)


# --- storage per-profile + migrations
w(
    Path("astra/game/storage.py"),
    """from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .migrations import migrate_dict
from .state import GameState, default_state

PROFILES_ROOT = Path("data") / "profiles"


def safe_profile(name: str) -> str:
    name = (name or "default").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", name):
        return "default"
    return name


def state_path(profile: str) -> Path:
    p = safe_profile(profile)
    return PROFILES_ROOT / p / "game_state.json"


def load_state(*, profile: str) -> GameState:
    path = state_path(profile)
    if not path.exists():
        return default_state()
    raw: dict[str, Any] = json.loads(path.read_text("utf-8"))
    migrated = migrate_dict(raw)
    return GameState.from_dict(migrated)


def save_state(state: GameState, *, profile: str) -> None:
    path = state_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state.to_dict(), ensure_ascii=False, indent=2) + "\\n"
    path.write_text(payload, encoding="utf-8")
""",
)


# --- engine: write last_seed deterministically
w(
    Path("astra/game/engine.py"),
    """from __future__ import annotations

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

    temp = replace(
        state,
        day=state.day + 1,
        ship=new_ship,
        player=new_player,
        last_seed=int(seed),
    )

    newly = check_achievements(temp)
    if newly:
        txt.extend([f"ACHIEVEMENT: {x}" for x in newly])
    temp2 = replace(temp, achievements=list(temp.achievements) + newly)

    final = apply_events(temp2, bus)
    return final, txt, [e.to_json() for e in bus]


def apply_external_event(state: GameState, e: GameEvent) -> GameState:
    return apply_events(state, [e])
""",
)


# --- CLI: profile support
w(
    Path("astra/cli.py"),
    """from __future__ import annotations

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


def _print_game_status(profile: str) -> None:
    s = load_state(profile=profile)
    qdefs = defs_by_id()
    print("GAME STATUS")
    print(f"- profile: {profile}")
    print(f"- day: {s.day}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")
    print(f"- ship: hull={s.ship.hull} power={s.ship.power}")
    print(f"- last_seed: {s.last_seed}")
    print("- quests:")
    for q in s.quests:
        qd = qdefs.get(q.quest_id)
        title = qd.title if qd else q.quest_id
        target = qd.target_value if qd else 0
        print(f"  * {q.quest_id} :: {title} [{q.status}] {q.progress}/{target}")


def _run_game_tick(write: bool, seed: int | None, profile: str) -> int:
    state = load_state(profile=profile)
    use_seed = int(seed if seed is not None else (state.day + 1))
    new_state, events_text, events_json = tick_day(state, seed=use_seed)

    print("GAME TICK")
    print(f"- profile: {profile}")
    print(f"- seed: {use_seed}")
    for e in events_text:
        print(f"- {e}")

    if write:
        save_state(new_state, profile=profile)
        append_events(events_json, write=True, profile=profile)
        print(f"- saved: data/profiles/{profile}/game_state.json")
        print(f"- logbook: data/profiles/{profile}/logbook.jsonl")
    else:
        print("- not saved (SAFE default). Use: --write")
    return 0


def _quest_claim(quest_id: str, write: bool, profile: str) -> int:
    state = load_state(profile=profile)
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
        print("Use: python -m astra --profile <p> --write game quest claim <id>")
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
        last_seed=state.last_seed,
    )

    save_state(new_state, profile=profile)
    append_events([{"type": "quest_claimed", "quest_id": quest_id, "reward_xp": qd.reward_xp}], write=True, profile=profile)
    print(f"- claimed: {quest_id}")
    print(f"- reward_xp: {qd.reward_xp} (xp={new_xp})")
    return 0


def _emit_hook(write: bool, profile: str, e: GameEvent) -> None:
    s = load_state(profile=profile)
    s2 = apply_external_event(s, e)
    if write:
        save_state(s2, profile=profile)
        append_events([e.to_json()], write=True, profile=profile)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="astra")
    p.add_argument("--once", choices=[m[0] for m in MENU])
    p.add_argument("--write", action="store_true")
    p.add_argument("--profile", default="default")

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
    profile = str(ns.profile)

    if ns.cmd == "doctor":
        rc = run_doctor()
        if rc == 0:
            _emit_hook(bool(ns.write), profile, GameEvent("doctor_ok", 1))
        return rc

    if ns.cmd == "game":
        if ns.game_cmd == "status":
            _print_game_status(profile)
            return 0
        if ns.game_cmd == "tick":
            return _run_game_tick(bool(ns.write), ns.seed, profile)
        if ns.game_cmd == "quest":
            if ns.quest_cmd == "list":
                _print_game_status(profile)
                return 0
            if ns.quest_cmd == "claim":
                return _quest_claim(str(ns.quest_id), bool(ns.write), profile)
        print("Use: python -m astra --profile <p> game status|tick|quest list|quest claim <id>")
        return 1

    if ns.once:
        if ns.once == "3":
            _emit_hook(bool(ns.write), profile, GameEvent("airi_status", 1))
        return dispatch(ns.once)

    while True:
        print("=== ASTRA HUB (Sprint 2D) ===")
        for key, label in MENU:
            print(f"[{key}] {label}")
        choice = input("> ").strip()
        code = dispatch(choice)
        if choice == "0":
            return code
""",
)

# --- golden tests
w(
    Path("tests/golden/test_tick_golden.py"),
    """import json
from pathlib import Path

from astra.game.engine import tick_day
from astra.game.state import default_state


def _load(name: str) -> dict:
    p = Path(__file__).parent / name
    return json.loads(p.read_text("utf-8"))


def test_golden_tick_seed_123():
    gold = _load("tick_seed_123.json")
    s0 = default_state()
    s1, _txt, events = tick_day(s0, seed=123)
    assert events == gold["events"]
    assert s1.to_dict() == gold["state"]


def test_golden_tick_seed_999():
    gold = _load("tick_seed_999.json")
    s0 = default_state()
    s1, _txt, events = tick_day(s0, seed=999)
    assert events == gold["events"]
    assert s1.to_dict() == gold["state"]
""",
)

gold_123 = {
    "events": [{"type": "tick_done", "amount": 1, "day": 1}],
    "state": {
        "schema_version": 3,
        "day": 1,
        "ship": {"sector": "Mostek", "hull": 99, "power": 99},
        "player": {"xp": 5, "level": 1},
        "achievements": ["Pierwszy dzień"],
        "quests": [
            {"quest_id": "q_doctor_once", "status": "active", "progress": 0},
            {"quest_id": "q_ticks_3", "status": "active", "progress": 1},
            {"quest_id": "q_airi_status", "status": "active", "progress": 0},
        ],
        "last_seed": 123,
    },
}
gold_999 = {
    "events": [{"type": "tick_done", "amount": 1, "day": 1}],
    "state": {
        "schema_version": 3,
        "day": 1,
        "ship": {"sector": "Mostek", "hull": 100, "power": 99},
        "player": {"xp": 5, "level": 1},
        "achievements": ["Pierwszy dzień"],
        "quests": [
            {"quest_id": "q_doctor_once", "status": "active", "progress": 0},
            {"quest_id": "q_ticks_3", "status": "active", "progress": 1},
            {"quest_id": "q_airi_status", "status": "active", "progress": 0},
        ],
        "last_seed": 999,
    },
}

w(Path("tests/golden/tick_seed_123.json"), json.dumps(gold_123, ensure_ascii=False, indent=2) + "\n")
w(Path("tests/golden/tick_seed_999.json"), json.dumps(gold_999, ensure_ascii=False, indent=2) + "\n")

# --- profiles test (pure python, no subprocess)
w(
    Path("tests/test_profiles.py"),
    """from pathlib import Path

from astra.game.storage import load_state, save_state, state_path


def test_profiles_separate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    s = load_state(profile="p1")
    save_state(s, profile="p1")

    p = state_path("p1")
    assert p.exists()
    assert Path("data/profiles/p1/game_state.json").exists()

    s2 = load_state(profile="p2")
    save_state(s2, profile="p2")
    assert Path("data/profiles/p2/game_state.json").exists()
""",
)

print("SPRINT 2D files generated.")
