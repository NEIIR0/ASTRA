import subprocess
import sys


def test_action_move_no_write():
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "astra",
            "game",
            "action",
            "move",
            "--sector",
            "Mostek",
            "--profile",
            "offline",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "ACTION MOVE" in r.stdout
    assert "not saved" in r.stdout
