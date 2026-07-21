"""
constants.py
------------
Enums, response templates, and application registry.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path


# ── Application Metadata ─────────────────────────────────────────

APP_NAME = "AIDA"
APP_FULL_NAME = "AI Desktop Assistant"
APP_VERSION = "1.0.0"
AUTHOR = "Manav Sharma"


# ── Command Categories ───────────────────────────────────────────

class CommandCategory(str, Enum):
    """Categories that the router dispatches commands to."""

    APP_CONTROL = "app_control"
    SYSTEM = "system"
    BROWSER = "browser"
    FILE_MANAGER = "file_manager"
    EMAIL = "email"
    MEDIA = "media"
    PRODUCTIVITY = "productivity"
    LLM_QUERY = "llm_query"
    WORKFLOW = "workflow"
    UTILITY = "utility"
    UNKNOWN = "unknown"


# ── Assistant Status ─────────────────────────────────────────────

class AssistantStatus(str, Enum):
    """States the assistant can be in."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    EXECUTING = "executing"
    ERROR = "error"


# ── Response Templates ───────────────────────────────────────────

RESPONSES = {
    "greeting_morning": "Good morning{name}! I'm AIDA, your desktop assistant. How can I help you?",
    "greeting_afternoon": "Good afternoon{name}! What can I do for you?",
    "greeting_evening": "Good evening{name}! How may I assist you?",

    "unknown_command": "I'm not sure what you mean. Could you try rephrasing that?",
    "confirm_action": "Are you sure you want to {action}?",
    "action_done": "Done! {detail}",
    "action_failed": "Sorry, I couldn't {action}. {reason}",

    "opening_app": "Opening {app} for you.",
    "closing_app": "Closing {app}.",
    "app_not_found": "I couldn't find {app} on your system.",
    "app_already_running": "{app} is already running.",

    "searching": "Searching for {query}.",
    "playing": "Playing {item}.",
    "no_results": "I couldn't find any results for {query}.",

    "email_sent": "Email sent to {to}.",
    "email_read": "You have {count} unread emails.",
    "no_emails": "You have no unread emails.",

    "file_found": "I found {count} matching files.",
    "file_not_found": "I couldn't find any files matching {query}.",
    "file_deleted": "File deleted: {name}.",

    "note_saved": "Note saved: {title}.",
    "task_added": "Task added: {task}.",
    "reminder_set": "Reminder set for {time}.",

    "shutdown_warning": "Your PC will shut down in {delay} seconds.",
    "goodbye": "Goodbye! Have a great day!",
    "listening": "I'm listening...",
    "thinking": "Let me think about that...",
}


# ── Windows Application Registry ────────────────────────────────
# Maps spoken app names to executable paths / commands.

APP_REGISTRY: dict[str, str] = {
    # Built-in Windows apps
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "command prompt": "cmd.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "control panel": "control.exe",
    "snipping tool": "SnippingTool.exe",
    "settings": "ms-settings:",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",

    # Common third-party apps (best-effort paths)
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "microsoft edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "vscode": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vs code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "spotify": r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    "discord": r"C:\Users\{user}\AppData\Local\Discord\Update.exe --processStart Discord.exe",
    "telegram": r"C:\Users\{user}\AppData\Roaming\Telegram Desktop\Telegram.exe",
    "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "obs": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
}


def resolve_app_path(app_name: str) -> str | None:
    """
    Look up an application path by spoken name.

    Resolves ``{user}`` placeholder with the current username.

    Returns
    -------
    str | None
        Resolved executable path, or ``None`` if not found.
    """

    import os

    raw = APP_REGISTRY.get(app_name.lower())

    if raw is None:
        return None

    return raw.replace("{user}", os.getenv("USERNAME", ""))


# ── Website Registry ─────────────────────────────────────────────

SITE_REGISTRY: dict[str, str] = {
    "linkedin": "https://www.linkedin.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "google mail": "https://mail.google.com",
    "chatgpt": "https://chat.openai.com",
    "chat gpt": "https://chat.openai.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "amazon": "https://www.amazon.com",
    "whatsapp": "https://web.whatsapp.com",
    "notion": "https://www.notion.so",
    "google drive": "https://drive.google.com",
    "google docs": "https://docs.google.com",
    "google sheets": "https://sheets.google.com",
}


# ── Dangerous Commands ───────────────────────────────────────────
# Actions that require explicit voice confirmation before execution.

DANGEROUS_ACTIONS: set[str] = {
    "shutdown",
    "restart",
    "sleep",
    "delete",
    "empty recycle bin",
    "format",
    "send email",
    "move file",
}


# ── Folder Shortcuts ─────────────────────────────────────────────

FOLDER_SHORTCUTS: dict[str, Path] = {
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "desktop": Path.home() / "Desktop",
    "pictures": Path.home() / "Pictures",
    "music": Path.home() / "Music",
    "videos": Path.home() / "Videos",
}
