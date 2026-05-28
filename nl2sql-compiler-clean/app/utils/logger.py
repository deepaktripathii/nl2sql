"""
logger.py
─────────
Centralised logging factory.

- Writes to both console (coloured) and file (plain text)
- Log level controlled by APP_DEBUG / LOG_LEVEL env vars
- Module-level loggers created via get_logger(__name__)
"""

from __future__ import annotations
import logging
import logging.handlers
import os
import sys
from pathlib import Path

_INITIALIZED = False
_LOG_FILE = "app/logs/query.log"

# ANSI colour codes for console output
_COLOURS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
    "RESET":    "\033[0m",
}


class _ColouredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, "")
        reset  = _COLOURS["RESET"]
        record.levelname = f"{colour}{record.levelname:<8}{reset}"
        return super().format(record)


def _init_logging() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    debug      = os.getenv("APP_DEBUG", "False").lower() == "true"
    level      = logging.DEBUG if debug else getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # ── console handler ────────────────────────────────────────────────────
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(_ColouredFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    root.addHandler(ch)

    # ── rotating file handler ──────────────────────────────────────────────
    try:
        log_path = Path(_LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        root.addHandler(fh)
    except OSError as exc:
        root.warning("Could not create log file %s: %s", _LOG_FILE, exc)

    # Silence noisy third-party loggers
    for noisy in ("urllib3", "openai", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger, initialising the logging system on first call.

    Usage
    -----
    logger = get_logger(__name__)
    logger.info("Query received: %s", query)
    """
    _init_logging()
    return logging.getLogger(name)
