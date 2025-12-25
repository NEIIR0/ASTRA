import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AstraConfig:
    profile: str = "offline"
    log_enabled: bool = False


def load_config(root: Path) -> AstraConfig:
    p = root / "config" / "astra.toml"
    if not p.exists():
        return AstraConfig()
    data = tomllib.loads(p.read_text("utf-8"))
    return AstraConfig(
        profile=data.get("profile", "offline"), log_enabled=bool(data.get("log_enabled", False))
    )
