import subprocess
import sys
from pathlib import Path


def test_astra_report_zip_no_errors():
    # czyścimy stare błędy z poprzednich padów testów
    err_dir = Path("data") / "errors"
    if err_dir.exists():
        for p in err_dir.glob("error_*.log"):
            p.unlink(missing_ok=True)

    r = subprocess.run(
        [sys.executable, "-m", "astra", "report", "--zip", "--profile", "offline"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "Brak error_" in r.stdout
