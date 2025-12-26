from __future__ import annotations

from .state import GameState


def check_achievements(state: GameState) -> list[str]:
    unlocked: list[str] = []
    if state.day >= 1 and "Pierwszy dzień" not in state.achievements:
        unlocked.append("Pierwszy dzień")
    if state.player.level >= 2 and "Awans: Poziom 2" not in state.achievements:
        unlocked.append("Awans: Poziom 2")
    return unlocked
