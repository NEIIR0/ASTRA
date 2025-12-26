from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    profile: str = "offline"
    log_enabled: bool = False


def _root(root: Path | None) -> Path:
    return Path.cwd() if root is None else Path(root)


def config_path(profile: str, *, root: Path | None = None) -> Path:
    r = _root(root)
    return r / "data" / "profiles" / profile / "config.json"


def load_config(root: Path | None = None, profile: str = "offline") -> Config:
    p = config_path(profile, root=root)
    if not p.exists():
        return Config(profile=profile, log_enabled=False)
    d = json.loads(p.read_text("utf-8"))
    return Config(
        profile=str(d.get("profile", profile)),
        log_enabled=bool(d.get("log_enabled", False)),
    )


def save_config(cfg: Config, *, root: Path | None = None) -> Path:
    p = config_path(cfg.profile, root=root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(asdict(cfg), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return p
