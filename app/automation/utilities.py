"""
utilities.py
------------
Desktop utility operations: screenshots, clipboard, folders, time/date.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import os
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config.config import SCREENSHOTS_DIR
from app.utils.constants import FOLDER_SHORTCUTS
from app.utils.helpers import best_match
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UtilityController:
    """
    Desktop utility operations.
    """

    # ══════════════════════════════════════════════════════════
    #  Screenshot
    # ══════════════════════════════════════════════════════════

    def take_screenshot(self, path: Optional[str] = None) -> str:
        """
        Capture the full screen and save to disk.
        """

        try:
            import pyautogui

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

            if path:
                save_path = Path(path) / filename
            else:
                save_path = SCREENSHOTS_DIR / filename

            save_path.parent.mkdir(parents=True, exist_ok=True)

            screenshot = pyautogui.screenshot()
            screenshot.save(str(save_path))

            logger.info("Screenshot saved: %s", save_path)
            return f"Screenshot saved to {save_path.name}."

        except Exception as exc:
            logger.exception("Screenshot failed")
            return f"Couldn't take screenshot: {exc}"

    # ══════════════════════════════════════════════════════════
    #  Folders
    # ══════════════════════════════════════════════════════════

    def open_folder(self, name: str = "") -> str:
        """
        Open a common system folder in Explorer.
        """

        if not name:
            return "Which folder should I open?"

        name = name.strip().lower()

        # strip prefix words
        for prefix in ("folder", "open", "the", "my"):
            name = name.replace(prefix, "").strip()

        folder_path = FOLDER_SHORTCUTS.get(name)

        if folder_path is None:
            matched = best_match(
                name,
                list(FOLDER_SHORTCUTS.keys()),
                threshold=65,
            )
            if matched:
                folder_path = FOLDER_SHORTCUTS[matched]
                name = matched

        if folder_path is None:
            return f"I don't know the folder '{name}'."

        if not folder_path.exists():
            return f"The {name} folder doesn't exist."

        os.startfile(str(folder_path))

        logger.info("Opened folder: %s", folder_path)
        return f"Opened {name.title()} folder."

    # ══════════════════════════════════════════════════════════
    #  Recycle Bin
    # ══════════════════════════════════════════════════════════

    def empty_recycle_bin(self) -> str:
        """Empty the Windows Recycle Bin."""

        try:
            import ctypes

            # SHEmptyRecycleBin(hwnd, rootPath, flags)
            # Flag 0x07 = no confirmation, no progress, no sound
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(
                None, None, 0x07
            )

            if result == 0:
                return "Recycle bin emptied."
            else:
                return "Recycle bin is already empty."

        except Exception as exc:
            logger.exception("Failed to empty recycle bin")
            return f"Couldn't empty recycle bin: {exc}"

    # ══════════════════════════════════════════════════════════
    #  Clipboard
    # ══════════════════════════════════════════════════════════

    def get_clipboard(self) -> str:
        """Read current clipboard text."""

        try:
            import pyperclip

            content = pyperclip.paste()

            if content:
                # limit response length
                preview = content[:200]
                if len(content) > 200:
                    preview += "..."
                return f"Clipboard contains: {preview}"

            return "Clipboard is empty."

        except Exception as exc:
            logger.error("Clipboard read failed: %s", exc)
            return "Couldn't read clipboard."

    def set_clipboard(self, text: str = "") -> str:
        """Copy text to clipboard."""

        if not text:
            return "What should I copy to the clipboard?"

        try:
            import pyperclip

            pyperclip.copy(text)
            return f"Copied to clipboard: {text[:100]}"

        except Exception as exc:
            logger.error("Clipboard write failed: %s", exc)
            return "Couldn't write to clipboard."

    # ══════════════════════════════════════════════════════════
    #  Type Text
    # ══════════════════════════════════════════════════════════

    def type_text(self, text: str = "") -> str:
        """Type text using keyboard simulation."""

        if not text:
            return "What should I type?"

        try:
            import pyautogui
            import time

            # small delay to let user focus the target window
            time.sleep(0.5)
            pyautogui.typewrite(text, interval=0.03)

            return f"Typed: {text[:80]}"

        except Exception as exc:
            logger.error("Type text failed: %s", exc)
            return f"Couldn't type text: {exc}"

    # ══════════════════════════════════════════════════════════
    #  Network
    # ══════════════════════════════════════════════════════════

    def get_ip_address(self) -> str:
        """Get the local IP address."""

        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return f"Your local IP address is {ip}."

        except Exception:
            return "Couldn't determine your IP address."

    # ══════════════════════════════════════════════════════════
    #  Date & Time
    # ══════════════════════════════════════════════════════════

    def get_time(self) -> str:
        """Get the current time."""

        now = datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}."

    def get_date(self) -> str:
        """Get the current date."""

        now = datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."
