from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def make_latest_report_zip(*, profile: str) -> str | None:
    """Creates data/profiles/<profile>/report_latest.zip from data/errors/error_*.log.
    Returns zip path as string, or None if no errors exist.
    """
    root = Path.cwd()
    err_dir = root / "data" / "errors"
    logs = sorted(err_dir.glob("error_*.log"))
    if not logs:
        return None

    out_dir = root / "data" / "profiles" / profile
    out_dir.mkdir(parents=True, exist_ok=True)
    out_zip = out_dir / "report_latest.zip"

    with ZipFile(out_zip, "w", compression=ZIP_DEFLATED) as z:
        for p in logs[-10:]:
            z.write(p, arcname=f"errors/{p.name}")
        z.writestr(
            "README.txt",
            "ASTRA report\n- contains last error_*.log from data/errors\n",
        )

    return str(out_zip)
