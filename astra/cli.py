from __future__ import annotations

import argparse

from .doctor import run_doctor
from .game.logbook import append_events
from .game.loop import tick_day
from .game.quests import claimable, defs_by_id, mark_claimed
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


def _print_game_status() -> None:
    s = load_state()
    qdefs = defs_by_id()
    print("GAME STATUS")
    print(f"- day: {s.day}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")
    print(f"- ship.power: {s.ship.power}")
    print("- quests:")
    for q in s.quests:
        qd = qdefs.get(q.quest_id)
        title = qd.title if qd else q.quest_id
        target = qd.target_value if qd else 0
        print(f"  * {q.quest_id} :: {title} [{q.status}] {q.progress}/{target}")


def _run_game_tick(write: bool) -> int:
    state = load_state()
    new_state, events_text, events_json = tick_day(state)

    print("GAME TICK")
    for e in events_text:
        print(f"- {e}")

    if write:
        save_state(new_state)
        append_events(events_json, write=True)
        print("- saved: data/game_state.json")
        print("- logbook: data/logbook.jsonl")
    else:
        print("- not saved (SAFE default). Use: --write")

    return 0


def _quest_list() -> int:
    _print_game_status()
    print("Use: python -m astra game quest claim <quest_id> [--write]")
    return 0


def _quest_claim(quest_id: str, write: bool) -> int:
    state = load_state()
    qdefs = defs_by_id()
    qd = qdefs.get(quest_id)
    if not qd:
        print(f"! unknown quest_id: {quest_id}")
        return 2

    found = None
    rest = []
    for q in state.quests:
        if q.quest_id == quest_id:
            found = q
        else:
            rest.append(q)

    if not found:
        print("! quest not present in state")
        return 2

    if not claimable(found):
        print(
            f"! not claimable: status={found.status}, progress={found.progress}/{qd.target_value}"
        )
        return 2

    if not write:
        print("- SAFE: claim would grant XP and mark quest as claimed")
        print("Use: python -m astra game quest claim <quest_id> --write")
        return 0

    # Apply reward
    new_xp = state.player.xp + qd.reward_xp
    new_level = state.player.level
    # (level is updated by tick; reward is additive and cheap)
    new_player = state.player.__class__(xp=new_xp, level=new_level)

    claimed = mark_claimed(found)
    new_state = state.__class__(
        schema_version=state.schema_version,
        day=state.day,
        ship=state.ship,
        player=new_player,
        achievements=state.achievements,
        quests=rest + [claimed],
    )

    save_state(new_state)
    append_events(
        [{"type": "quest_claimed", "quest_id": quest_id, "reward_xp": qd.reward_xp}], write=True
    )
    print(f"- claimed: {quest_id}")
    print(f"- reward_xp: {qd.reward_xp} (xp={new_xp})")
    print("- saved: data/game_state.json")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="astra")
    p.add_argument("--once", choices=[m[0] for m in MENU])

    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("doctor")

    p_game = sub.add_parser("game")
    p_game.add_argument("--write", action="store_true")
    sub_game = p_game.add_subparsers(dest="game_cmd")

    sub_game.add_parser("status")
    sub_game.add_parser("tick")

    p_q = sub_game.add_parser("quest")
    sub_q = p_q.add_subparsers(dest="quest_cmd")
    sub_q.add_parser("list")
    p_claim = sub_q.add_parser("claim")
    p_claim.add_argument("quest_id")

    ns = p.parse_args(argv)

    if ns.cmd == "doctor":
        rc = run_doctor()
        # quest hook: doctor_ok
        if rc == 0:
            append_events(
                [{"type": "doctor_ok", "amount": 1}], write=bool(getattr(ns, "write", False))
            )
        return rc

    if ns.cmd == "game":
        if ns.game_cmd == "status":
            _print_game_status()
            return 0
        if ns.game_cmd == "tick":
            return _run_game_tick(bool(ns.write))
        if ns.game_cmd == "quest":
            if ns.quest_cmd == "list":
                return _quest_list()
            if ns.quest_cmd == "claim":
                return _quest_claim(str(ns.quest_id), bool(ns.write))
        print("Use: python -m astra game status|tick|quest list|quest claim <id> [--write]")
        return 1

    if ns.once:
        # hook for AIRI status quest: option 3 is AIRI screen
        if ns.once == "3":
            append_events([{"type": "airi_status", "amount": 1}], write=False)
        return dispatch(ns.once)

    while True:
        print("=== ASTRA HUB (Sprint 2B) ===")
        for key, label in MENU:
            print(f"[{key}] {label}")
        choice = input("> ").strip()
        code = dispatch(choice)
        if choice == "0":
            return code
