"""
settings.py (GUI)
-----------------
Settings panel for the AIDA dashboard.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from app.gui.themes import (
    Theme,
    FONT_FAMILY,
    FONT_SIZE_NORMAL,
    FONT_SIZE_LARGE,
    FONT_SIZE_SMALL,
)
from app.config.settings import (
    WHISPER_MODEL,
    TTS_RATE,
    TTS_VOICE_INDEX,
    LLM_PROVIDER,
    DEFAULT_THEME,
)


class SettingsPanel(ctk.CTkToplevel):
    """
    Settings dialog for configuring the assistant.
    """

    def __init__(
        self,
        master,
        theme: Theme,
        on_save: Optional[callable] = None,
        **kwargs,
    ) -> None:

        super().__init__(master, **kwargs)

        self._theme = theme
        self._on_save = on_save

        self.title("AIDA Settings")
        self.geometry("480x560")
        self.resizable(False, False)
        self.configure(fg_color=theme.bg_primary)

        self._build_ui()

        # bring to front
        self.lift()
        self.focus_force()
        self.grab_set()

    def _build_ui(self) -> None:
        t = self._theme

        # ── Title ────────────────────────────────────────────
        title = ctk.CTkLabel(
            self,
            text="⚙  Settings",
            font=(FONT_FAMILY, FONT_SIZE_LARGE, "bold"),
            text_color=t.text_primary,
        )
        title.pack(pady=(20, 16))

        container = ctk.CTkScrollableFrame(
            self,
            fg_color=t.bg_primary,
        )
        container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # ── Whisper Model ────────────────────────────────────
        self._add_section(container, "Speech Recognition")

        self.whisper_var = ctk.StringVar(value=WHISPER_MODEL)
        self._add_dropdown(
            container, "Whisper Model",
            ["tiny", "base", "small", "medium", "large-v3"],
            self.whisper_var,
        )

        # ── TTS ──────────────────────────────────────────────
        self._add_section(container, "Text-to-Speech")

        self.rate_var = ctk.IntVar(value=TTS_RATE)
        self._add_slider(
            container, "Speech Rate",
            100, 250, self.rate_var,
        )

        self.voice_var = ctk.IntVar(value=TTS_VOICE_INDEX)
        self._add_dropdown(
            container, "Voice",
            ["Voice 0 (Male)", "Voice 1 (Female)"],
            self.voice_var,
        )

        # ── LLM ─────────────────────────────────────────────
        self._add_section(container, "AI Model")

        self.llm_var = ctk.StringVar(value=LLM_PROVIDER)
        self._add_dropdown(
            container, "LLM Provider",
            ["gemini", "openai"],
            self.llm_var,
        )

        # ── Theme ────────────────────────────────────────────
        self._add_section(container, "Appearance")

        self.theme_var = ctk.StringVar(value=DEFAULT_THEME)
        self._add_dropdown(
            container, "Theme",
            ["dark", "light"],
            self.theme_var,
        )

        # ── Save Button ─────────────────────────────────────
        save_btn = ctk.CTkButton(
            self,
            text="Save Settings",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            fg_color=t.accent,
            hover_color=t.accent_hover,
            text_color="#FFFFFF",
            corner_radius=10,
            height=42,
            command=self._save,
        )
        save_btn.pack(pady=(0, 20), padx=20, fill="x")

    def _add_section(self, parent, title: str) -> None:
        """Add a section header."""

        label = ctk.CTkLabel(
            parent,
            text=title,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            text_color=self._theme.text_primary,
            anchor="w",
        )
        label.pack(fill="x", padx=4, pady=(16, 4))

        sep = ctk.CTkFrame(
            parent,
            fg_color=self._theme.border,
            height=1,
        )
        sep.pack(fill="x", padx=4, pady=(0, 8))

    def _add_dropdown(
        self, parent, label: str, values: list, variable,
    ) -> None:
        """Add a labeled dropdown."""

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=4, pady=4)

        lbl = ctk.CTkLabel(
            row,
            text=label,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            text_color=self._theme.text_secondary,
            width=140,
            anchor="w",
        )
        lbl.pack(side="left")

        dropdown = ctk.CTkOptionMenu(
            row,
            values=[str(v) for v in values],
            variable=variable,
            fg_color=self._theme.bg_tertiary,
            button_color=self._theme.accent,
            button_hover_color=self._theme.accent_hover,
            text_color=self._theme.text_primary,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            corner_radius=8,
        )
        dropdown.pack(side="right", fill="x", expand=True)

    def _add_slider(
        self, parent, label: str,
        from_: int, to_: int, variable,
    ) -> None:
        """Add a labeled slider."""

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=4, pady=4)

        lbl = ctk.CTkLabel(
            row,
            text=label,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            text_color=self._theme.text_secondary,
            width=140,
            anchor="w",
        )
        lbl.pack(side="left")

        val_label = ctk.CTkLabel(
            row,
            text=str(variable.get()),
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            text_color=self._theme.text_primary,
            width=40,
        )
        val_label.pack(side="right")

        def on_slide(value):
            variable.set(int(value))
            val_label.configure(text=str(int(value)))

        slider = ctk.CTkSlider(
            row,
            from_=from_,
            to=to_,
            variable=variable,
            command=on_slide,
            fg_color=self._theme.bg_tertiary,
            progress_color=self._theme.accent,
            button_color=self._theme.accent,
            button_hover_color=self._theme.accent_hover,
        )
        slider.pack(side="right", fill="x", expand=True, padx=(8, 8))

    def _save(self) -> None:
        """Save settings and close."""

        settings = {
            "whisper_model": self.whisper_var.get(),
            "tts_rate": self.rate_var.get(),
            "llm_provider": self.llm_var.get(),
            "theme": self.theme_var.get(),
        }

        if self._on_save:
            self._on_save(settings)

        self.destroy()
