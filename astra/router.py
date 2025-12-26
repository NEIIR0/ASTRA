from __future__ import annotations

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
