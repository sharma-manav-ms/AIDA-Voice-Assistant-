"""
workflows.py
------------
Multi-step automated workflows.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING

from app.utils.constants import FOLDER_SHORTCUTS
from app.utils.logger import get_logger

if TYPE_CHECKING:
    from app.assistant.assistant import Assistant

logger = get_logger(__name__)


class WorkflowEngine:
    """
    Multi-step automated workflows that chain multiple
    automation actions together.
    """

    def __init__(self, assistant: "Assistant") -> None:
        self._assistant = assistant

    # ══════════════════════════════════════════════════════════
    #  Morning Briefing
    # ══════════════════════════════════════════════════════════

    def morning_briefing(self) -> str:
        """
        Deliver a morning briefing: weather, schedule, emails, news.
        """

        logger.info("Running morning briefing workflow.")
        parts = []

        # 1. Greeting
        parts.append("Good morning! Here's your daily briefing.")

        # 2. Date and time
        parts.append(
            self._assistant.utilities.get_date()
        )
        parts.append(
            self._assistant.utilities.get_time()
        )

        # 3. Weather
        try:
            weather = self._assistant.media.get_weather()
            parts.append(weather)
        except Exception:
            parts.append("I couldn't get the weather.")

        # 4. Today's schedule
        try:
            schedule = self._assistant.productivity.today_schedule()
            parts.append(schedule)
        except Exception:
            parts.append("No events on your calendar.")

        # 5. Unread emails
        try:
            emails = self._assistant.email.read_unread_summary()
            parts.append(emails)
        except Exception:
            parts.append("Couldn't check your emails.")

        # 6. News headlines
        try:
            news = self._assistant.media.get_headlines()
            parts.append(news)
        except Exception:
            parts.append("Couldn't fetch the news.")

        return " ".join(parts)

    # ══════════════════════════════════════════════════════════
    #  Organize Downloads
    # ══════════════════════════════════════════════════════════

    def organize_downloads(self) -> str:
        """
        Sort the Downloads folder into subfolders by file type.

        Creates subfolders: Images, Documents, Videos, Audio,
        Archives, Code, Others.
        """

        downloads = FOLDER_SHORTCUTS.get("downloads")

        if not downloads or not downloads.exists():
            return "Downloads folder not found."

        category_map = {
            "Images": {
                ".jpg", ".jpeg", ".png", ".gif", ".bmp",
                ".webp", ".svg", ".ico", ".tiff",
            },
            "Documents": {
                ".pdf", ".doc", ".docx", ".xls", ".xlsx",
                ".ppt", ".pptx", ".txt", ".csv", ".rtf",
                ".odt", ".ods",
            },
            "Videos": {
                ".mp4", ".avi", ".mkv", ".mov", ".wmv",
                ".flv", ".webm",
            },
            "Audio": {
                ".mp3", ".wav", ".flac", ".aac", ".ogg",
                ".wma", ".m4a",
            },
            "Archives": {
                ".zip", ".rar", ".7z", ".tar", ".gz",
                ".bz2", ".xz",
            },
            "Code": {
                ".py", ".js", ".ts", ".html", ".css",
                ".java", ".cpp", ".c", ".h", ".json",
                ".xml", ".yaml", ".yml", ".sh", ".bat",
            },
            "Installers": {
                ".exe", ".msi", ".dmg", ".deb", ".rpm",
            },
        }

        moved_count = 0
        skipped = 0

        for item in downloads.iterdir():
            if item.is_dir():
                continue

            ext = item.suffix.lower()
            target_folder = "Others"

            for category, extensions in category_map.items():
                if ext in extensions:
                    target_folder = category
                    break

            dest_dir = downloads / target_folder
            dest_dir.mkdir(exist_ok=True)

            dest_path = dest_dir / item.name

            # handle duplicates
            if dest_path.exists():
                stem = item.stem
                suffix = item.suffix
                counter = 1
                while dest_path.exists():
                    dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

            try:
                shutil.move(str(item), str(dest_path))
                moved_count += 1
            except Exception:
                skipped += 1

        logger.info(
            "Organized downloads: %d moved, %d skipped.",
            moved_count, skipped,
        )

        return (
            f"Downloads organized! Moved {moved_count} files "
            f"into categorized folders."
        )

    # ══════════════════════════════════════════════════════════
    #  Development Environment
    # ══════════════════════════════════════════════════════════

    def launch_dev_environment(self) -> str:
        """
        Launch a coding setup: VS Code + browser to localhost.
        """

        logger.info("Launching dev environment.")

        results = []

        # 1. Open VS Code
        try:
            result = self._assistant.app_ctrl.open_app("vscode")
            results.append(result)
        except Exception:
            results.append("Couldn't open VS Code.")

        time.sleep(2)

        # 2. Open browser to localhost
        try:
            import webbrowser
            webbrowser.open("http://localhost:3000")
            results.append("Opened browser to localhost:3000.")
        except Exception:
            results.append("Couldn't open browser.")

        return " ".join(results) + " Dev environment is ready!"

    # ══════════════════════════════════════════════════════════
    #  LinkedIn Job Search
    # ══════════════════════════════════════════════════════════

    def linkedin_job_search(self, job_title: str = "") -> str:
        """
        Open LinkedIn and search for jobs.
        """

        if not job_title:
            job_title = "Software Engineer"

        import webbrowser
        from urllib.parse import quote_plus

        url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={quote_plus(job_title)}"
            f"&f_AL=true"  # Easy Apply filter
        )

        webbrowser.open(url)

        return (
            f"Opened LinkedIn job search for '{job_title}' "
            f"with Easy Apply filter."
        )
