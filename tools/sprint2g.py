from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def w(path: str, text: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


# --- router: profile required
w(
    "astra/router.py",
    """from __future__ import annotations

from .screens import airi, bridge, game, lore, settings


def dispatch(key: str, *, profile: str) -> int:
    if key == "1":
        settings.run(profile=profile)
        return 0
    if key == "2":
        bridge.run(profile=profile)
        return 0
    if key == "3":
        airi.run(profile=profile)
        return 0
    if key == "4":
        lore.run(profile=profile)
        return 0
    if key == "5":
        game.run(profile=profile)
        return 0
    if key == "0":
        print("Do zobaczenia.")
        return 0

    print("Nieznana opcja.")
    return 1
""",
)

# --- screens: unify signature run(profile=...)
w(
    "astra/screens/lore.py",
    """from __future__ import annotations


def run(*, profile: str) -> None:
    _ = profile
    print("UNIWERSUM / CANON")
    print("ASTRA: statek kolonizacyjny; anomalia po czarnej dziurze uszkodziła okręt.")
    print("AIRI: cyfrowe życie (JA+cele+pamięć+refleksja+inicjatywa) bez roszczeń świadomości.")
""",
)

w(
    "astra/screens/settings.py",
    """from __future__ import annotations

from ..config import load_config


def run(*, profile: str) -> None:
    cfg = load_config()
    print("USTAWIENIA")
    print(f"- profile(run): {profile}")
    print(f"- config.profile: {cfg.profile}")
    print(f"- config.log_enabled: {cfg.log_enabled}")
""",
)

w(
    "astra/screens/bridge.py",
    """from __future__ import annotations

from ..integration.airi_client import AiriClient


def run(*, profile: str) -> None:
    _ = profile
    c = AiriClient()
    s = c.status()
    print("AIRI (bridge)")
    print(f"- AIRI online (version {s.version})")
    print(f"- policy: {s.policy} (default SAFE for action=bridge_status)")
    print("- mode: stub")
""",
)

w(
    "astra/screens/airi.py",
    """from __future__ import annotations


def run(*, profile: str) -> None:
    _ = profile
    print("AIRI")
    print("- entry: stub (Sprint 2G)")
""",
)

# game screen might already exist; keep signature consistent
w(
    "astra/screens/game.py",
    """from __future__ import annotations

from ..game.storage import load_state


def run(*, profile: str) -> None:
    s = load_state(profile=profile)
    print("TRYB GRY")
    print(f"- profile(run): {profile}")
    print(f"- day: {s.day}")
    print(f"- sector: {s.ship.sector}")
    print(f"- hull: {s.ship.hull}")
    print(f"- power: {s.ship.power}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")
    print(f"- last_seed: {getattr(s, 'last_seed', 0)}")
""",
)

# --- CLI: accept --profile and --write anywhere (also after subcommand)
w(
    "astra/cli.py",
    """from __future__ import annotations

import argparse

from .doctor import run_doctor
from .game.engine import tick_day
from .game.logbook import append_events
from .game.storage import load_state, save_state
from .report import make_latest_report_zip
from .router import dispatch


MENU = [
    ("1", "Ustawienia"),
    ("2", "Udaj się na mostek"),
    ("3", "Udaj się do AIRI"),
    ("4", "Uniwersum"),
    ("5", "Tryb gry"),
    ("0", "Wyjście"),
]


def _extract_globals(argv: list[str]) -> tuple[str, bool, str | None, list[str]]:
    profile = "offline"
    write = False
    once: str | None = None
    out: list[str] = []

    i = 0
    while i < len(argv):
        a = argv[i]

        if a in ("--profile",):
            if i + 1 >= len(argv):
                raise SystemExit("ERR: --profile requires value")
            profile = str(argv[i + 1])
            i += 2
            continue

        if a.startswith("--profile="):
            profile = a.split("=", 1)[1]
            i += 1
            continue

        if a == "--write":
            write = True
            i += 1
            continue

        if a == "--once":
            if i + 1 >= len(argv):
                raise SystemExit("ERR: --once requires value")
            once = str(argv[i + 1])
            i += 2
            continue

        if a.startswith("--once="):
            once = a.split("=", 1)[1]
            i += 1
            continue

        out.append(a)
        i += 1

    return profile, write, once, out


def _run_game_status(*, profile: str) -> int:
    s = load_state(profile=profile)
    print("GAME STATUS")
    print(f"- profile: {profile}")
    print(f"- day: {s.day}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")
    print(f"- ship: hull={s.ship.hull} power={s.ship.power}")
    print(f"- last_seed: {getattr(s, 'last_seed', 0)}")
    if getattr(s, "quests", []):
        print("- quests:")
        for q in s.quests:
            print(f"  * {q.quest_id} [{q.status}] {q.progress}")
    return 0


def _run_game_tick(*, profile: str, write: bool, seed: int | None) -> int:
    s0 = load_state(profile=profile)
    s1, _txt, events = tick_day(s0, seed=seed)

    print("GAME TICK")
    print(f"- profile: {profile}")
    print(f"- seed: {seed if seed is not None else getattr(s0, 'last_seed', 0)}")
    for line in _txt:
        print(f"- {line}")
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


def main(argv: list[str] | None = None) -> int:
    raw = list(argv) if argv is not None else None
    if raw is None:
        import sys

        raw = sys.argv[1:]

    profile, write, once, rest = _extract_globals(raw)

    p = argparse.ArgumentParser(prog="astra")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("doctor")

    p_report = sub.add_parser("report")
    p_report.add_argument("--zip", action="store_true")

    p_game = sub.add_parser("game")
    sub_game = p_game.add_subparsers(dest="game_cmd")
    sub_game.add_parser("status")
    p_tick = sub_game.add_parser("tick")
    p_tick.add_argument("--seed", type=int)

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
        print("Use: python -m astra game (status|tick) [--seed N] [--write] [--profile X]")
        return 1

    if once is not None:
        return dispatch(once, profile=profile)

    while True:
        print("=== ASTRA HUB ===")
        for key, label in MENU:
            print(f"[{key}] {label}")
        choice = input("> ").strip()
        code = dispatch(choice, profile=profile)
        if choice == "0":
            return code
""",
)

# --- tests: make them profile-safe + test profile-after-subcommand
w(
    "tests/test_cli.py",
    """import subprocess
import sys


def test_astra_once_lore():
    r = subprocess.run(
        [sys.executable, "-m", "astra", "--once", "4", "--profile", "offline"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "UNIWERSUM" in r.stdout


def test_astra_doctor():
    r = subprocess.run(
        [sys.executable, "-m", "astra", "doctor"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "ASTRA DOCTOR" in r.stdout
""",
)

w(
    "tests/test_game.py",
    """import subprocess
import sys


def test_astra_once_game_screen():
    r = subprocess.run(
        [sys.executable, "-m", "astra", "--once", "5", "--profile", "offline"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "TRYB GRY" in r.stdout


def test_astra_game_tick_profile_after_subcommand():
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "astra",
            "game",
            "tick",
            "--seed",
            "123",
            "--profile",
            "offline",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "GAME TICK" in r.stdout
""",
)

print("SPRINT 2G applied: profile propagation + CLI order-agnostic globals.")
