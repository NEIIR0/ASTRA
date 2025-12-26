from __future__ import annotations

import argparse

from .doctor import run_doctor
from .game.engine import apply_external_event, tick_day
from .game.events import GameEvent
from .game.logbook import append_events
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


def _print_game_status(profile: str) -> None:
    s = load_state(profile=profile)
    qdefs = defs_by_id()
    print("GAME STATUS")
    print(f"- profile: {profile}")
    print(f"- day: {s.day}")
    print(f"- level: {s.player.level} (xp={s.player.xp})")
    print(f"- ship: hull={s.ship.hull} power={s.ship.power}")
    print(f"- last_seed: {s.last_seed}")
    print("- quests:")
    for q in s.quests:
        qd = qdefs.get(q.quest_id)
        title = qd.title if qd else q.quest_id
        target = qd.target_value if qd else 0
        print(f"  * {q.quest_id} :: {title} [{q.status}] {q.progress}/{target}")


def _run_game_tick(write: bool, seed: int | None, profile: str) -> int:
    state = load_state(profile=profile)
    use_seed = int(seed if seed is not None else (state.day + 1))
    new_state, events_text, events_json = tick_day(state, seed=use_seed)

    print("GAME TICK")
    print(f"- profile: {profile}")
    print(f"- seed: {use_seed}")
    for e in events_text:
        print(f"- {e}")

    if write:
        save_state(new_state, profile=profile)
        append_events(events_json, write=True, profile=profile)
        print(f"- saved: data/profiles/{profile}/game_state.json")
        print(f"- logbook: data/profiles/{profile}/logbook.jsonl")
    else:
        print("- not saved (SAFE default). Use: --write")
    return 0


def _quest_claim(quest_id: str, write: bool, profile: str) -> int:
    state = load_state(profile=profile)
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

    if not found or not claimable(found):
        print("! not claimable")
        return 2

    if not write:
        print("- SAFE: would mark claimed + grant XP")
        print("Use: python -m astra --profile <p> --write game quest claim <id>")
        return 0

    new_xp = state.player.xp + qd.reward_xp
    new_player = state.player.__class__(xp=new_xp, level=state.player.level)
    claimed = mark_claimed(found)

    new_state = state.__class__(
        schema_version=state.schema_version,
        day=state.day,
        ship=state.ship,
        player=new_player,
        achievements=state.achievements,
        quests=rest + [claimed],
        last_seed=state.last_seed,
    )

    save_state(new_state, profile=profile)
    append_events(
        [{"type": "quest_claimed", "quest_id": quest_id, "reward_xp": qd.reward_xp}],
        write=True,
        profile=profile,
    )
    print(f"- claimed: {quest_id}")
    print(f"- reward_xp: {qd.reward_xp} (xp={new_xp})")
    return 0


def _emit_hook(write: bool, profile: str, e: GameEvent) -> None:
    s = load_state(profile=profile)
    s2 = apply_external_event(s, e)
    if write:
        save_state(s2, profile=profile)
        append_events([e.to_json()], write=True, profile=profile)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="astra")
    p.add_argument("--once", choices=[m[0] for m in MENU])
    p.add_argument("--write", action="store_true")
    p.add_argument("--profile", default="default")

    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("doctor")

    p_game = sub.add_parser("game")
    sub_game = p_game.add_subparsers(dest="game_cmd")
    sub_game.add_parser("status")
    p_tick = sub_game.add_parser("tick")
    p_tick.add_argument("--seed", type=int)

    p_q = sub_game.add_parser("quest")
    sub_q = p_q.add_subparsers(dest="quest_cmd")
    sub_q.add_parser("list")
    p_claim = sub_q.add_parser("claim")
    p_claim.add_argument("quest_id")

    ns = p.parse_args(argv)
    profile = str(ns.profile)

    if ns.cmd == "doctor":
        rc = run_doctor()
        if rc == 0:
            _emit_hook(bool(ns.write), profile, GameEvent("doctor_ok", 1))
        return rc

    if ns.cmd == "game":
        if ns.game_cmd == "status":
            _print_game_status(profile)
            return 0
        if ns.game_cmd == "tick":
            return _run_game_tick(bool(ns.write), ns.seed, profile)
        if ns.game_cmd == "quest":
            if ns.quest_cmd == "list":
                _print_game_status(profile)
                return 0
            if ns.quest_cmd == "claim":
                return _quest_claim(str(ns.quest_id), bool(ns.write), profile)
        print("Use: python -m astra --profile <p> game status|tick|quest list|quest claim <id>")
        return 1

    if ns.once:
        if ns.once == "3":
            _emit_hook(bool(ns.write), profile, GameEvent("airi_status", 1))
        return dispatch(ns.once)

    while True:
        print("=== ASTRA HUB (Sprint 2D) ===")
        for key, label in MENU:
            print(f"[{key}] {label}")
        choice = input("> ").strip()
        code = dispatch(choice)
        if choice == "0":
            return code
