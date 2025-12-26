from __future__ import annotations

from dataclasses import replace

from .achievements import check_achievements
from .progression import level_from_xp
from .state import GameState, PlayerState, ShipState


def tick_day(state: GameState) -> tuple[GameState, list[str]]:
    # Deterministyczny tick (dobry do testów). Losowość dodamy później kontrolowana seedem.
    events: list[str] = [f"Dzień {state.day} -> {state.day + 1}"]

    new_day = state.day + 1
    new_power = max(0, state.ship.power - 1)
    new_ship = ShipState(sector=state.ship.sector, hull=state.ship.hull, power=new_power)

    gained_xp = 5
    new_xp = state.player.xp + gained_xp
    new_level = level_from_xp(new_xp)
    new_player = PlayerState(xp=new_xp, level=new_level)
    events.append(f"+XP {gained_xp} (xp={new_xp}, lvl={new_level})")

    temp = replace(state, day=new_day, ship=new_ship, player=new_player)
    newly = check_achievements(temp)
    if newly:
        events.extend([f"ACHIEVEMENT: {x}" for x in newly])

    final = replace(temp, achievements=list(temp.achievements) + newly)
    return final, events
