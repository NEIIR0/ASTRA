from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def w(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# 1) astra/config.py (przywraca config_path + load/save + gameplay defaults)
w(
    "astra/config.py",
    """from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


DEFAULT_GAMEPLAY: dict[str, Any] = {
    "xp_per_tick": 5,
    "power_loss_per_tick": 1,
    "anomaly_hull_loss": 1,
    "anomaly_chance": 0.5,
    "xp_level_base": 10,  # progi: 10, 30, 60, ... (triangular * base)
}


@dataclass(frozen=True)
class Config:
    profile: str = "offline"
    log_enabled: bool = False
    root: Path = Path(".")
    gameplay: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_GAMEPLAY))


def config_path(*, root: Path | None = None, profile: str = "offline") -> Path:
    r = Path.cwd() if root is None else Path(root)
    return r / "data" / "profiles" / str(profile) / "config.json"


def load_config(root: Path | None = None, *, profile: str = "offline") -> Config:
    r = Path.cwd() if root is None else Path(root)
    p = config_path(root=r, profile=profile)

    gameplay = dict(DEFAULT_GAMEPLAY)
    if p.exists():
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                gp = raw.get("gameplay")
                if isinstance(gp, dict):
                    gameplay.update(gp)
        except Exception:
            # SAFE: jeśli config uszkodzony, jedziemy na defaultach
            pass

    return Config(profile=str(profile), log_enabled=False, root=r, gameplay=gameplay)


def save_config(cfg: Config) -> Path:
    p = config_path(root=cfg.root, profile=cfg.profile)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"gameplay": cfg.gameplay}
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    return p


__all__ = ["Config", "DEFAULT_GAMEPLAY", "config_path", "load_config", "save_config"]
""",
)

# 2) astra/game/engine.py (tick używa cfg.gameplay; default zachowany)
w(
    "astra/game/engine.py",
    """from __future__ import annotations

import random
from typing import Any


def _level_from_xp(xp: int, base: int) -> int:
    # progi: L=2 => base*1, L=3 => base*3, L=4 => base*6, ... => base * L*(L-1)/2
    lvl = 1
    while True:
        nxt = lvl + 1
        need = base * (nxt * (nxt - 1) // 2)
        if xp >= need:
            lvl = nxt
        else:
            return lvl


def tick_day(state: Any, *, seed: int | None = None, gameplay: dict[str, Any] | None = None):
    gp = dict(gameplay or {})
    xp_gain = int(gp.get("xp_per_tick", 5))
    power_loss = int(gp.get("power_loss_per_tick", 1))
    hull_loss = int(gp.get("anomaly_hull_loss", 1))
    chance = float(gp.get("anomaly_chance", 0.5))
    base = int(gp.get("xp_level_base", 10))

    last_seed = int(getattr(state, "last_seed", 0) or 0)
    use_seed = last_seed if seed is None else int(seed)

    rng = random.Random(use_seed)
    anomaly = rng.random() < chance

    ship = state.ship
    player = state.player

    day0 = int(state.day)
    day1 = day0 + 1

    dh = -hull_loss if anomaly else 0
    dp = -power_loss

    hull1 = int(ship.hull) + dh
    power1 = int(ship.power) + dp

    xp1 = int(player.xp) + xp_gain
    lvl0 = int(player.level)
    lvl1 = _level_from_xp(xp1, base=base)

    data = state.to_dict()
    data["day"] = day1
    data["last_seed"] = use_seed
    data["ship"] = {"sector": ship.sector, "hull": hull1, "power": power1}
    data["player"] = {"xp": xp1, "level": lvl1}

    s1 = state.__class__(**data)

    txt: list[str] = [f"Dzień {day0} -> {day1}"]
    if anomaly:
        txt.append(f"- hull: {dh} (anomalia)")
    txt.append(f"- power: {dp}")
    txt.append(f"+XP {xp_gain} (xp={xp1}, lvl={lvl1})")
    if lvl1 > lvl0:
        txt.append(f"ACHIEVEMENT: Awans: Poziom {lvl1}")

    events = [{"type": "tick_done", "amount": 1, "day": day1}]
    return s1, txt, events


__all__ = ["tick_day"]
""",
)

# 3) astra/game/sectors.py (upewniamy się że actions są źródłem prawdy)
w(
    "astra/game/sectors.py",
    """from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sector:
    name: str
    title: str = ""
    desc: str = ""
    actions: tuple[str, ...] = ("tick", "move")


DEFAULT_SECTORS: dict[str, Sector] = {
    "Mostek": Sector(
        name="Mostek",
        title="Mostek",
        desc="Centrum dowodzenia statku.",
        actions=("tick", "move"),
    ),
    "AIRI": Sector(
        name="AIRI",
        title="Moduł AIRI",
        desc="Interfejs do AIRI (kontrakt v1).",
        actions=("tick", "move"),
    ),
    "Sektor A-1": Sector(
        name="Sektor A-1",
        title="Sektor A-1",
        desc="Strefa testowa.",
        actions=("tick", "move"),
    ),
}


def sector_exists(name: str) -> bool:
    return str(name) in DEFAULT_SECTORS


def allowed_actions(sector: str) -> tuple[str, ...]:
    s = DEFAULT_SECTORS.get(str(sector))
    return s.actions if s else ()


__all__ = ["Sector", "DEFAULT_SECTORS", "sector_exists", "allowed_actions"]
""",
)

# 4) astra/game/policy.py (blokada: unknown_sector + action not allowed in current sector + power_down blocks move)
w(
    "astra/game/policy.py",
    """from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .events import EventBus
from .sectors import DEFAULT_SECTORS, allowed_actions


@dataclass(frozen=True)
class PolicyDecision:
    ok: bool
    reason: str = ""


def check_action_allowed(*, state: Any, action: str, kwargs: dict[str, Any], bus: EventBus) -> PolicyDecision:
    ship = getattr(state, "ship", None)
    sector = getattr(ship, "sector", "Mostek") if ship is not None else "Mostek"
    hull = getattr(ship, "hull", None) if ship is not None else None
    power = getattr(ship, "power", None) if ship is not None else None

    # global: game over blocks tick
    if action == "tick" and hull == 0:
        bus.emit("action_blocked", action=action, reason="game_over")
        return PolicyDecision(False, "game_over")

    # sector capability
    acts = allowed_actions(str(sector))
    if acts and action not in acts:
        bus.emit("action_not_allowed", action=action, sector=str(sector))
        return PolicyDecision(False, "action_not_allowed")

    # power==0: blokuj ruch
    if action == "move" and power == 0:
        bus.emit("action_blocked", action=action, reason="power_down")
        return PolicyDecision(False, "power_down")

    # move: target must exist
    if action == "move":
        target = str(kwargs.get("sector", "")).strip()
        if not target or DEFAULT_SECTORS.get(target) is None:
            bus.emit("sector_unknown", sector=target)
            return PolicyDecision(False, "unknown_sector")

    return PolicyDecision(True, "")
""",
)

# 5) astra/game/reducer.py (ładuje config per profile przez _profile; tick używa gameplay)
w(
    "astra/game/reducer.py",
    """from __future__ import annotations

from typing import Any

from astra.config import load_config

from .engine import tick_day
from .events import EventBus
from .policy import check_action_allowed
from .result import ActionError, ActionResult, fail, ok
from .rules import apply_rules
from .validate import validate_move, validate_state, validate_tick


def reduce(state: Any, action: str, **kwargs: Any) -> ActionResult:
    bus = EventBus()

    profile = str(kwargs.pop("_profile", "offline"))
    cfg = load_config(profile=profile)

    st_errs = validate_state(state)
    if st_errs:
        return fail(state, errors=st_errs, text=["ERROR: state validation failed."])

    dec = check_action_allowed(state=state, action=action, kwargs=kwargs, bus=bus)
    if not dec.ok:
        return fail(
            state,
            errors=[ActionError(code="policy_blocked", message=dec.reason, field="action")],
            text=[f"ERROR: policy blocked ({dec.reason})."],
            events=bus.drain(),
        )

    if action == "tick":
        seed = kwargs.get("seed")
        v = validate_tick(seed=seed)
        if v:
            return fail(state, errors=v, text=["ERROR: tick validation failed."], events=bus.drain())

        s1, txt, events = tick_day(state, seed=seed, gameplay=cfg.gameplay)
        s2, rtxt, rev = apply_rules(s1)
        return ok(s2, text=list(txt) + list(rtxt), events=list(events) + list(rev) + bus.drain())

    if action == "move":
        sector = str(kwargs.get("sector", ""))
        v = validate_move(sector=sector)
        if v:
            return fail(state, errors=v, text=["ERROR: move validation failed."], events=bus.drain())

        ship = state.ship
        data = state.to_dict()
        data["ship"] = {"sector": sector, "hull": ship.hull, "power": ship.power}
        s1 = state.__class__(**data)

        txt = [f"SECTOR MOVE: {ship.sector} -> {sector}"]
        events = [{"type": "sector_moved", "sector": sector}]

        s2, rtxt, rev = apply_rules(s1)
        return ok(s2, text=txt + list(rtxt), events=list(events) + list(rev) + bus.drain())

    return fail(
        state,
        errors=[ActionError(code="unknown_action", message=f"Unknown action: {action}", field="action")],
        text=["ERROR: unknown action."],
        events=bus.drain(),
    )
""",
)

# 6) astra/game/actions.py (forward _profile)
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


def run_action(state: Any, action: Any, *, profile: str = "offline") -> ActionResult:
    if isinstance(action, TickDay):
        return reduce(state, "tick", seed=action.seed, _profile=profile)
    if isinstance(action, MoveSector):
        return reduce(state, "move", sector=action.sector, _profile=profile)
    return reduce(state, "unknown", _profile=profile)


def apply_action(state: Any, action: str, **kwargs: Any) -> tuple[Any, list[str], list[dict[str, Any]]]:
    # Backward-compatible API: returns (state, text, events)
    r = reduce(state, action, **kwargs)
    return r.state, r.text, r.events


__all__ = ["TickDay", "MoveSector", "run_action", "apply_action"]
""",
)

# 7) astra/game/replay.py (pass _profile into apply_action; snapshot ok)
w(
    "astra/game/replay.py",
    """from __future__ import annotations

import json
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any

from .actions import apply_action
from .state import default_state


def _logbook_path(profile: str) -> Path:
    return Path("data") / "profiles" / profile / "logbook.jsonl"


def _dc_from_dict(proto: Any, data: dict[str, Any]) -> Any:
    if not is_dataclass(proto):
        return data
    kwargs: dict[str, Any] = {}
    for k, v in data.items():
        cur = getattr(proto, k, None)
        if is_dataclass(cur) and isinstance(v, dict):
            kwargs[k] = _dc_from_dict(cur, v)
        else:
            kwargs[k] = v
    # dataclass: rebuild using known fields from proto
    base = {}
    for f in getattr(proto, "__dataclass_fields__", {}).keys():
        base[f] = getattr(proto, f)
    base.update(kwargs)
    return proto.__class__(**base)


def replay_state(*, profile: str):
    p = _logbook_path(profile)
    if not p.exists():
        return default_state()

    items: list[dict[str, Any]] = []
    for raw in p.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            items.append(obj)

    last_snap: dict[str, Any] | None = None
    start_idx = 0
    for i, obj in enumerate(items):
        if obj.get("type") == "snapshot" and isinstance(obj.get("state"), dict):
            last_snap = obj["state"]
            start_idx = i + 1

    proto = default_state()
    state = _dc_from_dict(proto, last_snap) if last_snap else proto

    for obj in items[start_idx:]:
        if obj.get("type") != "command":
            continue

        action = obj.get("action")
        if action == "tick":
            state, _txt, _events = apply_action(state, "tick", seed=obj.get("seed"), _profile=profile)
        elif action == "move":
            state, _txt, _events = apply_action(
                state, "move", sector=obj.get("sector", "Mostek"), _profile=profile
            )

    return state


__all__ = ["replay_state"]
""",
)

# 8) tests: config + policy action_not_allowed
w(
    "tests/test_balance_config.py",
    """from astra.config import load_config


def test_default_config_has_gameplay_keys(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config(profile="dev")
    assert isinstance(cfg.gameplay, dict)
    assert cfg.gameplay["xp_per_tick"] == 5
""",
)

w(
    "tests/test_policy_action_not_allowed.py",
    """from dataclasses import replace

from astra.game.policy import check_action_allowed
from astra.game.events import EventBus
from astra.game.state import default_state


def test_action_not_allowed_emits_event():
    s = default_state()
    # sektor "Mostek" defaultowo ma tick/move, więc użyjemy sztucznej akcji
    bus = EventBus()
    dec = check_action_allowed(state=s, action="warp", kwargs={}, bus=bus)
    # jeśli sector ma listę akcji, warp powinien być zablokowany
    assert dec.ok is False
    ev = bus.drain()
    assert any(e.get("type") == "action_not_allowed" for e in ev)
""",
)

print("SPRINT 2Q applied: per-profile gameplay config + sector action policy + tick uses config + replay passes profile.")
"""
)

print("tools/sprint2q.py generated.")
