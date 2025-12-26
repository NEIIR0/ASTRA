from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

QuestStatus = Literal["active", "completed", "claimed"]


@dataclass(frozen=True)
class QuestDef:
    quest_id: str
    title: str
    description: str
    target_type: str
    target_value: int
    reward_xp: int


@dataclass(frozen=True)
class QuestProgress:
    quest_id: str
    status: QuestStatus = "active"
    progress: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"quest_id": self.quest_id, "status": self.status, "progress": self.progress}

    @staticmethod
    def from_dict(d: dict[str, Any]) -> QuestProgress:
        return QuestProgress(
            quest_id=str(d.get("quest_id", "")),
            status=str(d.get("status", "active")),  # type: ignore[arg-type]
            progress=int(d.get("progress", 0)),
        )


def catalog() -> list[QuestDef]:
    # Minimalny, ale „prawdziwy” katalog. Potem przeniesiemy do configu/plugina.
    return [
        QuestDef(
            quest_id="q_doctor_once",
            title="Uruchom ASTRA Doctor",
            description="Wykonaj: python -m astra doctor",
            target_type="doctor_ok",
            target_value=1,
            reward_xp=10,
        ),
        QuestDef(
            quest_id="q_ticks_3",
            title="Pierwsze 3 dni",
            description="Zrób 3 ticki (days).",
            target_type="tick_done",
            target_value=3,
            reward_xp=15,
        ),
        QuestDef(
            quest_id="q_airi_status",
            title="Sprawdź status AIRI",
            description="Wykonaj: python -m astra --once 3",
            target_type="airi_status",
            target_value=1,
            reward_xp=5,
        ),
    ]


def ensure_progress(existing: list[QuestProgress]) -> list[QuestProgress]:
    by_id = {q.quest_id: q for q in existing if q.quest_id}
    out: list[QuestProgress] = []
    for q in catalog():
        out.append(by_id.get(q.quest_id, QuestProgress(q.quest_id)))
    return out


def apply_event(
    progress: QuestProgress, qdef: QuestDef, event_type: str, amount: int
) -> QuestProgress:
    if progress.status != "active":
        return progress
    if event_type != qdef.target_type:
        return progress

    new_val = min(qdef.target_value, progress.progress + amount)
    status: QuestStatus = "completed" if new_val >= qdef.target_value else "active"
    return QuestProgress(quest_id=progress.quest_id, status=status, progress=new_val)


def claimable(q: QuestProgress) -> bool:
    return q.status == "completed"


def mark_claimed(q: QuestProgress) -> QuestProgress:
    return QuestProgress(quest_id=q.quest_id, status="claimed", progress=q.progress)


def defs_by_id() -> dict[str, QuestDef]:
    return {q.quest_id: q for q in catalog()}
