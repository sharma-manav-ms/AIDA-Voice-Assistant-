"""
app.py
------
Main CustomTkinter application window for AIDA.
Implements the Stitch 'Aura Kinetic' Cognitive Luminance desktop dashboard.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import threading
from typing import Optional

import customtkinter as ctk

from app.assistant.assistant import Assistant
from app.config.settings import (
    APP_NAME,
    APP_VERSION,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    DEFAULT_THEME,
)
from app.gui.themes import (
    Theme,
    get_theme,
    FONT_FAMILY,
    FONT_SIZE_SMALL,
    FONT_SIZE_NORMAL,
    FONT_SIZE_LARGE,
    FONT_SIZE_TITLE,
    FONT_SIZE_HEADER,
)
from app.gui.widgets import (
    VoiceOrbVisualizer,
    SystemDiagnosticsCard,
    QuickActionsWidget,
    MessageBubble,
    StatusBar,
    CommandHistory,
)
from app.gui.settings import SettingsPanel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AidaApp(ctk.CTk):
    """
    Main Aura Kinetic Dashboard window for AIDA.

    Layout:
    ┌─────────────┬───────────────────────────┬──────────────────┐
    │             │  Voice Orb & Waveform     │                  │
    │  Left       ├───────────────────────────┤  Right Sidebar   │
    │  Sidebar    │  Glassmorphic Chat        │  (Diagnostics    │
    │  (Nav &     │  Stream                   │   & Quick        │
    │   History)  ├───────────────────────────┤   Actions)       │
    │             │  Command Bar + Mic        │                  │
    ├─────────────┴───────────────────────────┴──────────────────┤
    │  Status Bar (SYSTEM ONLINE)                                │
    └────────────────────────────────────────────────────────────┘
    """

    def __init__(self) -> None:

        super().__init__()

        # ── Theme ────────────────────────────────────────────
        self._theme_name = DEFAULT_THEME
        self._theme = get_theme(self._theme_name)

        ctk.set_appearance_mode("dark" if self._theme_name == "dark" else "light")
        ctk.set_default_color_theme("blue")

        # ── Window config ────────────────────────────────────
        self.title(f"{APP_NAME} – AI Desktop Assistant")
        self.geometry("1180x780")
        self.minsize(980, 680)
        self.configure(fg_color=self._theme.bg_primary)

        # ── Build UI ─────────────────────────────────────────
        self._build_ui()

        # ── Assistant (lazy init) ────────────────────────────
        self._assistant: Optional[Assistant] = None
        self._is_listening = False

        # Start initializing assistant in background
        threading.Thread(
            target=self._init_assistant,
            daemon=True,
            name="AssistantInit",
        ).start()

    # ══════════════════════════════════════════════════════════
    #  UI Construction
    # ══════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        t = self._theme

        # ── Main grid layout ──────────────────────────────────
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Left Sidebar (Navigation & History) ───────────────
        left_sidebar = ctk.CTkFrame(
            self,
            fg_color=t.bg_secondary,
            width=240,
            corner_radius=0,
            border_width=1,
            border_color=t.border,
        )
        left_sidebar.grid(row=0, column=0, sticky="nsw")
        left_sidebar.grid_propagate(False)

        # Logo Header
        logo_frame = ctk.CTkFrame(left_sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 8))

        ctk.CTkLabel(
            logo_frame,
            text="⚡ AIDA",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            text_color=t.secondary_accent,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="Cognitive Voice Assistant",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            text_color=t.text_secondary,
            anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        # Divider
        ctk.CTkFrame(
            left_sidebar, fg_color=t.border, height=1,
        ).pack(fill="x", padx=16, pady=8)

        # Command History
        self._history = CommandHistory(
            left_sidebar, theme=t, height=360,
        )
        self._history.pack(fill="both", expand=True, padx=10, pady=4)

        # Settings button
        settings_btn = ctk.CTkButton(
            left_sidebar,
            text="⚙  Settings",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fg_color=t.bg_card,
            hover_color=t.accent,
            text_color=t.text_primary,
            corner_radius=8,
            height=36,
            command=self._show_settings,
        )
        settings_btn.pack(fill="x", padx=14, pady=(4, 16))

        # ── Center Main Content ───────────────────────────────
        center_content = ctk.CTkFrame(
            self,
            fg_color=t.bg_primary,
            corner_radius=0,
        )
        center_content.grid(row=0, column=1, sticky="nsew")
        center_content.grid_rowconfigure(1, weight=1)
        center_content.grid_columnconfigure(0, weight=1)

        # Top Section: 3D Voice Orb & Audio Waveform Visualizer
        orb_frame = ctk.CTkFrame(center_content, fg_color="transparent")
        orb_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))

        self._orb = VoiceOrbVisualizer(
            orb_frame,
            theme=t,
            command=self._on_mic_click,
        )
        self._orb.pack(anchor="center")

        # Middle Section: Glassmorphic Chat Stream
        self._chat_frame = ctk.CTkScrollableFrame(
            center_content,
            fg_color=t.bg_primary,
            corner_radius=0,
        )
        self._chat_frame.grid(
            row=1, column=0, sticky="nsew", padx=16, pady=(0, 8),
        )

        self._add_welcome()

        # Bottom Section: Command Bar + Mic Button
        input_frame = ctk.CTkFrame(
            center_content,
            fg_color=t.bg_secondary,
            corner_radius=14,
            border_width=1,
            border_color=t.border,
            height=60,
        )
        input_frame.grid(
            row=2, column=0, sticky="ew", padx=16, pady=(0, 12),
        )
        input_frame.grid_columnconfigure(0, weight=1)

        self._text_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type a command or speak to AIDA...",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fg_color=t.bg_tertiary,
            text_color=t.text_primary,
            placeholder_text_color=t.text_placeholder,
            border_color=t.border,
            corner_radius=10,
            height=40,
        )
        self._text_input.grid(
            row=0, column=0, sticky="ew", padx=(14, 8), pady=10,
        )
        self._text_input.bind("<Return>", self._on_text_submit)

        send_btn = ctk.CTkButton(
            input_frame,
            text="⚡ Send",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            fg_color=t.accent,
            hover_color=t.accent_hover,
            text_color="#FFFFFF",
            width=80,
            height=40,
            corner_radius=10,
            command=self._on_text_submit,
        )
        send_btn.grid(row=0, column=1, padx=(0, 14), pady=10)

        # ── Right Sidebar (Widgets) ───────────────────────────
        right_sidebar = ctk.CTkFrame(
            self,
            fg_color=t.bg_secondary,
            width=280,
            corner_radius=0,
            border_width=1,
            border_color=t.border,
        )
        right_sidebar.grid(row=0, column=2, sticky="nesw")
        right_sidebar.grid_propagate(False)

        # System Diagnostics Card
        self._diagnostics = SystemDiagnosticsCard(
            right_sidebar, theme=t,
        )
        self._diagnostics.pack(fill="x", padx=12, pady=(16, 8))

        # Quick Voice Actions Widget
        self._quick_actions = QuickActionsWidget(
            right_sidebar,
            theme=t,
            on_action=self._handle_quick_action,
        )
        self._quick_actions.pack(fill="x", padx=12, pady=8)

        # ── Bottom Status Bar ─────────────────────────────────
        self._status = StatusBar(self, theme=t)
        self._status.grid(row=1, column=0, columnspan=3, sticky="ew")

    def _add_welcome(self) -> None:
        """Add welcome message."""

        welcome = MessageBubble(
            self._chat_frame,
            role="assistant",
            text=(
                "Hello! I am AIDA, your AI Desktop Assistant. "
                "I am online and ready for voice commands or quick actions."
            ),
            theme=self._theme,
        )
        welcome.pack(fill="x", padx=(8, 60), pady=6, anchor="w")

    # ══════════════════════════════════════════════════════════
    #  Assistant Integration
    # ══════════════════════════════════════════════════════════

    def _init_assistant(self) -> None:
        """Initialize assistant in background thread."""

        try:
            self._update_status("thinking")

            self._assistant = Assistant()

            # Wire GUI callbacks
            self._assistant.set_status_callback(self._update_status)
            self._assistant.set_message_callback(self._add_message_safe)

            self._update_status("idle")
            logger.info("Assistant ready.")

        except Exception as exc:
            logger.exception("Failed to init assistant")
            self._update_status("error")

    def _on_mic_click(self) -> None:
        """Toggle voice listening."""

        if not self._assistant:
            self._add_message_safe("assistant", "Initializing assistant... please wait.")
            return

        if self._is_listening:
            self._assistant.stop()
            self._is_listening = False
            self._update_status("idle")
        else:
            self._is_listening = True
            self._update_status("listening")

            threading.Thread(
                target=self._listen_once,
                daemon=True,
            ).start()

    def _listen_once(self) -> None:
        """Listen once and process command."""

        try:
            text = self._assistant.listener.listen()

            if text:
                from app.utils.helpers import sanitize_text
                text = sanitize_text(text)

                if text:
                    self._add_message_safe("user", text)
                    self._history_add_safe(text)
                    self._update_status("thinking")

                    result = self._assistant.process_command(text)

                    self._update_status("speaking")
                    self._assistant.speaker.speak(result.response)

                    self._add_message_safe("assistant", result.response)

                    # Persist command
                    self._assistant.memory.log_command(
                        text, result.category.value, result.success,
                    )
                    self._diagnostics.update_metrics()

        except Exception as exc:
            logger.exception("Listen loop error")
            self._add_message_safe("assistant", f"Speech recognition error: {exc}")

        finally:
            self._is_listening = False
            self._update_status("idle")

    def _handle_quick_action(self, command: str) -> None:
        """Handle quick action button press."""

        if not self._assistant:
            return

        self._add_message_safe("user", command)
        self._history_add_safe(command)

        threading.Thread(
            target=self._process_text,
            args=(command,),
            daemon=True,
        ).start()

    def _on_text_submit(self, event=None) -> None:
        """Handle text input submit."""

        text = self._text_input.get().strip()

        if not text:
            return

        self._text_input.delete(0, "end")

        if not self._assistant:
            self._add_message_safe("assistant", "Initializing...")
            return

        self._add_message_safe("user", text)
        self._history_add_safe(text)

        threading.Thread(
            target=self._process_text,
            args=(text,),
            daemon=True,
        ).start()

    def _process_text(self, text: str) -> None:
        """Process typed command."""

        try:
            self._update_status("thinking")
            result = self._assistant.process_command(text)

            self._update_status("speaking")
            self._assistant.speaker.speak(result.response)

            self._add_message_safe("assistant", result.response)

            self._assistant.memory.log_command(
                text, result.category.value, result.success,
            )
            self._diagnostics.update_metrics()

        except Exception as exc:
            self._add_message_safe("assistant", f"Error: {exc}")

        finally:
            self._update_status("idle")

    # ══════════════════════════════════════════════════════════
    #  Thread-Safe UI Updates
    # ══════════════════════════════════════════════════════════

    def _add_message_safe(self, role: str, text: str) -> None:
        self.after(0, self._add_message, role, text)

    def _add_message(self, role: str, text: str) -> None:
        is_user = (role == "user")

        bubble = MessageBubble(
            self._chat_frame,
            role=role,
            text=text,
            theme=self._theme,
        )

        padx = (60, 8) if is_user else (8, 60)
        anchor = "e" if is_user else "w"

        bubble.pack(fill="x", padx=padx, pady=4, anchor=anchor)

        # Auto scroll down
        self._chat_frame._parent_canvas.yview_moveto(1.0)

    def _update_status(self, status: str) -> None:
        self.after(0, self._set_status, status)

    def _set_status(self, status: str) -> None:
        self._status.set_status(status)
        self._orb.set_status(status)

    def _history_add_safe(self, text: str) -> None:
        self.after(0, self._history.add_command, text)

    # ══════════════════════════════════════════════════════════
    #  Settings
    # ══════════════════════════════════════════════════════════

    def _show_settings(self) -> None:
        SettingsPanel(
            self,
            theme=self._theme,
            on_save=self._apply_settings,
        )

    def _apply_settings(self, settings: dict) -> None:
        logger.info("Settings updated: %s", settings)

        if self._assistant:
            for key, val in settings.items():
                self._assistant.memory.set_preference(key, str(val))

        self._add_message_safe(
            "assistant",
            "Settings saved successfully.",
        )
