from __future__ import annotations

import argparse

from .doctor import run_doctor
from .game.loop import tick_day
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


def _run_game_tick(save: bool) -> int:
    state = load_state()
    new_state, events = tick_day(state)

    print("GAME TICK")
    for e in events:
        print(f"- {e}")

    print(f"- new_day: {new_state.day}")
    print(f"- power: {new_state.ship.power}")
    print(f"- level: {new_state.player.level} (xp={new_state.player.xp})")

    if save:
        save_state(new_state)
        print("- saved: data/game_state.json")
    else:
        print("- not saved (SAFE default). Use: --save")

    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="astra")
    p.add_argument("--once", choices=[m[0] for m in MENU])

    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("doctor")

    p_game = sub.add_parser("game")
    sub_game = p_game.add_subparsers(dest="game_cmd")
    p_tick = sub_game.add_parser("tick")
    p_tick.add_argument("--save", action="store_true")

    ns = p.parse_args(argv)

    if ns.cmd == "doctor":
        return run_doctor()

    if ns.cmd == "game":
        if ns.game_cmd == "tick":
            return _run_game_tick(bool(ns.save))
        print("Use: python -m astra game tick [--save]")
        return 1

    if ns.once:
        return dispatch(ns.once)

    while True:
        print("=== ASTRA HUB (Sprint 2A) ===")
        for key, label in MENU:
            print(f"[{key}] {label}")
        choice = input("> ").strip()
        code = dispatch(choice)
        if choice == "0":
            return code
