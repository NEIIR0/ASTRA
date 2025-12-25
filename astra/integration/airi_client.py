from dataclasses import dataclass
from typing import Literal

Decision = Literal["SAFE", "WRITE", "EXEC", "DENY"]


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reason: str


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    output: str


class AiriClient:
    def status(self) -> ToolResult:
        from airi import __version__

        return ToolResult(True, f"AIRI online (version {__version__})")

    def decide(self, action: str) -> PolicyDecision:
        return PolicyDecision("SAFE", f"default SAFE for action={action}")
