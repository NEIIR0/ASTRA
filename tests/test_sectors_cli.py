import subprocess
import sys


def test_sectors_cli_list_runs():
    r = subprocess.run([sys.executable, "-m", "astra.sectors", "list"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "SECTORS" in r.stdout
    assert "Mostek" in r.stdout
