from __future__ import annotations

import argparse

from .doctor import run_doctor
from .router import dispatch

MENU = [
    ("1", "Ustawienia"),
    ("2", "Udaj się na mostek"),
    ("3", "Udaj się do AIRI"),
    ("4", "Uniwersum"),
    ("0", "Wyjście"),
]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="astra")
    p.add_argument("--once", choices=[m[0] for m in MENU])
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("doctor")
    ns = p.parse_args(argv)

    if ns.cmd == "doctor":
        return run_doctor()

    if ns.once:
        return dispatch(ns.once)

    while True:
        print("=== ASTRA HUB (Sprint 1.5) ===")
        for k, l in MENU:
            print(f"[{k}] {l}")
        ch = input("> ").strip()
        code = dispatch(ch)
        if ch == "0":
            return code
