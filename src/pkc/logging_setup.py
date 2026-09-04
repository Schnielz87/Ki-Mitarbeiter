"""Logging auf den portablen Datentraeger (./logs)."""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

_CONFIGURED = False


def setup_logging(
    log_dir: Path,
    level: str = "INFO",
    max_bytes: int = 2_000_000,
    backups: int = 5,
    console: bool = True,
) -> Path:
    """Richtet Datei- und Konsolenlogging ein. Gibt die Logdatei zurueck."""
    global _CONFIGURED
    log_dir.mkdir(parents=True, exist_ok=True)
    logfile = log_dir / "app.log"

    root = logging.getLogger()
    root.setLevel(getattr(logging, str(level).upper(), logging.INFO))
    if _CONFIGURED:
        return logfile

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(name)-22s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=max_bytes, backupCount=backups, encoding="utf-8"
    )
    handler.setFormatter(fmt)
    root.addHandler(handler)

    if console and sys.stderr is not None:
        stream = logging.StreamHandler(sys.stderr)
        stream.setFormatter(fmt)
        stream.setLevel(logging.WARNING)
        root.addHandler(stream)

    _CONFIGURED = True
    logging.getLogger(__name__).info("Logging initialisiert: %s", logfile)
    return logfile


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
