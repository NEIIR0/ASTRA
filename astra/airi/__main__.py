from __future__ import annotations

import argparse
import sys

from astra.game.actions import apply_action
from astra.game.logbook import append_command, append_events
from astra.game.storage import load_state, save_state

from .stub import StubAiri


def _split_globals(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    profile = "offline"
    write = False
    out: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--profile" and i + 1 < len(argv):
            profile = argv[i + 1]
            i += 2
            continue
        if a == "--write":
            write = True
            i += 1
            continue
        out.append(a)
        i += 1
    return argparse.Namespace(profile=profile, write=write), out


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    g, rest = _split_globals(argv)
    profile = str(g.profile)
    write = bool(g.write)

    p = argparse.ArgumentParser(prog="astra.airi")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("propose")
    sp.add_argument("--apply", action="store_true")

    ns = p.parse_args(rest)
    if ns.cmd != "propose":
        print("Use: python -m astra.airi propose [--apply] [--profile X] [--write]")
        return 1

    s0 = load_state(profile=profile)
    props = StubAiri().propose(state=s0)

    print("AIRI PROPOSE")
    print(f"- profile: {profile}")
    if not props:
        print("- proposals: 0")
        return 0

    for i, pr in enumerate(props, 1):
        print(f"- [{i}] {pr.action} {pr.kwargs} conf={pr.confidence:.2f} reason={pr.reason}")

    if not ns.apply:
        return 0

    pr0 = props[0]
    s1, txt, events = apply_action(s0, pr0.action, **pr0.kwargs, profile=profile)

    print("AIRI APPLY (first proposal)")
    for t in txt:
        print(f"- {t}")
    for ev in events:
        print(f"- {ev}")

    if write:
        save_state(s1, profile=profile)
        append_command(profile, pr0.action, **pr0.kwargs)
        append_events(profile, events)
        print(f"- saved: data/profiles/{profile}/game_state.json")
        print(f"- logbook: data/profiles/{profile}/logbook.jsonl")
    else:
        print("- not saved (SAFE default). Use: --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
