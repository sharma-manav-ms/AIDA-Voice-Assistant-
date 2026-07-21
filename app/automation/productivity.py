"""
productivity.py
---------------
Notes, todos, reminders, and calendar management.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import re
import threading
from datetime import datetime, timedelta
from typing import Optional

from app.memory.database import MemoryStore
from app.utils.constants import RESPONSES
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProductivityManager:
    """
    Voice-driven productivity tools.

    All data is persisted through the MemoryStore (SQLite).
    """

    def __init__(self, memory: MemoryStore) -> None:
        self.db = memory
        self._active_timers: list[threading.Timer] = []
        self._reminder_callback: Optional[callable] = None

    def set_reminder_callback(self, callback: callable) -> None:
        """Set the function called when a reminder fires."""
        self._reminder_callback = callback

    # ══════════════════════════════════════════════════════════
    #  Notes
    # ══════════════════════════════════════════════════════════

    def create_note(self, content: str = "") -> str:
        """Create a new note from voice input."""

        if not content:
            return "What should I note down?"

        # use first few words as title
        words = content.split()
        title = " ".join(words[:5])

        if len(words) > 5:
            title += "..."

        note_id = self.db.add_note(title=title, content=content)

        logger.info("Note created: #%d %s", note_id, title)
        return RESPONSES["note_saved"].format(title=title)

    def list_notes_summary(self) -> str:
        """Return a spoken summary of recent notes."""

        notes = self.db.get_notes(limit=10)

        if not notes:
            return "You don't have any notes yet."

        count = len(notes)
        result = f"You have {count} note{'s' if count > 1 else ''}. "

        for i, note in enumerate(notes[:5], 1):
            result += f"{i}. {note['title']}. "

        return result

    def read_note(self, query: str = "") -> str:
        """Search for and read a note."""

        if not query:
            return "Which note should I read?"

        results = self.db.search_notes(query)

        if not results:
            return f"I couldn't find a note about '{query}'."

        note = results[0]
        return f"Note: {note['title']}. {note['content']}"

    def delete_note(self, query: str = "") -> str:
        """Delete a note matching the query."""

        if not query:
            return "Which note should I delete?"

        results = self.db.search_notes(query)

        if not results:
            return f"I couldn't find a note about '{query}'."

        note = results[0]
        self.db.delete_note(note["id"])

        return f"Deleted note: {note['title']}."

    # ══════════════════════════════════════════════════════════
    #  Todos
    # ══════════════════════════════════════════════════════════

    def add_task(self, task: str = "") -> str:
        """Add a new task to the todo list."""

        if not task:
            return "What task should I add?"

        # detect priority from the text
        priority = "medium"
        lower = task.lower()

        if any(w in lower for w in ("urgent", "important", "critical")):
            priority = "high"
        elif any(w in lower for w in ("low", "minor", "whenever")):
            priority = "low"

        task_id = self.db.add_todo(task=task, priority=priority)

        logger.info("Task added: #%d %s [%s]", task_id, task, priority)
        return RESPONSES["task_added"].format(task=task)

    def list_tasks_summary(self) -> str:
        """Return a spoken summary of pending tasks."""

        tasks = self.db.get_todos(status="pending", limit=10)

        if not tasks:
            return "Your to-do list is empty. Well done!"

        count = len(tasks)
        result = f"You have {count} pending task{'s' if count > 1 else ''}. "

        for i, task in enumerate(tasks[:5], 1):
            priority = f" (priority: {task['priority']})" \
                if task['priority'] != 'medium' else ""
            result += f"{i}. {task['task']}{priority}. "

        return result

    def complete_task_by_name(self, name: str = "") -> str:
        """Mark a task as completed by fuzzy name match."""

        if not name:
            return "Which task should I mark as done?"

        tasks = self.db.get_todos(status="pending")

        if not tasks:
            return "You don't have any pending tasks."

        # simple substring matching
        for task in tasks:
            if name.lower() in task["task"].lower():
                self.db.complete_todo(task["id"])
                return f"Completed: {task['task']}. Nice work!"

        return f"I couldn't find a task matching '{name}'."

    # ══════════════════════════════════════════════════════════
    #  Reminders
    # ══════════════════════════════════════════════════════════

    def set_reminder(self, text: str = "") -> str:
        """
        Set a reminder from voice input.

        Tries to parse time from the text, e.g.:
        - "remind me in 10 minutes to call John"
        - "set reminder for 30 minutes meeting"
        """

        if not text:
            return "What should I remind you about, and when?"

        # try to extract minutes from text
        minutes = self._extract_minutes(text)

        if minutes is None:
            minutes = 5  # default to 5 minutes

        # the message is the text without the time portion
        message = re.sub(
            r"\b(in\s+)?\d+\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)\b",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        if not message:
            message = text

        trigger_time = (
            datetime.now() + timedelta(minutes=minutes)
        ).strftime("%Y-%m-%d %H:%M:%S")

        reminder_id = self.db.add_reminder(
            message=message,
            trigger_time=trigger_time,
        )

        # set an in-process timer
        timer = threading.Timer(
            minutes * 60,
            self._fire_reminder,
            args=(reminder_id, message),
        )
        timer.daemon = True
        timer.start()
        self._active_timers.append(timer)

        logger.info(
            "Reminder #%d set for %d minutes: %s",
            reminder_id, minutes, message,
        )

        return RESPONSES["reminder_set"].format(
            time=f"{minutes} minutes"
        )

    def _fire_reminder(self, reminder_id: int, message: str) -> None:
        """Called when a reminder timer expires."""

        logger.info("Reminder fired: %s", message)
        self.db.complete_reminder(reminder_id)

        if self._reminder_callback:
            self._reminder_callback(f"Reminder: {message}")

    def _extract_minutes(self, text: str) -> Optional[int]:
        """Extract a time duration from text in minutes."""

        # "in N minutes/hours/seconds"
        match = re.search(
            r"(\d+)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        value = int(match.group(1))
        unit = match.group(2).lower()

        if unit.startswith("hour") or unit.startswith("hr"):
            return value * 60
        elif unit.startswith("sec"):
            return max(1, value // 60)

        return value

    # ══════════════════════════════════════════════════════════
    #  Calendar
    # ══════════════════════════════════════════════════════════

    def add_event(self, text: str = "") -> str:
        """Add a calendar event from voice input."""

        if not text:
            return "What event should I add, and when?"

        # simple parsing: look for date-like patterns
        today = datetime.now()

        # check for "today", "tomorrow"
        if "tomorrow" in text.lower():
            event_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            text = text.lower().replace("tomorrow", "").strip()
        elif "today" in text.lower():
            event_date = today.strftime("%Y-%m-%d")
            text = text.lower().replace("today", "").strip()
        else:
            event_date = today.strftime("%Y-%m-%d")

        # extract time (HH:MM, N AM/PM)
        time_match = re.search(
            r"(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?",
            text,
        )
        event_time = "00:00"

        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            period = time_match.group(3)

            if period and period.lower() == "pm" and hour < 12:
                hour += 12
            elif period and period.lower() == "am" and hour == 12:
                hour = 0

            event_time = f"{hour:02d}:{minute:02d}"
            text = text[:time_match.start()] + text[time_match.end():]

        title = text.strip() or "Event"

        event_id = self.db.add_event(
            title=title,
            event_date=event_date,
            event_time=event_time,
        )

        logger.info(
            "Event added: #%d %s on %s at %s",
            event_id, title, event_date, event_time,
        )

        return f"Event added: {title} on {event_date} at {event_time}."

    def today_schedule(self) -> str:
        """List today's events."""

        today = datetime.now().strftime("%Y-%m-%d")
        events = self.db.get_events_for_date(today)

        if not events:
            return "You have no events scheduled for today."

        count = len(events)
        result = f"You have {count} event{'s' if count > 1 else ''} today. "

        for i, ev in enumerate(events, 1):
            result += f"{i}. {ev['title']} at {ev['event_time']}. "

        return result
