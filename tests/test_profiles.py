from pathlib import Path

from astra.game.storage import load_state, save_state, state_path


def test_profiles_separate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    s = load_state(profile="p1")
    save_state(s, profile="p1")

    p = state_path("p1")
    assert p.exists()
    assert Path("data/profiles/p1/game_state.json").exists()

    s2 = load_state(profile="p2")
    save_state(s2, profile="p2")
    assert Path("data/profiles/p2/game_state.json").exists()
