from __future__ import annotations

from pathlib import Path

V = "0.0.15"  # ASTRA v0.01.5


def w(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")


# Version single-source
w(Path("astra_common/__init__.py"), f'__version__ = "{V}"\n')
w(Path("airi/__init__.py"), "from astra_common import __version__\n")
w(Path("astra/__init__.py"), "from astra_common import __version__\n")

# Build + editable install
w(
    Path("pyproject.toml"),
    f'''[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "astra-airi"
version = "{V}"
requires-python = ">=3.12"
description = "ASTRA(HUB)+AIRI(agent) monorepo, local-first."
readme = "README.md"

[tool.setuptools.packages.find]
include = ["airi","astra","astra_common"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E","F","I","UP"]
''',
)

# Config loader
w(
    Path("astra/config.py"),
    """import tomllib
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
    return AstraConfig(profile=data.get("profile","offline"), log_enabled=bool(data.get("log_enabled",False)))
""",
)

# Logging (opt-in)
w(
    Path("astra/logging_setup.py"),
    """import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(root: Path, enabled: bool) -> logging.Logger:
    log = logging.getLogger("astra")
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    if not enabled:
        return log
    (root/"logs").mkdir(exist_ok=True)
    h = RotatingFileHandler(root/"logs"/"astra.log", maxBytes=512_000, backupCount=3, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    h.setFormatter(fmt)
    log.addHandler(h)
    return log
""",
)

# AIRI interface contract (stub)
w(
    Path("astra/integration/airi_client.py"),
    """from dataclasses import dataclass
from typing import Literal

Decision = Literal["SAFE","WRITE","EXEC","DENY"]

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
""",
)

w(
    Path("astra/integration/airi_bridge.py"),
    """from .airi_client import AiriClient

def airi_status() -> str:
    c = AiriClient()
    s = c.status()
    p = c.decide("bridge_status")
    return f"- {s.output}\\n- policy: {p.decision} ({p.reason})\\n- mode: stub"
""",
)

# Screens + router
w(
    Path("astra/screens/lore.py"),
    """def run() -> None:
    print("UNIWERSUM / CANON (Sprint 1.5)")
    print("ASTRA: statek kolonizacyjny; anomalia po czarnej dziurze uszkodziła okręt.")
    print("AIRI: cyfrowe życie (JA+cele+pamięć+refleksja+inicjatywa) bez roszczeń świadomości.")
""",
)
w(
    Path("astra/screens/airi.py"),
    """from ..integration.airi_bridge import airi_status
def run() -> None:
    print("AIRI (bridge)")
    print(airi_status())
""",
)
w(
    Path("astra/screens/settings.py"),
    """def run() -> None:
    print("USTAWIENIA (stub)")
    print("- profil / config.toml (Sprint 1.5)")
""",
)
w(
    Path("astra/screens/bridge.py"),
    """def run() -> None:
    print("MOSTEK (stub)")
    print("- status okrętu: w Sprint 2 (state.py)")
""",
)
w(
    Path("astra/router.py"),
    """from .screens import airi, bridge, lore, settings

def dispatch(key: str) -> int:
    if key=="1": settings.run(); return 0
    if key=="2": bridge.run(); return 0
    if key=="3": airi.run(); return 0
    if key=="4": lore.run(); return 0
    if key=="0": print("Do zobaczenia."); return 0
    print("Nieznana opcja."); return 1
""",
)

# ASTRA doctor
w(
    Path("astra/doctor.py"),
    """from pathlib import Path
from .config import load_config

def run_doctor() -> int:
    root = Path.cwd()
    cfg = load_config(root)
    print("ASTRA DOCTOR")
    print(f"- cwd: {root}")
    print(f"- config.profile: {cfg.profile}")
    print(f"- config.log_enabled: {cfg.log_enabled}")
    try:
        import airi  # noqa
        print("- airi: OK")
    except Exception as e:
        print(f"! airi: FAIL ({e})"); return 2
    return 0
""",
)

# ASTRA CLI (router + doctor)
w(
    Path("astra/cli.py"),
    """from __future__ import annotations
import argparse
from .doctor import run_doctor
from .router import dispatch

MENU = [("1","Ustawienia"),("2","Udaj się na mostek"),("3","Udaj się do AIRI"),("4","Uniwersum"),("0","Wyjście")]

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="astra")
    p.add_argument("--once", choices=[m[0] for m in MENU])
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("doctor")
    ns = p.parse_args(argv)

    if ns.cmd=="doctor":
        return run_doctor()

    if ns.once:
        return dispatch(ns.once)

    while True:
        print("=== ASTRA HUB (Sprint 1.5) ===")
        for k,l in MENU: print(f"[{k}] {l}")
        ch = input("> ").strip()
        code = dispatch(ch)
        if ch=="0": return code
""",
)

w(Path("astra/__main__.py"), "from .cli import main\nraise SystemExit(main())\n")

# CLI functional tests
w(
    Path("tests/test_cli.py"),
    """import subprocess, sys

def test_astra_once_lore():
    r = subprocess.run([sys.executable,"-m","astra","--once","4"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "UNIWERSUM" in r.stdout

def test_astra_doctor():
    r = subprocess.run([sys.executable,"-m","astra","doctor"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "ASTRA DOCTOR" in r.stdout
""",
)

# Repo hygiene (minimal)
w(
    Path("CHANGELOG.md"),
    f"# Changelog\\n\\n## {V} (v0.01.5)\\n- ASTRA/AIRI interface + config + screens + doctor + CLI tests\\n",
)
w(Path("LICENSE"), "MIT License\\n")
w(Path("CONTRIBUTING.md"), "# Contributing\\n- PR: tests+ruff must pass.\\n")
w(
    Path("SECURITY.md"),
    "# Security\\n- Zgłoszenia: przez Issues (private info = email w profilu).\\n",
)
w(Path(".github/CODEOWNERS"), "* @NEIIR0\n")
w(
    Path("docs/adr/0001-monorepo-astra-airi.md"),
    "# ADR-0001 Monorepo\\nDecyzja: monorepo, moduły astra/ i airi/ + kontrakt integracji.\\n",
)
w(
    Path(".github/ISSUE_TEMPLATE/bug.md"),
    "---\nname: Bug\nabout: Report a bug\n---\n\n**Opis**\n\n**Kroki**\n\n**Logi**\n",
)
print("SPRINT 1.5 files generated.")
