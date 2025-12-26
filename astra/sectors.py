from __future__ import annotations

import argparse

from .game.sectors import DEFAULT_SECTORS


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="astra.sectors")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("list")
    p_show = sub.add_parser("show")
    p_show.add_argument("--name", required=True)

    ns = p.parse_args(argv)

    if ns.cmd in (None, "list"):
        print("SECTORS")
        for k in sorted(DEFAULT_SECTORS.keys()):
            s = DEFAULT_SECTORS[k]
            print(f"- {s.name}: {s.title}")
        return 0

    if ns.cmd == "show":
        s = DEFAULT_SECTORS.get(str(ns.name))
        if s is None:
            print("NOT FOUND")
            return 1
        print("SECTOR")
        print(f"- name: {s.name}")
        print(f"- title: {s.title}")
        print(f"- desc: {s.desc}")
        print(f"- actions: {list(s.actions)}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
