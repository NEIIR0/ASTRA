import sys
from pathlib import Path


def run_doctor() -> int:
    root = Path.cwd()
    print("AIRI DOCTOR")
    print(f"- cwd: {root}")
    print(f"- python: {sys.version.split()[0]}")
    print(f"- prefix: {sys.prefix}")

    venv_ps1 = root / ".venv" / "Scripts" / "Activate.ps1"
    print("- .venv: OK" if venv_ps1.exists() else "! WARN: brak .venv")
    print("- policy: SAFE default")
    return 0
