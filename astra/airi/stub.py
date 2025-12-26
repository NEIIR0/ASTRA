from __future__ import annotations

from typing import Any

from .contract import ActionProposal


class StubAiri:
    def propose(self, *, state: Any) -> list[ActionProposal]:
        ship = getattr(state, "ship", None)
        hull = getattr(ship, "hull", 100) if ship is not None else 100
        power = getattr(ship, "power", 100) if ship is not None else 100
        sector = getattr(ship, "sector", "Mostek") if ship is not None else "Mostek"
        last_seed = int(getattr(state, "last_seed", 0) or 0)

        out: list[ActionProposal] = []

        if hull <= 20 and sector != "Mostek":
            out.append(
                ActionProposal(
                    action="move",
                    kwargs={"sector": "Mostek"},
                    reason="Low hull -> retreat to Mostek.",
                    confidence=0.8,
                )
            )

        if power == 0:
            return out

        out.append(
            ActionProposal(
                action="tick",
                kwargs={"seed": last_seed or 123},
                reason="Advance one day (deterministic).",
                confidence=0.6,
            )
        )
        return out


__all__ = ["StubAiri"]
