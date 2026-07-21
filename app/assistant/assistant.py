"""
assistant.py
------------
Central orchestrator for AIDA.

Owns the listen → think → act → speak loop and registers
all command handlers from the automation modules.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from app.assistant.listener import Listener
from app.assistant.memory import SessionContext
from app.assistant.router import CommandRouter, CommandResult
from app.assistant.speaker import Speaker

from app.automation.app_control import AppController
from app.automation.browser import BrowserController
from app.automation.email_service import EmailController
from app.automation.file_manager import FileManager
from app.automation.media import MediaController
from app.automation.productivity import ProductivityManager
from app.automation.system import SystemController
from app.automation.utilities import UtilityController
from app.automation.workflows import WorkflowEngine

from app.ai.llm import LLMClient

from app.memory.database import MemoryStore

from app.utils.constants import (
    AssistantStatus,
    CommandCategory,
    DANGEROUS_ACTIONS,
    RESPONSES,
)
from app.utils.helpers import get_time_greeting, sanitize_text
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Assistant:
    """
    The main AIDA assistant.

    Manages the voice interaction loop and dispatches commands
    to the appropriate automation modules.
    """

    def __init__(self) -> None:

        logger.info("Initializing AIDA...")

        # ── Core components ──────────────────────────────────
        self.speaker = Speaker()
        self.listener = Listener()
        self.router = CommandRouter()
        self.memory = MemoryStore()
        self.session = SessionContext()

        # ── AI ───────────────────────────────────────────────
        try:
            self.llm = LLMClient()
            self.router.set_llm_fallback(self._llm_ask)
        except Exception as exc:
            logger.warning("LLM not available: %s", exc)
            self.llm = None

        # ── Automation modules ───────────────────────────────
        self.app_ctrl = AppController()
        self.sys_ctrl = SystemController()
        self.browser = BrowserController()
        self.file_mgr = FileManager()
        self.utilities = UtilityController()
        self.media = MediaController()
        self.email = EmailController()
        self.productivity = ProductivityManager(self.memory)
        self.workflows = WorkflowEngine(self)

        # ── State ────────────────────────────────────────────
        self.status: AssistantStatus = AssistantStatus.IDLE
        self.running: bool = False
        self._status_callback: Optional[Callable] = None
        self._message_callback: Optional[Callable] = None

        # ── Bootstrap ────────────────────────────────────────
        self.session.session_id = self.memory.new_session_id()
        self._load_user_preferences()
        self._register_all_commands()

        logger.info(
            "AIDA initialized. Session: %s",
            self.session.session_id,
        )

    # ══════════════════════════════════════════════════════════
    #  Public API
    # ══════════════════════════════════════════════════════════

    def run(self) -> None:
        """Start the continuous listen → act → speak loop (blocking)."""

        self.running = True
        self.greet()

        logger.info("Assistant loop started.")

        while self.running:
            try:
                self._set_status(AssistantStatus.LISTENING)

                text = self.listener.listen()

                if text is None:
                    continue

                text = sanitize_text(text)

                if not text:
                    continue

                logger.info("User said: %s", text)
                self._emit_message("user", text)
                self.session.add_command(text)

                # ── Check for exit commands ──────────────────
                if self._is_exit_command(text):
                    self._say(RESPONSES["goodbye"])
                    self.stop()
                    break

                # ── Process ──────────────────────────────────
                self._set_status(AssistantStatus.THINKING)

                result = self.process_command(text)

                self._set_status(AssistantStatus.SPEAKING)
                self._say(result.response)
                self._emit_message("assistant", result.response)

                # ── Persist ──────────────────────────────────
                self.memory.log_command(
                    text,
                    result.category.value,
                    result.success,
                )

                self.session.add_user_message(text)
                self.session.add_assistant_message(result.response)

            except KeyboardInterrupt:
                logger.info("Interrupted by user.")
                self.stop()
                break

            except Exception:
                logger.exception("Error in main loop.")
                self._set_status(AssistantStatus.ERROR)
                time.sleep(1)

        self._set_status(AssistantStatus.IDLE)

    def run_async(self) -> threading.Thread:
        """Start the assistant loop in a background thread."""

        thread = threading.Thread(
            target=self.run,
            daemon=True,
            name="AssistantLoop",
        )
        thread.start()
        return thread

    def stop(self) -> None:
        """Signal the assistant loop to stop."""

        self.running = False
        logger.info("Assistant stopping...")

    def process_command(self, text: str) -> CommandResult:
        """
        Route and execute a single command.

        This is also callable from the GUI for typed input.
        """

        # safety check for dangerous actions
        if self._is_dangerous(text):
            self._say(
                RESPONSES["confirm_action"].format(
                    action=text.lower()
                )
            )

            confirmation = self.listener.listen()

            if confirmation and "yes" in confirmation.lower():
                pass  # proceed
            else:
                return CommandResult(
                    category=CommandCategory.UNKNOWN,
                    action="cancelled",
                    response="Okay, cancelled.",
                    success=False,
                )

        self._set_status(AssistantStatus.EXECUTING)

        return self.router.route(text)

    def greet(self) -> None:
        """Speak a time-appropriate greeting."""

        key = get_time_greeting()
        name_part = ""

        if self.session.user_name:
            name_part = f", {self.session.user_name}"

        greeting = RESPONSES[key].format(name=name_part)
        self._say(greeting)

    # ══════════════════════════════════════════════════════════
    #  GUI Callbacks
    # ══════════════════════════════════════════════════════════

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set a function the GUI calls to update status display."""
        self._status_callback = callback

    def set_message_callback(
        self,
        callback: Callable[[str, str], None],
    ) -> None:
        """Set a function the GUI calls to display messages."""
        self._message_callback = callback

    # ══════════════════════════════════════════════════════════
    #  Command Registration
    # ══════════════════════════════════════════════════════════

    def _register_all_commands(self) -> None:
        """Wire up every automation module to the router."""

        r = self.router

        # ── App Control ──────────────────────────────────────
        r.register(
            CommandCategory.APP_CONTROL, "open_app",
            ["open", "launch", "start", "run"],
            self.app_ctrl.open_app,
        )
        r.register(
            CommandCategory.APP_CONTROL, "close_app",
            ["close", "quit", "exit", "kill"],
            self.app_ctrl.close_app,
        )
        r.register(
            CommandCategory.APP_CONTROL, "switch_app",
            ["switch to", "go to", "focus"],
            self.app_ctrl.switch_to,
        )

        # ── System Control ───────────────────────────────────
        r.register(
            CommandCategory.SYSTEM, "shutdown",
            ["shutdown", "shut down", "power off", "turn off computer"],
            self.sys_ctrl.shutdown, extract_args=False,
        )
        r.register(
            CommandCategory.SYSTEM, "restart",
            ["restart", "reboot"],
            self.sys_ctrl.restart, extract_args=False,
        )
        r.register(
            CommandCategory.SYSTEM, "sleep",
            ["sleep", "hibernate"],
            self.sys_ctrl.sleep, extract_args=False,
        )
        r.register(
            CommandCategory.SYSTEM, "lock",
            ["lock", "lock screen", "lock pc", "lock computer"],
            self.sys_ctrl.lock, extract_args=False,
        )
        r.register(
            CommandCategory.SYSTEM, "volume_up",
            ["volume up", "increase volume", "louder"],
            self.sys_ctrl.volume_up, extract_args=False,
        )
        r.register(
            CommandCategory.SYSTEM, "volume_down",
            ["volume down", "decrease volume", "quieter", "softer"],
            self.sys_ctrl.volume_down, extract_args=False,
        )
        r.register(
            CommandCategory.SYSTEM, "mute",
            ["mute", "unmute", "toggle mute"],
            self.sys_ctrl.mute_toggle, extract_args=False,
        )
        r.register(
            CommandCategory.SYSTEM, "brightness_up",
            ["brightness up", "increase brightness", "brighter"],
            self.sys_ctrl.brightness_up, extract_args=False,
        )
        r.register(
            CommandCategory.SYSTEM, "brightness_down",
            ["brightness down", "decrease brightness", "dimmer"],
            self.sys_ctrl.brightness_down, extract_args=False,
        )
        r.register(
            CommandCategory.SYSTEM, "battery",
            ["battery", "battery level", "power status"],
            self.sys_ctrl.get_battery, extract_args=False,
        )
        r.register(
            CommandCategory.SYSTEM, "system_info",
            ["system info", "system information", "pc info"],
            self.sys_ctrl.get_system_info, extract_args=False,
        )

        # ── Utilities ────────────────────────────────────────
        r.register(
            CommandCategory.UTILITY, "screenshot",
            ["screenshot", "take screenshot", "capture screen",
             "take a screenshot"],
            self.utilities.take_screenshot, extract_args=False,
        )
        r.register(
            CommandCategory.UTILITY, "open_folder",
            ["open folder", "open downloads", "open documents",
             "open desktop", "open pictures", "open music", "open videos"],
            self.utilities.open_folder,
        )
        r.register(
            CommandCategory.UTILITY, "clipboard_get",
            ["what's in clipboard", "read clipboard", "paste clipboard"],
            self.utilities.get_clipboard, extract_args=False,
        )
        r.register(
            CommandCategory.UTILITY, "clipboard_set",
            ["copy to clipboard", "set clipboard"],
            self.utilities.set_clipboard,
        )
        r.register(
            CommandCategory.UTILITY, "recycle_bin",
            ["empty recycle bin", "clear recycle bin",
             "empty trash", "clear trash"],
            self.utilities.empty_recycle_bin, extract_args=False,
        )
        r.register(
            CommandCategory.UTILITY, "time",
            ["what time", "current time", "tell me the time",
             "what's the time"],
            self.utilities.get_time, extract_args=False,
        )
        r.register(
            CommandCategory.UTILITY, "date",
            ["what date", "current date", "today's date",
             "what's the date", "what day"],
            self.utilities.get_date, extract_args=False,
        )
        r.register(
            CommandCategory.UTILITY, "ip_address",
            ["ip address", "my ip", "what's my ip"],
            self.utilities.get_ip_address, extract_args=False,
        )

        # ── Browser ──────────────────────────────────────────
        r.register(
            CommandCategory.BROWSER, "google_search",
            ["search for", "google", "search google", "look up"],
            self.browser.google_search,
        )
        r.register(
            CommandCategory.BROWSER, "google_images",
            ["search images", "google images", "find images of"],
            self.browser.google_images,
        )
        r.register(
            CommandCategory.BROWSER, "google_news",
            ["search news", "google news"],
            self.browser.google_news,
        )
        r.register(
            CommandCategory.BROWSER, "youtube_search",
            ["youtube search", "search youtube", "find on youtube"],
            self.browser.youtube_search,
        )
        r.register(
            CommandCategory.BROWSER, "youtube_play",
            ["play on youtube", "youtube play", "play video"],
            self.browser.youtube_play,
        )
        r.register(
            CommandCategory.BROWSER, "open_website",
            ["open website", "go to website", "visit"],
            self.browser.open_website,
        )

        # ── File Manager ─────────────────────────────────────
        r.register(
            CommandCategory.FILE_MANAGER, "find_files",
            ["find file", "search file", "find my", "locate",
             "where is", "search for file"],
            self.file_mgr.find_files,
        )
        r.register(
            CommandCategory.FILE_MANAGER, "find_by_type",
            ["find pdf", "find word", "find excel", "find images",
             "find videos", "find all"],
            self.file_mgr.find_by_type,
        )
        r.register(
            CommandCategory.FILE_MANAGER, "open_file",
            ["open file"],
            self.file_mgr.open_file_by_name,
        )
        r.register(
            CommandCategory.FILE_MANAGER, "delete_file",
            ["delete file", "remove file"],
            self.file_mgr.delete_file_by_name,
        )
        r.register(
            CommandCategory.FILE_MANAGER, "recent_files",
            ["recent files", "recent downloads"],
            self.file_mgr.get_recent_files_summary, extract_args=False,
        )

        # ── Email ────────────────────────────────────────────
        r.register(
            CommandCategory.EMAIL, "read_emails",
            ["read email", "check email", "unread email", "read my email",
             "check my email", "any new email"],
            self.email.read_unread_summary, extract_args=False,
        )
        r.register(
            CommandCategory.EMAIL, "send_email",
            ["send email", "send an email", "compose email", "write email"],
            self.email.send_email_interactive,
        )
        r.register(
            CommandCategory.EMAIL, "search_email",
            ["search email", "find email"],
            self.email.search_inbox_summary,
        )

        # ── Media ────────────────────────────────────────────
        r.register(
            CommandCategory.MEDIA, "play_spotify",
            ["play music", "play spotify", "open spotify and play"],
            self.media.play_spotify, extract_args=False,
        )
        r.register(
            CommandCategory.MEDIA, "pause_spotify",
            ["pause music", "pause spotify", "stop music"],
            self.media.pause_spotify, extract_args=False,
        )
        r.register(
            CommandCategory.MEDIA, "next_track",
            ["next song", "next track", "skip song", "skip track"],
            self.media.next_track, extract_args=False,
        )
        r.register(
            CommandCategory.MEDIA, "weather",
            ["weather", "what's the weather", "how's the weather",
             "weather in", "temperature"],
            self.media.get_weather,
        )
        r.register(
            CommandCategory.MEDIA, "news",
            ["news", "headlines", "latest news", "top news",
             "what's happening"],
            self.media.get_headlines, extract_args=False,
        )

        # ── Productivity ─────────────────────────────────────
        r.register(
            CommandCategory.PRODUCTIVITY, "create_note",
            ["create note", "make note", "new note", "take note",
             "note down"],
            self.productivity.create_note,
        )
        r.register(
            CommandCategory.PRODUCTIVITY, "list_notes",
            ["list notes", "show notes", "my notes", "read notes"],
            self.productivity.list_notes_summary, extract_args=False,
        )
        r.register(
            CommandCategory.PRODUCTIVITY, "add_task",
            ["add task", "new task", "add todo", "add to do",
             "remind me to"],
            self.productivity.add_task,
        )
        r.register(
            CommandCategory.PRODUCTIVITY, "list_tasks",
            ["list tasks", "show tasks", "my tasks", "pending tasks",
             "to do list", "todo list"],
            self.productivity.list_tasks_summary, extract_args=False,
        )
        r.register(
            CommandCategory.PRODUCTIVITY, "complete_task",
            ["complete task", "finish task", "done with task",
             "mark task done"],
            self.productivity.complete_task_by_name,
        )
        r.register(
            CommandCategory.PRODUCTIVITY, "set_reminder",
            ["set reminder", "remind me", "set alarm", "set timer"],
            self.productivity.set_reminder,
        )
        r.register(
            CommandCategory.PRODUCTIVITY, "add_event",
            ["add event", "schedule event", "add to calendar",
             "calendar event"],
            self.productivity.add_event,
        )
        r.register(
            CommandCategory.PRODUCTIVITY, "today_schedule",
            ["today's schedule", "what's on today", "today's events",
             "my schedule"],
            self.productivity.today_schedule, extract_args=False,
        )

        # ── Workflows ────────────────────────────────────────
        r.register(
            CommandCategory.WORKFLOW, "morning_briefing",
            ["morning briefing", "good morning briefing", "daily briefing"],
            self.workflows.morning_briefing, extract_args=False,
        )
        r.register(
            CommandCategory.WORKFLOW, "organize_downloads",
            ["organize downloads", "sort downloads", "clean downloads"],
            self.workflows.organize_downloads, extract_args=False,
        )
        r.register(
            CommandCategory.WORKFLOW, "dev_environment",
            ["launch dev", "start dev", "dev environment",
             "coding setup", "start coding"],
            self.workflows.launch_dev_environment, extract_args=False,
        )

        # ── LLM direct commands ──────────────────────────────
        r.register(
            CommandCategory.LLM_QUERY, "explain_code",
            ["explain code", "explain this code", "what does this code do"],
            self._llm_explain_code,
        )
        r.register(
            CommandCategory.LLM_QUERY, "write_email_llm",
            ["draft email", "write an email", "compose a letter"],
            self._llm_write_email,
        )
        r.register(
            CommandCategory.LLM_QUERY, "summarize",
            ["summarize", "give me a summary", "summarize this"],
            self._llm_summarize,
        )
        r.register(
            CommandCategory.LLM_QUERY, "translate",
            ["translate", "translate to", "say in"],
            self._llm_translate,
        )

        logger.info(
            "Registered %d commands across %d categories.",
            len(self.router),
            len(self.router.get_categories()),
        )

    # ══════════════════════════════════════════════════════════
    #  LLM Wrappers
    # ══════════════════════════════════════════════════════════

    def _llm_ask(self, text: str) -> str:
        """General Q&A via LLM with conversation context."""

        if not self.llm:
            return "LLM is not configured. Please set an API key in .env."

        context = self.session.get_conversation_messages()
        return self.llm.ask(text, context=context)

    def _llm_explain_code(self, code: str = "") -> str:
        if not self.llm:
            return "LLM is not configured."
        return self.llm.explain_code(code or "Please paste or read the code.")

    def _llm_write_email(self, hint: str = "") -> str:
        if not self.llm:
            return "LLM is not configured."
        return self.llm.write_email(hint=hint)

    def _llm_summarize(self, text: str = "") -> str:
        if not self.llm:
            return "LLM is not configured."
        return self.llm.summarize(text or "No text provided.")

    def _llm_translate(self, text: str = "") -> str:
        if not self.llm:
            return "LLM is not configured."
        return self.llm.translate(text)

    # ══════════════════════════════════════════════════════════
    #  Internals
    # ══════════════════════════════════════════════════════════

    def _say(self, text: str) -> None:
        """Speak text and log it."""

        if text:
            logger.info("AIDA: %s", text)
            self.speaker.speak(text)

    def _set_status(self, status: AssistantStatus) -> None:
        """Update status and notify the GUI if connected."""

        self.status = status

        if self._status_callback:
            try:
                self._status_callback(status.value)
            except Exception:
                pass

    def _emit_message(self, role: str, text: str) -> None:
        """Push a message to the GUI if connected."""

        if self._message_callback:
            try:
                self._message_callback(role, text)
            except Exception:
                pass

    def _is_exit_command(self, text: str) -> bool:
        """Check if the user wants to quit."""

        exit_phrases = {
            "goodbye", "bye", "exit", "quit", "stop",
            "go to sleep", "that's all", "shut up",
            "goodbye aida", "bye aida", "stop listening",
        }
        return text.lower().strip() in exit_phrases

    def _is_dangerous(self, text: str) -> bool:
        """Check if the command is potentially destructive."""

        lower = text.lower()
        return any(action in lower for action in DANGEROUS_ACTIONS)

    def _load_user_preferences(self) -> None:
        """Load persisted preferences into session context."""

        prefs = self.memory.get_all_preferences()

        self.session.user_name = prefs.get("user_name", "")

        logger.info(
            "Loaded preferences: user=%s",
            self.session.user_name or "(not set)",
        )
