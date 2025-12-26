from __future__ import annotations

from .screens import airi, bridge, game, lore, settings


def dispatch(key: str) -> int:
    if key == "1":
        settings.run()
        return 0
    if key == "2":
        bridge.run()
        return 0
    if key == "3":
        airi.run()
        return 0
    if key == "4":
        lore.run()
        return 0
    if key == "5":
        game.run()
        return 0
    if key == "0":
        print("Do zobaczenia.")
        return 0

    print("Nieznana opcja.")
    return 1
