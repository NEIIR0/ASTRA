import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(root: Path, enabled: bool) -> logging.Logger:
    log = logging.getLogger("astra")
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    if not enabled:
        return log
    (root / "logs").mkdir(exist_ok=True)
    h = RotatingFileHandler(root / "logs" / "astra.log", maxBytes=512_000, backupCount=3, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    h.setFormatter(fmt)
    log.addHandler(h)
    return log
