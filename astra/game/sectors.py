from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class SectorDef:
    id: str
    name: str
    description: str = ""
    tags: tuple[str, ...] = ()


class SectorRegistry:
    def __init__(self, sectors: Iterable[SectorDef]) -> None:
        self._by_id = {s.id: s for s in sectors}

    def get(self, sector_id: str) -> SectorDef | None:
        return self._by_id.get(sector_id)

    def list(self) -> list[SectorDef]:
        return list(self._by_id.values())


DEFAULT_SECTORS = SectorRegistry(
    [
        SectorDef(id="Mostek", name="Mostek", description="Centrum dowodzenia.", tags=("core",)),
        SectorDef(id="AIRI", name="AIRI", description="Interfejs AIRI / rdzeń AI.", tags=("ai",)),
        SectorDef(id="Sektor A-1", name="Sektor A-1", description="Korytarze A-1.", tags=("field",)),
    ]
)
