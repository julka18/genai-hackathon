# utilities/logger.py
from __future__ import annotations
import logging
import time
from contextlib import ContextDecorator
from datetime import datetime
from pathlib import Path

# -------- repo root discovery --------
def _find_repo_root(start: Path) -> Path:
    markers = {".git", "pyproject.toml", "README.md", "package.json"}
    cur = start.resolve()
    for _ in range(6):
        if any((cur / m).exists() for m in markers):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.parent

_THIS_FILE = Path(__file__).resolve()
REPO_ROOT = _find_repo_root(_THIS_FILE)
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
_FMT = "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s"

def _configure_root_logger() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(_FMT))

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(_FMT))

    root.addHandler(fh)
    root.addHandler(ch)

_configure_root_logger()
logging.getLogger(__name__).info("✅ Logger initialized → %s", LOG_FILE)

def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or __name__)

def get_log_file() -> Path:
    return LOG_FILE

class _Step(ContextDecorator):
    def __init__(self, name: str, logger: logging.Logger | None = None, **meta):
        self.name = name
        self.logger = logger or get_logger("step")
        self.meta = meta
        self._t0 = 0.0

    def __enter__(self):
        meta = f" | meta={self.meta}" if self.meta else ""
        self.logger.info("▶️ START: %s%s", self.name, meta)
        self._t0 = time.perf_counter()
        return self

    def done(self, **extra):
        dt = time.perf_counter() - self._t0
        merged = {**self.meta, **extra} if (self.meta or extra) else None
        meta = f" | meta={merged}" if merged else ""
        self.logger.info("✅ DONE : %s (%.2fs)%s", self.name, dt, meta)

    def __exit__(self, exc_type, exc, tb):
        if exc:
            dt = time.perf_counter() - self._t0
            self.logger.exception("❌ FAIL : %s (%.2fs) — %s", self.name, dt, exc)
            return False
        self.done()
        return True

def step(name: str, logger: logging.Logger | None = None, **meta) -> _Step:
    return _Step(name, logger=logger, **meta)
