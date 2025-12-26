from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sector:
    name: str
    title: str = ""
    desc: str = ""
    actions: tuple[str, ...] = ("tick", "move")  # do rozbudowy


DEFAULT_SECTORS: dict[str, Sector] = {
    "Mostek": Sector(
        name="Mostek",
        title="Mostek",
        desc="Centrum dowodzenia statku.",
        actions=("tick", "move"),
    ),
    "AIRI": Sector(
        name="AIRI",
        title="Moduł AIRI",
        desc="Interfejs do AIRI (kontrakt v1).",
        actions=("tick", "move"),
    ),
    "Sektor A-1": Sector(
        name="Sektor A-1",
        title="Sektor A-1",
        desc="Strefa testowa.",
        actions=("tick", "move"),
    ),
}


def sector_exists(name: str) -> bool:
    return str(name) in DEFAULT_SECTORS


__all__ = ["Sector", "DEFAULT_SECTORS", "sector_exists"]
