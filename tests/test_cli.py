import subprocess
import sys


def test_astra_once_lore():
    r = subprocess.run(
        [sys.executable, "-m", "astra", "--once", "4", "--profile", "offline"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "UNIWERSUM" in r.stdout


def test_astra_doctor():
    r = subprocess.run(
        [sys.executable, "-m", "astra", "doctor"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "ASTRA DOCTOR" in r.stdout
