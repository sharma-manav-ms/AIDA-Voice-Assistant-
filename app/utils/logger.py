"""
logger.py
---------
Application-wide logging with console + rotating file output.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from colorama import Fore, Style, init as colorama_init

# Initialize colorama for Windows ANSI support
colorama_init(autoreset=True)


# ── Paths ────────────────────────────────────────────────────────

_LOG_DIR = Path(__file__).resolve().parents[1] / "memory" / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "aida.log"


# ── Color Formatter ──────────────────────────────────────────────

class ColorFormatter(logging.Formatter):
    """Add ANSI colors to console log output."""

    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


# ── Factory ──────────────────────────────────────────────────────

_CONFIGURED: set[str] = set()


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger with colored console and rotating file handlers.

    Calling this multiple times with the same *name* returns
    the same logger without duplicating handlers.

    Parameters
    ----------
    name : str
        Logger name — typically ``__name__``.

    Returns
    -------
    logging.Logger
    """

    if name in _CONFIGURED:
        return logging.getLogger(name)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # avoid duplicating handlers if basicConfig was called elsewhere
    if logger.hasHandlers():
        logger.handlers.clear()

    # ── Console handler (colored) ────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(
        ColorFormatter(
            "[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(console)

    # ── File handler (rotating, 5 MB × 3 backups) ───────────
    try:
        file_handler = RotatingFileHandler(
            _LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)
    except OSError:
        # gracefully degrade if log file is locked
        logger.warning("Could not open log file: %s", _LOG_FILE)

    _CONFIGURED.add(name)

    return logger