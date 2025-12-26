import subprocess
import sys

from astra.airi.stub import StubAiri
from astra.game.state import default_state


def test_stub_airi_proposes():
    s = default_state()
    props = StubAiri().propose(state=s)
    assert isinstance(props, list)


def test_airi_module_runs():
    r = subprocess.run(
        [sys.executable, "-m", "astra.airi", "propose", "--profile", "offline"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "AIRI PROPOSE" in r.stdout
