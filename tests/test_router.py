"""
test_router.py
--------------
Unit tests for the command router.
"""

import pytest
from app.assistant.router import CommandRouter, CommandResult
from app.utils.constants import CommandCategory


def test_exact_keyword_route():
    router = CommandRouter()
    called = []

    def handle_time():
        called.append("time")
        return "12:00 PM"

    router.register(
        CommandCategory.UTILITY,
        "get_time",
        ["what time", "current time"],
        handle_time,
        extract_args=False,
    )

    res = router.route("what time is it")
    assert res.success is True
    assert res.category == CommandCategory.UTILITY
    assert res.response == "12:00 PM"
    assert "time" in called


def test_argument_extraction():
    router = CommandRouter()
    extracted_args = []

    def handle_open(app_name):
        extracted_args.append(app_name)
        return f"Opening {app_name}"

    router.register(
        CommandCategory.APP_CONTROL,
        "open_app",
        ["open", "launch"],
        handle_open,
        extract_args=True,
    )

    res = router.route("open google chrome")
    assert res.success is True
    assert res.response == "Opening google chrome"
    assert extracted_args == ["google chrome"]


def test_unknown_command():
    router = CommandRouter()
    res = router.route("xyz123abc unhandled command")
    assert res.success is False
    assert res.category == CommandCategory.UNKNOWN
