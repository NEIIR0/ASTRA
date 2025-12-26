from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ShipState:
    sector: str = "Mostek"
    hull: int = 100
    power: int = 100

    def to_dict(self) -> dict[str, Any]:
        return {"sector": self.sector, "hull": int(self.hull), "power": int(self.power)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ShipState:
        return cls(
            sector=str(d.get("sector", "Mostek")),
            hull=int(d.get("hull", 100)),
            power=int(d.get("power", 100)),
        )


@dataclass(frozen=True)
class PlayerState:
    xp: int = 0
    level: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {"xp": int(self.xp), "level": int(self.level)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PlayerState:
        return cls(xp=int(d.get("xp", 0)), level=int(d.get("level", 1)))


@dataclass(frozen=True)
class QuestState:
    quest_id: str
    status: str = "active"
    progress: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"quest_id": self.quest_id, "status": self.status, "progress": int(self.progress)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> QuestState:
        return cls(
            quest_id=str(d.get("quest_id", "")),
            status=str(d.get("status", "active")),
            progress=int(d.get("progress", 0)),
        )


def _default_quests() -> list[QuestState]:
    return [
        QuestState("q_doctor_once", "active", 0),
        QuestState("q_ticks_3", "active", 0),
        QuestState("q_airi_status", "active", 0),
    ]


@dataclass(frozen=True)
class GameState:
    schema_version: int = 3
    day: int = 0
    ship: ShipState = field(default_factory=ShipState)
    player: PlayerState = field(default_factory=PlayerState)
    achievements: list[str] = field(default_factory=list)
    quests: list[Any] = field(default_factory=list)  # QuestState OR dict (back-compat)
    last_seed: int = 0

    def to_dict(self) -> dict[str, Any]:
        q_out: list[dict[str, Any]] = []
        for q in self.quests:
            if isinstance(q, dict):
                q_out.append(
                    {
                        "quest_id": str(q.get("quest_id", "")),
                        "status": str(q.get("status", "")),
                        "progress": int(q.get("progress", 0)),
                    }
                )
            elif hasattr(q, "to_dict"):
                q_out.append(q.to_dict())
        return {
            "schema_version": int(self.schema_version),
            "day": int(self.day),
            "ship": self.ship.to_dict(),
            "player": self.player.to_dict(),
            "achievements": list(self.achievements),
            "quests": q_out,
            "last_seed": int(self.last_seed),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GameState:
        ship_d = d.get("ship", {})
        player_d = d.get("player", {})

        ship = ShipState.from_dict(ship_d) if isinstance(ship_d, dict) else ShipState()
        player = PlayerState.from_dict(player_d) if isinstance(player_d, dict) else PlayerState()

        ach = d.get("achievements", [])
        achievements = [str(x) for x in ach] if isinstance(ach, list) else []

        # parse quests (support dict/list), then ENSURE required defaults exist
        quests_in = d.get("quests", [])
        parsed: list[QuestState] = []
        if isinstance(quests_in, list):
            for q in quests_in:
                if isinstance(q, QuestState):
                    parsed.append(q)
                elif isinstance(q, dict):
                    qs = QuestState.from_dict(q)
                    if qs.quest_id:
                        parsed.append(qs)

        defaults = _default_quests()
        by_id: dict[str, QuestState] = {q.quest_id: q for q in defaults}
        extras: list[QuestState] = []

        for q in parsed:
            if q.quest_id in by_id:
                by_id[q.quest_id] = q
            else:
                extras.append(q)

        quests: list[QuestState] = list(by_id.values()) + extras

        return cls(
            schema_version=int(d.get("schema_version", 3)),
            day=int(d.get("day", 0)),
            ship=ship,
            player=player,
            achievements=achievements,
            quests=quests,
            last_seed=int(d.get("last_seed", 0)),
        )


def default_state() -> GameState:
    return GameState(
        schema_version=3,
        day=0,
        ship=ShipState(sector="Mostek", hull=100, power=100),
        player=PlayerState(xp=0, level=1),
        achievements=[],
        quests=_default_quests(),
        last_seed=0,
    )


__all__ = ["ShipState", "PlayerState", "QuestState", "GameState", "default_state"]
