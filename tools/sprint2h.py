from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def w(path: str, text: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


# 1) Game Core v2 — ACTIONS
w(
    "astra/game/actions.py",
    """from __future__ import annotations

from dataclasses import replace
from typing import Any

from .engine import tick_day
from .events import GameEvent


def move_sector(state, *, sector: str) -> tuple[Any, list[str], list[dict[str, Any]]]:
    txt: list[str] = [f"SECTOR MOVE: {state.ship.sector} -> {sector}"]
    new_ship = replace(state.ship, sector=sector)
    new_state = replace(state, ship=new_ship)
    events = [GameEvent("sector_moved", None, {"sector": sector}).to_dict()]
    return new_state, txt, events


def apply_action(
    state,
    action: str,
    *,
    seed: int | None = None,
    sector: str | None = None,
) -> tuple[Any, list[str], list[dict[str, Any]]]:
    if action == "tick":
        return tick_day(state, seed=seed)
    if action == "move":
        if not sector:
            raise ValueError("move requires sector")
        return move_sector(state, sector=sector)
    raise ValueError(f"Unknown action: {action}")
""",
)

# 2) CLI — game action (tick/move), globals --profile/--write order-agnostic
w(
    "astra/cli.py",
    """from __future__ import annotations

import argparse

from .doctor import run_doctor
from .report import make_latest_report_zip
from .router import dispatch

from .game.actions import apply_action
from .game.logbook import append_events
from .game.storage import load_state, save_state


MENU = [
    ("1", "Ustawienia"),
    ("2", "Udaj się na mostek"),
    ("3", "Udaj się do AIRI"),
    ("4", "Uniwersum"),
    ("5", "Tryb gry"),
    ("0", "Wyjście"),
]


def _split_globals(argv: list[str] | None) -> tuple[argparse.Namespace, list[str]]:
    g = argparse.ArgumentParser(add_help=False)
    g.add_argument("--profile", default="offline")
    g.add_argument("--write", action="store_true")
    ns, rest = g.parse_known_args(argv)
    return ns, rest


def _run_game_status(*, profile: str) -> int:
    s = load_state(profile=profile)
    print("GAME STATUS")
    print(f"- profile: {profile}")
    print(f"- day: {s.day}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")
    print(f"- ship: hull={s.ship.hull} power={s.ship.power} sector={s.ship.sector}")
    print(f"- last_seed: {getattr(s, 'last_seed', 0)}")
    qs = getattr(s, "quests", [])
    if qs:
        print("- quests:")
        for q in qs:
            print(f"  * {q.quest_id} [{q.status}] {q.progress}")
    return 0


def _run_game_tick(*, profile: str, write: bool, seed: int | None) -> int:
    s0 = load_state(profile=profile)
    s1, txt, events = apply_action(s0, "tick", seed=seed)

    print("GAME TICK")
    print(f"- profile: {profile}")
    print(f"- seed: {seed if seed is not None else getattr(s0, 'last_seed', 0)}")
    for t in txt:
        print(f"- {t}")
    for ev in events:
        print(f"- {ev}")

    if write:
        save_state(s1, profile=profile)
        append_events(events, write=True, profile=profile)
        print(f"- saved: data/profiles/{profile}/game_state.json")
        print(f"- logbook: data/profiles/{profile}/logbook.jsonl")
    else:
        print("- not saved (SAFE default). Use: --write")
    return 0


def _run_game_action_move(*, profile: str, write: bool, sector: str) -> int:
    s0 = load_state(profile=profile)
    s1, txt, events = apply_action(s0, "move", sector=sector)

    print("ACTION MOVE")
    print(f"- profile: {profile}")
    for t in txt:
        print(f"- {t}")
    for ev in events:
        print(f"- {ev}")

    if write:
        save_state(s1, profile=profile)
        append_events(events, write=True, profile=profile)
        print(f"- saved: data/profiles/{profile}/game_state.json")
    else:
        print("- not saved (SAFE default). Use: --write")
    return 0


def main(argv: list[str] | None = None) -> int:
    g, rest = _split_globals(argv)
    profile = str(g.profile)
    write = bool(g.write)

    p = argparse.ArgumentParser(prog="astra")
    p.add_argument("--once", choices=[m[0] for m in MENU])

    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("doctor")

    p_report = sub.add_parser("report")
    p_report.add_argument("--zip", action="store_true")

    p_game = sub.add_parser("game")
    game_sub = p_game.add_subparsers(dest="game_cmd")

    game_sub.add_parser("status")

    p_tick = game_sub.add_parser("tick")
    p_tick.add_argument("--seed", type=int)

    p_action = game_sub.add_parser("action")
    action_sub = p_action.add_subparsers(dest="action_cmd")

    p_a_tick = action_sub.add_parser("tick")
    p_a_tick.add_argument("--seed", type=int)

    p_a_move = action_sub.add_parser("move")
    p_a_move.add_argument("--sector", required=True)

    ns = p.parse_args(rest)

    if ns.cmd == "doctor":
        return run_doctor()

    if ns.cmd == "report":
        if ns.zip:
            out = make_latest_report_zip(profile=profile)
            print(out if out else "Brak error_*.log w data/errors")
            return 0
        print("Use: python -m astra report --zip [--profile X]")
        return 1

    if ns.cmd == "game":
        if ns.game_cmd == "status":
            return _run_game_status(profile=profile)
        if ns.game_cmd == "tick":
            return _run_game_tick(profile=profile, write=write, seed=ns.seed)
        if ns.game_cmd == "action":
            if ns.action_cmd == "tick":
                return _run_game_tick(profile=profile, write=write, seed=ns.seed)
            if ns.action_cmd == "move":
                return _run_game_action_move(profile=profile, write=write, sector=str(ns.sector))
            print("Use: python -m astra game action (tick|move) ...")
            return 1
        print("Use: python -m astra game (status|tick|action) ...")
        return 1

    if ns.once is not None:
        return dispatch(ns.once, profile=profile)

    while True:
        print("=== ASTRA HUB ===")
        for key, label in MENU:
            print(f"[{key}] {label}")
        choice = input("> ").strip()
        code = dispatch(choice, profile=profile)
        if choice == "0":
            return code


if __name__ == "__main__":
    raise SystemExit(main())
""",
)

# 3) Tests — actions
w(
    "tests/test_actions.py",
    """import subprocess
import sys


def test_action_move_no_write():
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "astra",
            "game",
            "action",
            "move",
            "--sector",
            "Mostek",
            "--profile",
            "offline",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "ACTION MOVE" in r.stdout
    assert "not saved" in r.stdout
""",
)

print("SPRINT 2H (Actions) applied.")
