"""
memory.py
---------
Session-level context for the assistant.

Tracks the current session's short-term state: recent commands,
active conversation context, and ephemeral user data.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class SessionContext:
    """
    Short-term memory for a single assistant session.

    This is NOT the persistent SQLite store — it's the in-memory
    context that feeds the LLM and tracks what happened this run.
    """

    session_id: str = ""
    user_name: str = ""
    start_time: datetime = field(default_factory=datetime.now)

    # rolling window of last N commands (text strings)
    recent_commands: deque = field(
        default_factory=lambda: deque(maxlen=50)
    )

    # conversation turns for LLM context
    conversation: list[dict[str, str]] = field(default_factory=list)

    # ephemeral key-value store for the session
    _context: dict[str, Any] = field(default_factory=dict)

    # ── Commands ─────────────────────────────────────────────

    def add_command(self, text: str) -> None:
        """Record a command that was processed this session."""

        self.recent_commands.append({
            "text": text,
            "time": datetime.now().strftime("%H:%M:%S"),
        })

    def get_last_command(self) -> Optional[str]:
        """Return the most recent command text, or None."""

        if self.recent_commands:
            return self.recent_commands[-1]["text"]
        return None

    # ── Conversation (for LLM) ───────────────────────────────

    def add_user_message(self, text: str) -> None:
        """Append a user turn to the conversation."""

        self.conversation.append({
            "role": "user",
            "content": text,
        })

    def add_assistant_message(self, text: str) -> None:
        """Append an assistant turn to the conversation."""

        self.conversation.append({
            "role": "assistant",
            "content": text,
        })

    def get_conversation_messages(
        self,
        max_turns: int = 20,
    ) -> list[dict[str, str]]:
        """
        Return the last *max_turns* conversation messages.

        This is the sliding window that gets sent to the LLM.
        """

        # Each turn is one message, so max_turns messages total
        return self.conversation[-max_turns:]

    def clear_conversation(self) -> None:
        """Reset the conversation history."""
        self.conversation.clear()

    # ── Context store ────────────────────────────────────────

    def set(self, key: str, value: Any) -> None:
        """Store an ephemeral value for this session."""
        self._context[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve an ephemeral value."""
        return self._context.get(key, default)

    # ── Info ─────────────────────────────────────────────────

    @property
    def uptime_seconds(self) -> float:
        """Seconds since session started."""

        return (datetime.now() - self.start_time).total_seconds()

    @property
    def command_count(self) -> int:
        """Number of commands processed this session."""

        return len(self.recent_commands)

    def summary(self) -> dict[str, Any]:
        """Return a summary dict for logging or display."""

        return {
            "session_id": self.session_id,
            "user_name": self.user_name,
            "uptime": f"{self.uptime_seconds:.0f}s",
            "commands": self.command_count,
            "conversation_turns": len(self.conversation),
        }
