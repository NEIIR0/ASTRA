from __future__ import annotations

from dataclasses import replace
from typing import Any

from .engine import tick_day
from .events import EventBus
from .policy import check_action_allowed
from .result import ActionError, ActionResult, fail, ok
from .rules import apply_rules
from .validate import validate_move, validate_state, validate_tick


def reduce(state: Any, action: str, **kwargs: Any) -> ActionResult:
    bus = EventBus()

    st_errs = validate_state(state)
    if st_errs:
        return fail(state, errors=st_errs, text=["ERROR: state validation failed."])

    dec = check_action_allowed(state=state, action=action, kwargs=kwargs, bus=bus)
    if not dec.ok:
        return fail(
            state,
            errors=[ActionError(code="policy_blocked", message=dec.reason, field="action")],
            text=[f"ERROR: policy blocked ({dec.reason})."],
            events=bus.drain(),
        )

    if action == "tick":
        seed = kwargs.get("seed")
        v = validate_tick(seed=seed)
        if v:
            return fail(
                state,
                errors=v,
                text=["ERROR: tick validation failed."],
                events=bus.drain(),
            )

        s1, txt, events = tick_day(state, seed=seed)
        s2, rtxt, rev = apply_rules(s1)
        return ok(s2, text=list(txt) + list(rtxt), events=events + rev + bus.drain())

    if action == "move":
        sector = str(kwargs.get("sector", ""))
        v = validate_move(sector=sector)
        if v:
            return fail(
                state,
                errors=v,
                text=["ERROR: move validation failed."],
                events=bus.drain(),
            )

        ship0 = state.ship
        # klucz: zachowujemy typ ShipState (nie dict)
        s1 = replace(state, ship=replace(ship0, sector=sector))

        txt = [f"SECTOR MOVE: {ship0.sector} -> {sector}"]
        events = [{"type": "sector_moved", "sector": sector}]

        s2, rtxt, rev = apply_rules(s1)
        return ok(
            s2,
            text=txt + list(rtxt),
            events=events + rev + bus.drain(),
        )

    return fail(
        state,
        errors=[ActionError(code="unknown_action", message=f"Unknown action: {action}", field="action")],
        text=["ERROR: unknown action."],
        events=bus.drain(),
    )
