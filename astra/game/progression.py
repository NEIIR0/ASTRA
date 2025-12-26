from __future__ import annotations


def level_from_xp(xp: int) -> int:
    # Prosta krzywa na start; później podmienimy na tabelę/progi w configu.
    if xp < 10:
        return 1
    if xp < 25:
        return 2
    if xp < 45:
        return 3
    return 4
