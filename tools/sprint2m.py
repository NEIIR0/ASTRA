from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()

def w(path: str, text: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

# 1) logbook.py (snapshot + tx)
w("astra/game/logbook.py", """from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def logbook_path(profile: str) -> Path:
    return Path("data") / "profiles" / profile / "logbook.jsonl"


def _write_lines(p: Path, lines: list[dict[str, Any]]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        for obj in lines:
            f.write(json.dumps(obj, ensure_ascii=False) + "\\n")


def to_dict(obj: Any) -> dict[str, Any]:
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()  # type: ignore[no-any-return]
    raise TypeError("Object is not serializable to dict")


def append_tx(profile: str, action: str, events: list[dict[str, Any]], **kwargs: Any) -> None:
    lines: list[dict[str, Any]] = [{"type": "command", "action": action, **kwargs}]
    lines.extend(list(events))
    _write_lines(logbook_path(profile), lines)


def append_snapshot(profile: str, state: Any) -> None:
    _write_lines(logbook_path(profile), [{"type": "snapshot", "state": to_dict(state)}])


def iter_logbook(profile: str) -> list[dict[str, Any]]:
    p = logbook_path(profile)
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    for raw in p.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def find_last_snapshot(profile: str) -> dict[str, Any] | None:
    last: dict[str, Any] | None = None
    for obj in iter_logbook(profile):
        if obj.get("type") == "snapshot" and isinstance(obj.get("state"), dict):
            last = obj["state"]
    return last


__all__ = ["append_tx", "append_snapshot", "iter_logbook", "find_last_snapshot", "logbook_path", "to_dict"]
""")

# 2) replay.py (start od snapshotu)
w("astra/game/replay.py", """from __future__ import annotations

from typing import Any

from .actions import apply_action
from .logbook import find_last_snapshot, iter_logbook
from .state import default_state


def _state_from_dict_fallback(d: dict[str, Any]):
    # działa z Twoim obecnym patternem: s.__class__(**s.to_dict())
    s0 = default_state()
    return s0.__class__(**d)  # type: ignore[arg-type]


def replay_state(*, profile: str):
    snap = find_last_snapshot(profile)
    state = _state_from_dict_fallback(snap) if snap else default_state()

    for obj in iter_logbook(profile):
        if obj.get("type") != "command":
            continue

        action = obj.get("action")
        if action == "tick":
            state, _txt, _events = apply_action(state, "tick", seed=obj.get("seed"))
        elif action == "move":
            state, _txt, _events = apply_action(state, "move", sector=obj.get("sector", "Mostek"))

    return state
""")

# 3) Patch cli.py: import + komenda game snapshot + snapshot przy --write
cli_p = ROOT / "astra/cli.py"
cli = cli_p.read_text("utf-8")

cli = re.sub(
    r"from \.game\.logbook import append_tx",
    "from .game.logbook import append_snapshot, append_tx",
    cli,
    count=1,
)

# dodaj handler _run_game_snapshot jeśli brak
if "_run_game_snapshot" not in cli:
    insert_after = "def _run_game_move"
    idx = cli.find(insert_after)
    if idx != -1:
        # wstaw przed _run_game_move
        block = """def _run_game_snapshot(*, profile: str) -> int:
    from .game.storage import load_state

    s = load_state(profile=profile)
    append_snapshot(profile, s)
    print("SNAPSHOT")
    print(f"- profile: {profile}")
    print("- appended: snapshot -> logbook.jsonl")
    return 0


"""
        cli = cli[:idx] + block + cli[idx:]

# dodaj parser "snapshot" i routing
cli = cli.replace('game_sub.add_parser("status")', 'game_sub.add_parser("status")\n\n    game_sub.add_parser("snapshot")')

cli = cli.replace(
    'if ns.game_cmd == "tick":\n            return _run_game_tick(profile=profile, write=write, seed=ns.seed)',
    'if ns.game_cmd == "tick":\n            return _run_game_tick(profile=profile, write=write, seed=ns.seed)\n        if ns.game_cmd == "snapshot":\n            return _run_game_snapshot(profile=profile)',
)

# po zapisaniu stanu w tick/move dopnij snapshot (po save_state)
cli = cli.replace(
    'save_state(s1, profile=profile)\n        append_tx(profile, "tick", events, seed=seed)',
    'save_state(s1, profile=profile)\n        append_tx(profile, "tick", events, seed=seed)\n        append_snapshot(profile, s1)',
)

cli = cli.replace(
    'save_state(s1, profile=profile)\n        append_tx(profile, "move", events, sector=sector)',
    'save_state(s1, profile=profile)\n        append_tx(profile, "move", events, sector=sector)\n        append_snapshot(profile, s1)',
)

cli_p.write_text(cli, encoding="utf-8")

# 4) test
w("tests/test_snapshot_replay.py", """from astra.game.replay import replay_state
from astra.game.storage import load_state, save_state
from astra.game.logbook import append_snapshot


def test_replay_uses_snapshot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    s = load_state(profile="dev")
    save_state(s, profile="dev")
    append_snapshot("dev", s)

    out = replay_state(profile="dev")
    assert out.day == s.day
""")

print("SPRINT 2M applied: snapshot + replay-from-snapshot + CLI game snapshot + tests.")
