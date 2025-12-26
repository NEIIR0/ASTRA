from astra.game.logbook import append_snapshot
from astra.game.replay import replay_state
from astra.game.storage import load_state, save_state


def test_replay_uses_snapshot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    s = load_state(profile="dev")
    save_state(s, profile="dev")
    append_snapshot("dev", s)

    out = replay_state(profile="dev")
    assert out.day == s.day
