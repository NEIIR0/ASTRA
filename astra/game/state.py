from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .quests import QuestProgress, ensure_progress

SCHEMA_VERSION = 2


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
    quests: list[QuestProgress] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "day": self.day,
            "ship": {"sector": self.ship.sector, "hull": self.ship.hull, "power": self.ship.power},
            "player": {"xp": self.player.xp, "level": self.player.level},
            "achievements": list(self.achievements),
            "quests": [q.to_dict() for q in self.quests],
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> GameState:
        sv = int(d.get("schema_version", 0))

        ship_d = d.get("ship", {}) or {}
        player_d = d.get("player", {}) or {}

        base = GameState(
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
            quests=[],
        )

        if sv == 2:
            raw = d.get("quests", []) or []
            quests = [QuestProgress.from_dict(x) for x in raw if isinstance(x, dict)]
            return GameState(
                schema_version=SCHEMA_VERSION,
                day=base.day,
                ship=base.ship,
                player=base.player,
                achievements=base.achievements,
                quests=ensure_progress(quests),
            )

        if sv == 1:
            # migracja: stare active_quests(list[str]) -> nowe questy z katalogu
            return GameState(
                schema_version=SCHEMA_VERSION,
                day=base.day,
                ship=base.ship,
                player=base.player,
                achievements=base.achievements,
                quests=ensure_progress([]),
            )

        raise ValueError(f"Unsupported schema_version={sv} (expected 1 or 2)")


def default_state() -> GameState:
    return GameState(quests=ensure_progress([]))
