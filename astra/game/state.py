from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ShipState:
    sector: str = "Mostek"
    hull: int = 100
    power: int = 100


@dataclass(frozen=True)
class PlayerState:
    xp: int = 0
    level: int = 1


@dataclass(frozen=True)
class GameState:
    schema_version: int = SCHEMA_VERSION
    day: int = 0
    ship: ShipState = field(default_factory=ShipState)
    player: PlayerState = field(default_factory=PlayerState)
    achievements: list[str] = field(default_factory=list)
    active_quests: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "day": self.day,
            "ship": {"sector": self.ship.sector, "hull": self.ship.hull, "power": self.ship.power},
            "player": {"xp": self.player.xp, "level": self.player.level},
            "achievements": list(self.achievements),
            "active_quests": list(self.active_quests),
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> GameState:
        sv = int(d.get("schema_version", 0))
        if sv != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version={sv} (expected {SCHEMA_VERSION})")

        ship_d = d.get("ship", {}) or {}
        player_d = d.get("player", {}) or {}

        return GameState(
            schema_version=SCHEMA_VERSION,
            day=int(d.get("day", 0)),
            ship=ShipState(
                sector=str(ship_d.get("sector", "Mostek")),
                hull=int(ship_d.get("hull", 100)),
                power=int(ship_d.get("power", 100)),
            ),
            player=PlayerState(
                xp=int(player_d.get("xp", 0)),
                level=int(player_d.get("level", 1)),
            ),
            achievements=[str(x) for x in (d.get("achievements", []) or [])],
            active_quests=[str(x) for x in (d.get("active_quests", []) or [])],
        )


def default_state() -> GameState:
    return GameState(active_quests=["Uruchom ASTRA Doctor", "Sprawdź status AIRI na mostku"])
