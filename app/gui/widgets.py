"""
widgets.py
----------
Custom widgets for the AIDA GUI dashboard.
Implements the Stitch 'Aura Kinetic' UI components:
- Interactive Pulsing Voice Orb with Waveform Visualizer
- System Diagnostics Card (CPU, RAM, Battery)
- Quick Action Pills
- Glassmorphic Message Bubbles
- Status Bar & Sidebar Command History

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import math
import time
import threading
from typing import Optional

import customtkinter as ctk

from app.gui.themes import (
    Theme,
    FONT_FAMILY,
    FONT_SIZE_SMALL,
    FONT_SIZE_NORMAL,
    FONT_SIZE_LARGE,
    FONT_SIZE_TITLE,
)


# ══════════════════════════════════════════════════════════════════
#  Pulsing Voice Orb & Waveform Visualizer
# ══════════════════════════════════════════════════════════════════

class VoiceOrbVisualizer(ctk.CTkCanvas):
    """
    Central 3D Holographic Voice Orb and Audio Waveform Visualizer.
    Flashes concentric Electric Indigo and Neon Cyan aura rings
    with pulsating audio wave lines when listening or speaking.
    """

    WIDTH = 280
    HEIGHT = 160

    def __init__(
        self,
        master,
        theme: Theme,
        command: Optional[callable] = None,
        **kwargs,
    ) -> None:

        super().__init__(
            master,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg=theme.bg_primary,
            highlightthickness=0,
            **kwargs,
        )

        self._theme = theme
        self._command = command
        self._animating = False
        self._phase = 0.0
        self._status = "idle"

        self._cx = self.WIDTH // 2
        self._cy = self.HEIGHT // 2 - 10
        self._orb_radius = 36

        self._draw_idle()

        self.bind("<Button-1>", self._on_click)

    def _draw_idle(self) -> None:
        """Draw orb in idle cognitive luminance state."""

        self.delete("all")
        cx, cy = self._cx, self._cy
        r = self._orb_radius

        # Outer subtle cyan aura
        self.create_oval(
            cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 16,
            fill="",
            outline=self._theme.secondary_accent,
            width=1,
            tags="aura",
        )

        # Indigo glow ring
        self.create_oval(
            cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8,
            fill=self._theme.bg_tertiary,
            outline=self._theme.accent,
            width=2,
            tags="ring",
        )

        # Core Orb
        self.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=self._theme.accent,
            outline=self._theme.accent_hover,
            width=3,
            tags="orb",
        )

        # Mic icon inside orb
        self._draw_mic_icon(cx, cy)

        # Waveform baseline
        self._draw_waveform_baseline()

        # Status text below orb
        self.create_text(
            cx, cy + r + 30,
            text="CLICK OR SAY 'AIDA' TO START",
            fill=self._theme.text_secondary,
            font=(FONT_FAMILY, 9, "bold"),
            tags="subtext",
        )

    def _draw_mic_icon(self, cx: int, cy: int) -> None:
        """Draw minimalist mic icon."""

        w, h = 7, 14
        self.create_rectangle(
            cx - w, cy - h, cx + w, cy + 2,
            fill="#FFFFFF",
            outline="",
            tags="mic",
        )
        self.create_oval(
            cx - w, cy - h - 5, cx + w, cy - h + 5,
            fill="#FFFFFF",
            outline="",
            tags="mic",
        )
        self.create_line(
            cx, cy + 5, cx, cy + 13,
            fill="#FFFFFF",
            width=2,
            tags="mic",
        )
        self.create_line(
            cx - 8, cy + 13, cx + 8, cy + 13,
            fill="#FFFFFF",
            width=2,
            tags="mic",
        )
        self.create_arc(
            cx - 12, cy - 4, cx + 12, cy + 10,
            start=0, extent=180,
            style="arc",
            outline="#FFFFFF",
            width=2,
            tags="mic",
        )

    def _draw_waveform_baseline(self) -> None:
        """Draw faint horizontal waveform bars at left and right of orb."""

        cy = self._cy
        for x in range(20, self._cx - 50, 8):
            self.create_line(x, cy, x, cy, fill=self._theme.border, width=2, tags="wave")

        for x in range(self._cx + 50, self.WIDTH - 20, 8):
            self.create_line(x, cy, x, cy, fill=self._theme.border, width=2, tags="wave")

    def start_animation(self) -> None:
        """Start pulsing & waveform animation."""

        if not self._animating:
            self._animating = True
            self._animate_frame()

    def stop_animation(self) -> None:
        """Stop animation and return to idle."""

        self._animating = False
        self._draw_idle()

    def _animate_frame(self) -> None:
        """Render a single animation frame."""

        if not self._animating:
            return

        self.delete("all")
        cx, cy = self._cx, self._cy
        r = self._orb_radius
        self._phase += 0.12

        # Dynamic expansion based on phase
        pulse_inner = math.sin(self._phase) * 6
        pulse_outer = math.cos(self._phase * 0.8) * 12

        # Outer Neon Cyan Aura Ring
        self.create_oval(
            cx - r - 20 - pulse_outer, cy - r - 20 - pulse_outer,
            cx + r + 20 + pulse_outer, cy + r + 20 + pulse_outer,
            fill="",
            outline=self._theme.secondary_glow if self._status == "listening" else self._theme.accent_hover,
            width=1,
        )

        # Middle Electric Indigo Aura Ring
        self.create_oval(
            cx - r - 10 - pulse_inner, cy - r - 10 - pulse_inner,
            cx + r + 10 + pulse_inner, cy + r + 10 + pulse_inner,
            fill=self._theme.bg_tertiary,
            outline=self._theme.accent,
            width=2,
        )

        # Core Pulsing Orb
        orb_color = self._theme.secondary_accent if self._status == "listening" else self._theme.accent
        self.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=orb_color,
            outline="#FFFFFF",
            width=2,
        )

        self._draw_mic_icon(cx, cy)

        # Real-time Waveform Neon lines
        wave_color = self._theme.secondary_glow if self._status == "listening" else self._theme.accent_hover

        # Left waveform bars
        for i, x in enumerate(range(20, cx - 50, 8)):
            h = abs(math.sin(self._phase + i * 0.4)) * 24 + 4
            self.create_line(x, cy - h / 2, x, cy + h / 2, fill=wave_color, width=3)

        # Right waveform bars
        for i, x in enumerate(range(cx + 50, self.WIDTH - 20, 8)):
            h = abs(math.cos(self._phase + i * 0.4)) * 24 + 4
            self.create_line(x, cy - h / 2, x, cy + h / 2, fill=wave_color, width=3)

        # Active Status subtext
        status_text = "LISTENING..." if self._status == "listening" else "AIDA THINKING..." if self._status == "thinking" else "SPEAKING..."
        self.create_text(
            cx, cy + r + 30,
            text=status_text,
            fill=self._theme.secondary_accent if self._status == "listening" else self._theme.accent_hover,
            font=(FONT_FAMILY, 10, "bold"),
        )

        self.after(40, self._animate_frame)

    def set_status(self, status: str) -> None:
        """Update orb state."""

        self._status = status

        if status in ("listening", "thinking", "speaking"):
            self.start_animation()
        else:
            self.stop_animation()

    def _on_click(self, event) -> None:
        if self._command:
            self._command()


# ══════════════════════════════════════════════════════════════════
#  System Diagnostics Widget Card
# ══════════════════════════════════════════════════════════════════

class SystemDiagnosticsCard(ctk.CTkFrame):
    """
    Glassmorphic System Diagnostic Widget.
    Displays live CPU, RAM, and Battery progress indicators.
    """

    def __init__(self, master, theme: Theme, **kwargs) -> None:

        super().__init__(
            master,
            fg_color=theme.bg_card,
            corner_radius=12,
            border_width=1,
            border_color=theme.border,
            **kwargs,
        )

        self._theme = theme

        # Header
        header = ctk.CTkLabel(
            self,
            text="⚡  SYSTEM DIAGNOSTICS",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=theme.secondary_accent,
            anchor="w",
        )
        header.pack(fill="x", padx=14, pady=(12, 8))

        # CPU bar
        self.cpu_bar, self.cpu_lbl = self._create_metric_row("CPU Load", theme.accent)
        # RAM bar
        self.ram_bar, self.ram_lbl = self._create_metric_row("Memory", theme.secondary_accent)
        # Battery bar
        self.bat_bar, self.bat_lbl = self._create_metric_row("Battery", theme.success)

        # Initial refresh
        self.update_metrics()

    def _create_metric_row(self, label: str, color: str):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=3)

        lbl = ctk.CTkLabel(
            row,
            text=label,
            font=(FONT_FAMILY, 10),
            text_color=self._theme.text_secondary,
            width=70,
            anchor="w",
        )
        lbl.pack(side="left")

        bar = ctk.CTkProgressBar(
            row,
            height=6,
            fg_color=self._theme.bg_tertiary,
            progress_color=color,
            corner_radius=3,
        )
        bar.pack(side="left", fill="x", expand=True, padx=(4, 8))
        bar.set(0.2)

        val_lbl = ctk.CTkLabel(
            row,
            text="--%",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=self._theme.text_primary,
            width=36,
            anchor="e",
        )
        val_lbl.pack(side="right")

        return bar, val_lbl

    def update_metrics(self) -> None:
        """Fetch real-time psutil stats."""

        try:
            import psutil

            # CPU
            cpu = psutil.cpu_percent(interval=None) / 100.0
            self.cpu_bar.set(max(0.05, cpu))
            self.cpu_lbl.configure(text=f"{int(cpu * 100)}%")

            # RAM
            mem = psutil.virtual_memory()
            ram = mem.percent / 100.0
            self.ram_bar.set(max(0.05, ram))
            self.ram_lbl.configure(text=f"{int(ram * 100)}%")

            # Battery
            bat = psutil.sensors_battery()
            if bat:
                b_val = bat.percent / 100.0
                self.bat_bar.set(max(0.05, b_val))
                self.bat_lbl.configure(text=f"{int(bat.percent)}%")
            else:
                self.bat_bar.set(1.0)
                self.bat_lbl.configure(text="100%")

        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════
#  Quick Voice Action Pills
# ══════════════════════════════════════════════════════════════════

class QuickActionsWidget(ctk.CTkFrame):
    """
    Grid of interactive shortcut pill buttons for common voice triggers.
    """

    def __init__(
        self,
        master,
        theme: Theme,
        on_action: Optional[callable] = None,
        **kwargs,
    ) -> None:

        super().__init__(
            master,
            fg_color=theme.bg_card,
            corner_radius=12,
            border_width=1,
            border_color=theme.border,
            **kwargs,
        )

        self._theme = theme
        self._on_action = on_action

        # Header
        header = ctk.CTkLabel(
            self,
            text="🚀  QUICK ACTIONS",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=theme.accent_hover,
            anchor="w",
        )
        header.pack(fill="x", padx=14, pady=(12, 8))

        actions = [
            ("🌅 Morning Briefing", "morning briefing"),
            ("📁 Find Resume", "find my resume"),
            ("🎵 Play Music", "play music on spotify"),
            ("🌦️ Weather", "what is the weather"),
            ("📋 My Tasks", "show my tasks"),
            ("📸 Screenshot", "take screenshot"),
        ]

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=(0, 10))

        for idx, (label, cmd) in enumerate(actions):
            r = idx // 2
            c = idx % 2

            btn = ctk.CTkButton(
                grid,
                text=label,
                font=(FONT_FAMILY, 11),
                fg_color=theme.bg_tertiary,
                hover_color=theme.accent,
                text_color=theme.text_primary,
                corner_radius=8,
                height=32,
                command=lambda command=cmd: self._trigger(command),
            )
            btn.grid(row=r, column=c, padx=4, pady=4, sticky="ew")
            grid.grid_columnconfigure(c, weight=1)

    def _trigger(self, command: str) -> None:
        if self._on_action:
            self._on_action(command)


# ══════════════════════════════════════════════════════════════════
#  Glassmorphic Message Bubble
# ══════════════════════════════════════════════════════════════════

class MessageBubble(ctk.CTkFrame):
    """
    Glassmorphic Chat Message Bubble with cyan top-border light stroke.
    """

    def __init__(
        self,
        master,
        role: str,
        text: str,
        theme: Theme,
        **kwargs,
    ) -> None:

        is_user = (role == "user")

        super().__init__(
            master,
            fg_color=theme.user_bubble if is_user else theme.assistant_bubble,
            corner_radius=14,
            border_width=1,
            border_color=theme.accent if is_user else theme.border,
            **kwargs,
        )

        text_color = theme.user_text if is_user else theme.assistant_text

        # Header tag
        hdr_frame = ctk.CTkFrame(self, fg_color="transparent")
        hdr_frame.pack(fill="x", padx=14, pady=(8, 0))

        role_name = "YOU" if is_user else "AIDA ASSISTANT"
        role_color = "#FFFFFF" if is_user else theme.secondary_accent

        label = ctk.CTkLabel(
            hdr_frame,
            text=role_name,
            font=(FONT_FAMILY, 10, "bold"),
            text_color=role_color,
            anchor="w",
        )
        label.pack(side="left")

        ts = ctk.CTkLabel(
            hdr_frame,
            text=time.strftime("%I:%M %p"),
            font=(FONT_FAMILY, 9),
            text_color=theme.text_muted if not is_user else "#E0E0E0",
            anchor="e",
        )
        ts.pack(side="right")

        # Message Body
        msg = ctk.CTkLabel(
            self,
            text=text,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            text_color=text_color,
            wraplength=480,
            justify="left",
            anchor="w",
        )
        msg.pack(padx=14, pady=(4, 10), anchor="w")


# ══════════════════════════════════════════════════════════════════
#  Status Bar
# ══════════════════════════════════════════════════════════════════

class StatusBar(ctk.CTkFrame):
    """
    Bottom Status bar with active indicator.
    """

    def __init__(self, master, theme: Theme, **kwargs) -> None:

        super().__init__(
            master,
            fg_color=theme.bg_secondary,
            height=34,
            corner_radius=0,
            border_width=1,
            border_color=theme.border,
            **kwargs,
        )

        self._theme = theme

        self._dot = ctk.CTkLabel(
            self,
            text="●",
            font=(FONT_FAMILY, 12),
            text_color=theme.status_idle,
            width=20,
        )
        self._dot.pack(side="left", padx=(12, 2))

        self._label = ctk.CTkLabel(
            self,
            text="SYSTEM ONLINE",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=theme.text_secondary,
        )
        self._label.pack(side="left")

        self._version = ctk.CTkLabel(
            self,
            text="AIDA v1.0.0 | Aura Kinetic Design System",
            font=(FONT_FAMILY, 10),
            text_color=theme.text_muted,
        )
        self._version.pack(side="right", padx=14)

    def set_status(self, status: str) -> None:
        """Update status bar state."""

        status_map = {
            "idle": ("SYSTEM ONLINE", self._theme.status_idle),
            "listening": ("LISTENING...", self._theme.status_listening),
            "thinking": ("THINKING...", self._theme.status_thinking),
            "speaking": ("SPEAKING...", self._theme.status_speaking),
            "executing": ("EXECUTING...", self._theme.status_thinking),
            "error": ("SYSTEM ERROR", self._theme.status_error),
        }

        text, color = status_map.get(status, ("SYSTEM ONLINE", self._theme.status_idle))

        self._label.configure(text=text)
        self._dot.configure(text_color=color)


# ══════════════════════════════════════════════════════════════════
#  Command History Panel
# ══════════════════════════════════════════════════════════════════

class CommandHistory(ctk.CTkScrollableFrame):
    """
    Scrollable list of recent commands in the sidebar.
    """

    def __init__(self, master, theme: Theme, **kwargs) -> None:

        super().__init__(
            master,
            fg_color=theme.bg_secondary,
            corner_radius=8,
            label_text="Recent Voice Commands",
            label_font=(FONT_FAMILY, 11, "bold"),
            label_fg_color=theme.bg_secondary,
            label_text_color=theme.text_secondary,
            **kwargs,
        )

        self._theme = theme
        self._items: list[ctk.CTkLabel] = []

    def add_command(self, text: str) -> None:
        """Add a command to history."""

        display = text[:45] + "..." if len(text) > 45 else text

        label = ctk.CTkLabel(
            self,
            text=f"› {display}",
            font=(FONT_FAMILY, 11),
            text_color=self._theme.text_secondary,
            anchor="w",
        )
        label.pack(fill="x", padx=6, pady=2, anchor="w")

        self._items.append(label)

        if len(self._items) > 30:
            old = self._items.pop(0)
            old.destroy()

    def clear(self) -> None:
        for item in self._items:
            item.destroy()
        self._items.clear()
