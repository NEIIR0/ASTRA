from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BalanceConfig:
    xp_per_tick: int = 5
    anomaly_hull_loss: int = 1
    anomaly_power_loss: int = 1


def _balance_path(*, profile: str) -> Path:
    return Path("data") / "profiles" / profile / "balance.json"


def load_balance(*, profile: str) -> BalanceConfig:
    p = _balance_path(profile=profile)
    if not p.exists():
        return BalanceConfig()
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return BalanceConfig()

    if not isinstance(obj, dict):
        return BalanceConfig()

    return BalanceConfig(
        xp_per_tick=int(obj.get("xp_per_tick", 5)),
        anomaly_hull_loss=int(obj.get("anomaly_hull_loss", 1)),
        anomaly_power_loss=int(obj.get("anomaly_power_loss", 1)),
    )


def save_balance(*, profile: str, cfg: BalanceConfig) -> None:
    p = _balance_path(profile=profile)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(
            {
                "xp_per_tick": cfg.xp_per_tick,
                "anomaly_hull_loss": cfg.anomaly_hull_loss,
                "anomaly_power_loss": cfg.anomaly_power_loss,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


__all__ = ["BalanceConfig", "load_balance", "save_balance"]
