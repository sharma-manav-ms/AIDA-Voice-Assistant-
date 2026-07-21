"""
security.py
-----------
Credential encryption and action confirmation.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from app.utils.constants import DANGEROUS_ACTIONS
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Key file location ────────────────────────────────────────────

_KEY_DIR = Path(__file__).resolve().parents[1] / "memory"
_KEY_FILE = _KEY_DIR / ".fernet.key"


class SecurityManager:
    """
    Handles credential encryption and dangerous-action gating.
    """

    def __init__(self) -> None:
        self._fernet = None
        self._init_fernet()

    def _init_fernet(self) -> None:
        """Load or generate a Fernet encryption key."""

        try:
            from cryptography.fernet import Fernet

            if _KEY_FILE.exists():
                key = _KEY_FILE.read_bytes()
            else:
                key = Fernet.generate_key()
                _KEY_DIR.mkdir(parents=True, exist_ok=True)
                _KEY_FILE.write_bytes(key)
                logger.info("Generated new encryption key.")

            self._fernet = Fernet(key)

        except ImportError:
            logger.warning(
                "cryptography package not installed. "
                "Encryption features disabled."
            )

    # ── Encrypt / Decrypt ────────────────────────────────────

    def encrypt(self, plaintext: str) -> Optional[str]:
        """
        Encrypt a string.

        Returns the encrypted token as a UTF-8 string,
        or None if encryption is unavailable.
        """

        if self._fernet is None:
            return None

        try:
            return self._fernet.encrypt(
                plaintext.encode("utf-8")
            ).decode("utf-8")

        except Exception as exc:
            logger.error("Encryption failed: %s", exc)
            return None

    def decrypt(self, token: str) -> Optional[str]:
        """
        Decrypt an encrypted token.

        Returns the plaintext string, or None on failure.
        """

        if self._fernet is None:
            return None

        try:
            return self._fernet.decrypt(
                token.encode("utf-8")
            ).decode("utf-8")

        except Exception as exc:
            logger.error("Decryption failed: %s", exc)
            return None

    # ── Action Safety ────────────────────────────────────────

    @staticmethod
    def is_dangerous(command: str) -> bool:
        """
        Check whether a command string contains a dangerous action.
        """

        lower = command.lower()

        return any(action in lower for action in DANGEROUS_ACTIONS)

    @staticmethod
    def confirm_action_text(action: str) -> str:
        """
        Return the confirmation prompt for a dangerous action.
        """

        return (
            f"You asked me to {action}. "
            f"This is a potentially risky action. "
            f"Please say 'yes' to confirm, or 'no' to cancel."
        )

    @staticmethod
    def is_confirmed(response: str) -> bool:
        """Check whether the user confirmed an action."""

        if not response:
            return False

        lower = response.strip().lower()

        affirmatives = {
            "yes", "yeah", "yep", "sure", "confirm",
            "do it", "go ahead", "proceed", "ok", "okay",
            "affirmative",
        }

        return any(word in lower for word in affirmatives)

    # ── Environment Validation ───────────────────────────────

    @staticmethod
    def validate_env_keys(
        required: list[str],
    ) -> dict[str, bool]:
        """
        Check that required environment variables are set.

        Returns a dict mapping each key to True/False.
        """

        return {
            key: bool(os.getenv(key))
            for key in required
        }
