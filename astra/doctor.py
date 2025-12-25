from pathlib import Path

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
        print(f"! airi: FAIL ({e})")
        return 2
    return 0
