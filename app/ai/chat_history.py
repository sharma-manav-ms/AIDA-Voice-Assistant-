"""
chat_history.py
---------------
Manages conversation context for LLM calls with a sliding window.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

from typing import Any, Optional

from app.config.settings import LLM_MAX_HISTORY_TURNS
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChatHistory:
    """
    Sliding-window conversation buffer.

    Keeps the most recent *max_turns* messages to stay within
    token limits when sending context to the LLM.
    """

    def __init__(self, max_turns: int = LLM_MAX_HISTORY_TURNS) -> None:

        self.max_turns = max_turns
        self._messages: list[dict[str, str]] = []

    # ── Adding messages ──────────────────────────────────────

    def add_user(self, text: str) -> None:
        """Append a user message."""

        self._messages.append({
            "role": "user",
            "content": text,
        })
        self._trim()

    def add_assistant(self, text: str) -> None:
        """Append an assistant message."""

        self._messages.append({
            "role": "assistant",
            "content": text,
        })
        self._trim()

    # ── Retrieval ────────────────────────────────────────────

    def get_messages(self) -> list[dict[str, str]]:
        """Return all messages in the current window."""

        return list(self._messages)

    def get_last_user_message(self) -> Optional[str]:
        """Return the most recent user message, or None."""

        for msg in reversed(self._messages):
            if msg["role"] == "user":
                return msg["content"]

        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """Return the most recent assistant message, or None."""

        for msg in reversed(self._messages):
            if msg["role"] == "assistant":
                return msg["content"]

        return None

    # ── Management ───────────────────────────────────────────

    def clear(self) -> None:
        """Reset the conversation history."""

        self._messages.clear()
        logger.debug("Chat history cleared.")

    def _trim(self) -> None:
        """Keep only the last *max_turns* messages."""

        if len(self._messages) > self.max_turns:
            excess = len(self._messages) - self.max_turns
            self._messages = self._messages[excess:]
            logger.debug("Trimmed %d old messages.", excess)

    # ── Persistence ──────────────────────────────────────────

    def save_to_db(self, db, session_id: str) -> None:
        """
        Persist all messages to the MemoryStore.

        Parameters
        ----------
        db : MemoryStore
            The database instance.
        session_id : str
            Current session identifier.
        """

        for msg in self._messages:
            db.save_message(
                role=msg["role"],
                content=msg["content"],
                session_id=session_id,
            )

        logger.info(
            "Saved %d messages to session %s.",
            len(self._messages),
            session_id,
        )

    def load_from_db(self, db, session_id: str) -> None:
        """
        Load messages from a previous session.

        Parameters
        ----------
        db : MemoryStore
            The database instance.
        session_id : str
            Session to restore from.
        """

        rows = db.get_conversation(session_id)

        self._messages = [
            {"role": r["role"], "content": r["content"]}
            for r in rows
        ]

        self._trim()

        logger.info(
            "Loaded %d messages from session %s.",
            len(self._messages),
            session_id,
        )

    # ── Info ─────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._messages)

    def __repr__(self) -> str:
        return f"ChatHistory({len(self._messages)}/{self.max_turns} turns)"
