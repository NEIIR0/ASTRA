import argparse

from .doctor import run_doctor


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="airi")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("hub")
    sub.add_parser("chat")
    sub.add_parser("eval")
    sub.add_parser("doctor")

    ns = p.parse_args(argv)

    if ns.cmd is None:
        print("A.I.R.I boot OK")
        print("Next: python -m airi doctor")
        return 0

    if ns.cmd == "doctor":
        return run_doctor()

    print(f"{ns.cmd}: not implemented yet (Sprint 0 stub).")
    return 0
