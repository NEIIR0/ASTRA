import subprocess
import sys


def test_astra_once_game_screen():
    r = subprocess.run(
        [sys.executable, "-m", "astra", "--once", "5", "--profile", "offline"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "TRYB GRY" in r.stdout


def test_astra_game_tick_profile_after_subcommand():
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "astra",
            "game",
            "tick",
            "--seed",
            "123",
            "--profile",
            "offline",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "GAME TICK" in r.stdout
