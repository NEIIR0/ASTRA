from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def w(rel: str, txt: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt, encoding="utf-8")

w("astra/airi/__init__.py", """"AIRI layer (propose actions, ASTRA executes)."\n""")

w("astra/airi/contract.py", """from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ActionProposal:
    action: str
    kwargs: dict[str, Any]
    reason: str
    confidence: float = 0.5


class AiriAgent(Protocol):
    def propose(self, *, state: Any) -> list[ActionProposal]: ...


__all__ = ["ActionProposal", "AiriAgent"]
""")

w("astra/airi/stub.py", """from __future__ import annotations

from typing import Any

from .contract import ActionProposal


class StubAiri:
    def propose(self, *, state: Any) -> list[ActionProposal]:
        ship = getattr(state, "ship", None)
        hull = getattr(ship, "hull", 100) if ship is not None else 100
        power = getattr(ship, "power", 100) if ship is not None else 100
        sector = getattr(ship, "sector", "Mostek") if ship is not None else "Mostek"
        last_seed = int(getattr(state, "last_seed", 0) or 0)

        out: list[ActionProposal] = []

        if hull <= 20 and sector != "Mostek":
            out.append(
                ActionProposal(
                    action="move",
                    kwargs={"sector": "Mostek"},
                    reason="Low hull -> retreat to Mostek.",
                    confidence=0.8,
                )
            )

        if power == 0:
            return out

        out.append(
            ActionProposal(
                action="tick",
                kwargs={"seed": last_seed or 123},
                reason="Advance one day (deterministic).",
                confidence=0.6,
            )
        )
        return out


__all__ = ["StubAiri"]
""")

w("astra/airi/__main__.py", """from __future__ import annotations

import argparse

from astra.game.actions import apply_action
from astra.game.logbook import append_command, append_events
from astra.game.storage import load_state, save_state

from .stub import StubAiri


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="astra.airi")
    p.add_argument("--profile", default="offline")
    p.add_argument("--write", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("propose")
    sp.add_argument("--apply", action="store_true")

    ns = p.parse_args(argv)
    profile = str(ns.profile)
    write = bool(ns.write)

    if ns.cmd != "propose":
        print("Use: python -m astra.airi propose [--apply] [--profile X] [--write]")
        return 1

    s0 = load_state(profile=profile)
    agent = StubAiri()
    props = agent.propose(state=s0)

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
    s1, txt, events = apply_action(s0, pr0.action, **pr0.kwargs)

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
""")

w("tests/test_airi_contract.py", """import subprocess
import sys

from astra.airi.stub import StubAiri
from astra.game.state import default_state


def test_stub_airi_proposes():
    s = default_state()
    props = StubAiri().propose(state=s)
    assert isinstance(props, list)


def test_airi_module_runs():
    r = subprocess.run(
        [sys.executable, "-m", "astra.airi", "propose", "--profile", "offline"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "AIRI PROPOSE" in r.stdout
""")

print("SPRINT 2O applied: AIRI contract v1 + stub + runner + tests.")