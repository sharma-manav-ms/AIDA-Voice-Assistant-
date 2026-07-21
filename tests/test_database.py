"""
test_database.py
----------------
Unit tests for MemoryStore (SQLite).
"""

import tempfile
from pathlib import Path
import pytest

from app.memory.database import MemoryStore


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        yield MemoryStore(db_path)


def test_user_preferences(temp_db):
    temp_db.set_preference("user_name", "Alice")
    assert temp_db.get_preference("user_name") == "Alice"
    assert temp_db.get_preference("missing_key", default="default") == "default"


def test_command_logging(temp_db):
    temp_db.log_command("open chrome", "app_control", True)
    temp_db.log_command("what time is it", "utility", True)

    recent = temp_db.get_recent_commands(2)
    assert len(recent) == 2
    assert recent[0]["command"] == "what time is it"
    assert recent[1]["command"] == "open chrome"


def test_notes_crud(temp_db):
    note_id = temp_db.add_note("Shopping List", "Milk, Eggs, Bread")
    assert note_id > 0

    notes = temp_db.get_notes()
    assert len(notes) == 1
    assert notes[0]["title"] == "Shopping List"

    search_res = temp_db.search_notes("Milk")
    assert len(search_res) == 1

    deleted = temp_db.delete_note(note_id)
    assert deleted is True
    assert len(temp_db.get_notes()) == 0


def test_todos_crud(temp_db):
    todo_id = temp_db.add_todo("Complete AIDA project", priority="high")
    assert todo_id > 0

    pending = temp_db.get_todos(status="pending")
    assert len(pending) == 1

    temp_db.complete_todo(todo_id)
    assert len(temp_db.get_todos(status="pending")) == 0
    assert len(temp_db.get_todos(status="completed")) == 1
