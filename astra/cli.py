from __future__ import annotations

import argparse
import sys

from .doctor import run_doctor
from .game.actions import apply_action
from .game.logbook import append_snapshot, append_tx
from .game.storage import load_state, save_state
from .report import make_latest_report_zip
from .router import dispatch

MENU = [
    ("1", "Ustawienia"),
    ("2", "Udaj siÄ‚â€žĂ˘â€žË na mostek"),
    ("3", "Udaj siÄ‚â€žĂ˘â€žË do AIRI"),
    ("4", "Uniwersum"),
    ("5", "Tryb gry"),
    ("0", "WyjĂ„Ä…Ă˘â‚¬Ĺźcie"),
]


def _split_globals(argv: list[str] | None) -> tuple[argparse.Namespace, list[str]]:
    args = list(argv or [])
    profile = "offline"
    write = False

    out: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--profile" and i + 1 < len(args):
            profile = args[i + 1]
            i += 2
            continue
        if a == "--write":
            write = True
            i += 1
            continue
        out.append(a)
        i += 1

    return argparse.Namespace(profile=profile, write=write), out


def _run_game_status(*, profile: str) -> int:
    s = load_state(profile=profile)
    ship = s.ship
    player = s.player
    print("GAME STATUS")
    print(f"- profile: {profile}")
    print(f"- day: {s.day}")
    print(f"- level: {player.level} (xp={player.xp})")
    print(f"- ship: hull={ship.hull} power={ship.power} sector={ship.sector}")
    print(f"- last_seed: {getattr(s, 'last_seed', 0)}")
    print("- quests:")
    for q in getattr(s, "quests", []):
        print(f"  * {q.quest_id} [{q.status}] {q.progress}")
    return 0


def _run_game_tick(*, profile: str, write: bool, seed: int | None) -> int:
    s0 = load_state(profile=profile)
    s1, txt, events = apply_action(s0, "tick", seed=seed, profile=profile)

    print("GAME TICK")
    print(f"- profile: {profile}")
    print(f"- seed: {seed}")
    for t in txt:
        print(f"- {t}")
    for ev in events:
        print(f"- {ev}")

    if write:
        save_state(s1, profile=profile)
        append_tx(profile, "tick", events, seed=seed)
        append_snapshot(profile, s1)
        print(f"- saved: data/profiles/{profile}/game_state.json")
        print(f"- logbook: data/profiles/{profile}/logbook.jsonl")
    else:
        print("- not saved (SAFE default). Use: --write")
    return 0


def _run_game_snapshot(*, profile: str) -> int:
    from .game.storage import load_state

    s = load_state(profile=profile)
    append_snapshot(profile, s)
    print("SNAPSHOT")
    print(f"- profile: {profile}")
    print("- appended: snapshot -> logbook.jsonl")
    return 0


def _run_game_move(*, profile: str, write: bool, sector: str) -> int:
    s0 = load_state(profile=profile)
    s1, txt, events = apply_action(s0, "move", sector=sector, profile=profile)

    print("ACTION MOVE")
    print(f"- profile: {profile}")
    for t in txt:
        print(f"- {t}")
    for ev in events:
        print(f"- {ev}")

    if write:
        save_state(s1, profile=profile)
        append_tx(profile, "move", events, sector=sector)
        append_snapshot(profile, s1)
        print(f"- saved: data/profiles/{profile}/game_state.json")
    else:
        print("- not saved (SAFE default). Use: --write")
    return 0


def _run_game_replay(*, profile: str) -> int:
    from .game.replay import replay_state

    s = replay_state(profile=profile)
    ship = s.ship
    player = s.player
    print("REPLAY")
    print(f"- profile: {profile}")
    print(f"- day: {s.day}")
    print(f"- level: {player.level} (xp={player.xp})")
    print(f"- ship: hull={ship.hull} power={ship.power} sector={ship.sector}")
    print(f"- last_seed: {getattr(s, 'last_seed', 0)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
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

    game_sub.add_parser("snapshot")

    p_tick = game_sub.add_parser("tick")
    p_tick.add_argument("--seed", type=int)
    game_sub.add_parser("replay")
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
        if ns.game_cmd == "snapshot":
            return _run_game_snapshot(profile=profile)
        if ns.game_cmd == "replay":
            return _run_game_replay(profile=profile)
        if ns.game_cmd == "action":
            if ns.action_cmd == "tick":
                return _run_game_tick(profile=profile, write=write, seed=ns.seed)
            if ns.action_cmd == "move":
                return _run_game_move(profile=profile, write=write, sector=str(ns.sector))
            print("Use: python -m astra game action (tick|move) ...")
            return 1
        print("Use: python -m astra game (status|tick|replay|action) ...")
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
