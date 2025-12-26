from __future__ import annotations

import traceback
import zipfile
from datetime import datetime
from pathlib import Path

ERROR_DIR = Path("data") / "errors"
ERROR_DIR.mkdir(parents=True, exist_ok=True)


def _next_error_file() -> Path:
    logs = sorted(ERROR_DIR.glob("error_*.log"))
    if not logs:
        return ERROR_DIR / "error_0001.log"
    last = int(logs[-1].stem.split("_")[-1])
    return ERROR_DIR / f"error_{last + 1:04d}.log"


def log_exception(exc_type, exc, tb) -> None:
    path = _next_error_file()
    err_no = path.stem.split("_")[-1]
    msg = f"{exc_type.__name__}: {exc}"

    with path.open("w", encoding="utf-8") as f:
        f.write("ASTRA ERROR LOG\n")
        f.write(f"Time: {datetime.now().isoformat()}\n")
        f.write(f"ErrorNo: {err_no}\n")
        f.write(f"Summary: {msg}\n")
        f.write(f"File: {path}\n\n")
        traceback.print_exception(exc_type, exc, tb, file=f)

    try:
        print(f"BLAD nr {err_no} — {msg}")
        print(f"Log: {path}")
    except Exception:
        pass


def make_latest_report_zip(profile: str) -> Path | None:
    logs = sorted(ERROR_DIR.glob("error_*.log"))
    if not logs:
        return None
    latest = logs[-1]
    out = Path("data") / "profiles" / profile / "report_latest.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(latest, arcname=latest.name)
    return out
