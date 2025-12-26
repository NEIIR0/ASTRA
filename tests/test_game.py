import subprocess
import sys


def test_astra_once_game_screen():
    cmd = [sys.executable, "-m", "astra", "--once", "5"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0
    assert "TRYB GRY" in r.stdout


def test_astra_game_tick_no_save():
    cmd = [sys.executable, "-m", "astra", "game", "tick"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0
    assert "GAME TICK" in r.stdout
    assert "not saved" in r.stdout
