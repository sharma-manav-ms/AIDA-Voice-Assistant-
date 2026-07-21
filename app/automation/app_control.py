"""
app_control.py
--------------
Open, close, and switch between desktop applications.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

import psutil

from app.utils.constants import APP_REGISTRY, RESPONSES, resolve_app_path
from app.utils.helpers import best_match
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AppController:
    """
    Desktop application manager.

    Handles opening, closing, and switching between Windows apps
    using a registry of known application paths.
    """

    def __init__(self) -> None:
        self._known_names = list(APP_REGISTRY.keys())

    # ── Open ─────────────────────────────────────────────────

    def open_app(self, name: str = "") -> str:
        """
        Open an application by spoken name.

        Falls back to fuzzy matching if the exact name isn't found.
        """

        if not name:
            return "Which application would you like me to open?"

        name = name.strip().lower()

        # direct registry lookup
        path = resolve_app_path(name)

        # fuzzy fallback
        if path is None:
            matched = best_match(name, self._known_names, threshold=65)
            if matched:
                path = resolve_app_path(matched)
                name = matched

        if path is None:
            return RESPONSES["app_not_found"].format(app=name)

        try:
            # ms-settings: style URIs
            if path.startswith("ms-"):
                os.startfile(path)
            else:
                # handle paths with arguments (e.g. Discord)
                subprocess.Popen(
                    path,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            logger.info("Opened: %s → %s", name, path)
            return RESPONSES["opening_app"].format(app=name.title())

        except FileNotFoundError:
            return RESPONSES["app_not_found"].format(app=name.title())

        except Exception as exc:
            logger.exception("Failed to open %s", name)
            return RESPONSES["action_failed"].format(
                action=f"open {name}",
                reason=str(exc),
            )

    # ── Close ────────────────────────────────────────────────

    def close_app(self, name: str = "") -> str:
        """
        Close an application by killing matching processes.
        """

        if not name:
            return "Which application should I close?"

        name = name.strip().lower()

        # Map spoken name to process name
        process_map = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "firefox": "firefox.exe",
            "notepad": "notepad.exe",
            "calculator": "CalculatorApp.exe",
            "paint": "mspaint.exe",
            "spotify": "Spotify.exe",
            "discord": "Discord.exe",
            "vscode": "Code.exe",
            "vs code": "Code.exe",
            "visual studio code": "Code.exe",
            "word": "WINWORD.EXE",
            "excel": "EXCEL.EXE",
            "powerpoint": "POWERPNT.EXE",
            "vlc": "vlc.exe",
            "task manager": "Taskmgr.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
        }

        proc_name = process_map.get(name)

        if proc_name is None:
            matched = best_match(name, list(process_map.keys()))
            if matched:
                proc_name = process_map[matched]
                name = matched

        if proc_name is None:
            # try generic kill by name
            proc_name = f"{name}.exe"

        killed = 0

        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and \
                   proc.info["name"].lower() == proc_name.lower():
                    proc.terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if killed:
            return RESPONSES["closing_app"].format(app=name.title())

        return f"{name.title()} doesn't seem to be running."

    # ── Switch / Focus ───────────────────────────────────────

    def switch_to(self, name: str = "") -> str:
        """
        Bring an application window to the foreground.

        Uses pyautogui / win32gui to find and focus the window.
        """

        if not name:
            return "Which application should I switch to?"

        name = name.strip().lower()

        try:
            import pyautogui

            # find windows matching the app name
            windows = pyautogui.getWindowsWithTitle(name)

            if not windows:
                # try title case
                windows = pyautogui.getWindowsWithTitle(name.title())

            if windows:
                win = windows[0]
                if win.isMinimized:
                    win.restore()
                win.activate()
                return f"Switched to {name.title()}."

            return f"I can't find a window for {name.title()}."

        except Exception as exc:
            logger.exception("Failed to switch to %s", name)
            return f"Couldn't switch to {name.title()}: {exc}"

    # ── Query ────────────────────────────────────────────────

    def is_running(self, name: str) -> bool:
        """Check if an application process is active."""

        name_lower = name.lower()

        for proc in psutil.process_iter(["name"]):
            try:
                pname = proc.info.get("name", "")
                if pname and name_lower in pname.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return False

    def list_running(self) -> str:
        """Return a summary of running known applications."""

        running = []

        for app_name in self._known_names:
            if self.is_running(app_name):
                running.append(app_name.title())

        if running:
            return "Running apps: " + ", ".join(running)

        return "No known apps are currently running."
