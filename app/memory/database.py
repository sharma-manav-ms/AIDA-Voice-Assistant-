"""
database.py
-----------
SQLite-backed persistent storage for AIDA.

Stores user preferences, command history, conversations,
notes, todos, calendar events, and reminders.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryStore:
    """
    Persistent storage using SQLite.

    All public methods are self-contained transactions.
    """

    def __init__(self, db_path: Optional[str | Path] = None) -> None:

        if db_path is None:
            from app.config.config import DB_PATH
            db_path = DB_PATH

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_tables()

        logger.info("MemoryStore initialized at %s", self.db_path)

    # ── Connection helper ────────────────────────────────────

    @contextmanager
    def _connect(self):
        """Yield a cursor inside a committed transaction."""

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ── Schema ───────────────────────────────────────────────

    def _init_tables(self) -> None:
        """Create tables if they don't exist."""

        with self._connect() as conn:
            conn.executescript("""

                CREATE TABLE IF NOT EXISTS user_preferences (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS command_history (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    command   TEXT    NOT NULL,
                    category  TEXT    NOT NULL DEFAULT 'unknown',
                    success   INTEGER NOT NULL DEFAULT 1,
                    timestamp TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT    NOT NULL,
                    role       TEXT    NOT NULL,
                    content    TEXT    NOT NULL,
                    timestamp  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS notes (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    title      TEXT    NOT NULL,
                    content    TEXT    NOT NULL DEFAULT '',
                    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS todos (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    task         TEXT    NOT NULL,
                    priority     TEXT    NOT NULL DEFAULT 'medium',
                    status       TEXT    NOT NULL DEFAULT 'pending',
                    created_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS calendar_events (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    title      TEXT    NOT NULL,
                    event_date TEXT    NOT NULL,
                    event_time TEXT    NOT NULL DEFAULT '00:00',
                    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS reminders (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    message      TEXT    NOT NULL,
                    trigger_time TEXT    NOT NULL,
                    status       TEXT    NOT NULL DEFAULT 'pending',
                    created_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE INDEX IF NOT EXISTS idx_cmd_ts
                    ON command_history(timestamp);

                CREATE INDEX IF NOT EXISTS idx_conv_session
                    ON conversations(session_id);

                CREATE INDEX IF NOT EXISTS idx_todo_status
                    ON todos(status);

                CREATE INDEX IF NOT EXISTS idx_reminder_status
                    ON reminders(status);
            """)

    # ══════════════════════════════════════════════════════════
    #  User Preferences
    # ══════════════════════════════════════════════════════════

    def set_preference(self, key: str, value: str) -> None:
        """Insert or update a user preference."""

        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_preferences (key, value) "
                "VALUES (?, ?)",
                (key, value),
            )

    def get_preference(self, key: str, default: str = "") -> str:
        """Retrieve a preference value, or *default* if missing."""

        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM user_preferences WHERE key = ?",
                (key,),
            ).fetchone()

        return row["value"] if row else default

    def get_all_preferences(self) -> dict[str, str]:
        """Return all stored preferences as a dict."""

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, value FROM user_preferences"
            ).fetchall()

        return {r["key"]: r["value"] for r in rows}

    # ══════════════════════════════════════════════════════════
    #  Command History
    # ══════════════════════════════════════════════════════════

    def log_command(
        self,
        command: str,
        category: str = "unknown",
        success: bool = True,
    ) -> None:
        """Record an executed command."""

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO command_history (command, category, success) "
                "VALUES (?, ?, ?)",
                (command, category, int(success)),
            )

    def get_recent_commands(self, n: int = 20) -> list[dict[str, Any]]:
        """Return the last *n* commands."""

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT command, category, success, timestamp "
                "FROM command_history ORDER BY id DESC LIMIT ?",
                (n,),
            ).fetchall()

        return [dict(r) for r in rows]

    def get_frequent_commands(self, n: int = 10) -> list[dict[str, Any]]:
        """Return the *n* most frequently used commands."""

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT command, COUNT(*) as count "
                "FROM command_history "
                "GROUP BY command ORDER BY count DESC LIMIT ?",
                (n,),
            ).fetchall()

        return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════════════
    #  Conversations
    # ══════════════════════════════════════════════════════════

    def new_session_id(self) -> str:
        """Generate a unique session identifier."""
        return uuid.uuid4().hex[:12]

    def save_message(
        self,
        role: str,
        content: str,
        session_id: str,
    ) -> None:
        """Persist a single chat message."""

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO conversations (session_id, role, content) "
                "VALUES (?, ?, ?)",
                (session_id, role, content),
            )

    def get_conversation(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve messages for a session, oldest first."""

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content, timestamp FROM conversations "
                "WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                (session_id, limit),
            ).fetchall()

        return [dict(r) for r in rows]

    # ══════════════════════════════════════════════════════════
    #  Notes
    # ══════════════════════════════════════════════════════════

    def add_note(self, title: str, content: str = "") -> int:
        """Create a note. Returns the new note id."""

        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (title, content) VALUES (?, ?)",
                (title, content),
            )
            return cursor.lastrowid

    def get_notes(self, limit: int = 50) -> list[dict[str, Any]]:
        """List notes, most recent first."""

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, title, content, created_at, updated_at "
                "FROM notes ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [dict(r) for r in rows]

    def search_notes(self, query: str) -> list[dict[str, Any]]:
        """Full-text search on note title and content."""

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, title, content, created_at FROM notes "
                "WHERE title LIKE ? OR content LIKE ? "
                "ORDER BY id DESC",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()

        return [dict(r) for r in rows]

    def delete_note(self, note_id: int) -> bool:
        """Delete a note by id. Returns True if a row was removed."""

        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM notes WHERE id = ?", (note_id,)
            )
            return cursor.rowcount > 0

    # ══════════════════════════════════════════════════════════
    #  Todos
    # ══════════════════════════════════════════════════════════

    def add_todo(
        self,
        task: str,
        priority: str = "medium",
    ) -> int:
        """Create a todo item. Returns the new id."""

        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO todos (task, priority) VALUES (?, ?)",
                (task, priority),
            )
            return cursor.lastrowid

    def get_todos(
        self,
        status: str = "pending",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List todos filtered by status."""

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, task, priority, status, created_at, completed_at "
                "FROM todos WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()

        return [dict(r) for r in rows]

    def complete_todo(self, todo_id: int) -> bool:
        """Mark a todo as completed."""

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE todos SET status = 'completed', completed_at = ? "
                "WHERE id = ?",
                (now, todo_id),
            )
            return cursor.rowcount > 0

    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo item."""

        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM todos WHERE id = ?", (todo_id,)
            )
            return cursor.rowcount > 0

    # ══════════════════════════════════════════════════════════
    #  Calendar Events
    # ══════════════════════════════════════════════════════════

    def add_event(
        self,
        title: str,
        event_date: str,
        event_time: str = "00:00",
    ) -> int:
        """Add a calendar event. Returns the new id."""

        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO calendar_events (title, event_date, event_time) "
                "VALUES (?, ?, ?)",
                (title, event_date, event_time),
            )
            return cursor.lastrowid

    def get_events_for_date(self, date: str) -> list[dict[str, Any]]:
        """Retrieve events for a given date (YYYY-MM-DD)."""

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, title, event_date, event_time "
                "FROM calendar_events WHERE event_date = ? "
                "ORDER BY event_time ASC",
                (date,),
            ).fetchall()

        return [dict(r) for r in rows]

    def delete_event(self, event_id: int) -> bool:
        """Delete a calendar event."""

        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM calendar_events WHERE id = ?", (event_id,)
            )
            return cursor.rowcount > 0

    # ══════════════════════════════════════════════════════════
    #  Reminders
    # ══════════════════════════════════════════════════════════

    def add_reminder(
        self,
        message: str,
        trigger_time: str,
    ) -> int:
        """Schedule a reminder. Returns the new id."""

        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO reminders (message, trigger_time) "
                "VALUES (?, ?)",
                (message, trigger_time),
            )
            return cursor.lastrowid

    def get_pending_reminders(self) -> list[dict[str, Any]]:
        """Return reminders that are still pending."""

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, message, trigger_time FROM reminders "
                "WHERE status = 'pending' AND trigger_time <= ? "
                "ORDER BY trigger_time ASC",
                (now,),
            ).fetchall()

        return [dict(r) for r in rows]

    def complete_reminder(self, reminder_id: int) -> bool:
        """Mark a reminder as fired."""

        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE reminders SET status = 'fired' WHERE id = ?",
                (reminder_id,),
            )
            return cursor.rowcount > 0
