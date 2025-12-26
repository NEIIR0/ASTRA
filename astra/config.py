from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    profile: str = "offline"
    log_enabled: bool = False
    root: Path = Path(".")


def config_path(root: Path | None = None, *, profile: str = "offline") -> Path:
    r = Path.cwd() if root is None else Path(root)
    return r / "data" / "profiles" / str(profile) / "config.json"


def load_config(root: Path | None = None, *, profile: str = "offline") -> Config:
    # Backward compatible: may be called as load_config() with no args.
    r = Path.cwd() if root is None else Path(root)
    p = config_path(r, profile=profile)
    if not p.exists():
        return Config(profile=str(profile), log_enabled=False, root=r)

    try:
        obj: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return Config(profile=str(profile), log_enabled=False, root=r)

    return Config(
        profile=str(obj.get("profile", profile)),
        log_enabled=bool(obj.get("log_enabled", False)),
        root=r,
    )


def save_config(cfg: Config) -> Path:
    p = config_path(cfg.root, profile=cfg.profile)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(
            {"profile": cfg.profile, "log_enabled": cfg.log_enabled},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return p


__all__ = ["Config", "config_path", "load_config", "save_config"]
