"""
file_manager.py
---------------
Search and manage local files via voice commands.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config.settings import FILE_SEARCH_EXTENSIONS, FUZZY_MATCH_THRESHOLD
from app.utils.constants import FOLDER_SHORTCUTS, RESPONSES
from app.utils.helpers import best_match, format_file_size, fuzzy_match
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FileManager:
    """
    File search and management via voice.

    Searches the user's Documents, Downloads, and Desktop folders
    by default, using fuzzy filename matching.
    """

    SEARCH_DIRS: list[Path] = [
        FOLDER_SHORTCUTS["documents"],
        FOLDER_SHORTCUTS["downloads"],
        FOLDER_SHORTCUTS["desktop"],
    ]

    def __init__(self) -> None:
        pass

    # ══════════════════════════════════════════════════════════
    #  Search
    # ══════════════════════════════════════════════════════════

    def find_files(self, query: str = "") -> str:
        """
        Fuzzy search for files matching *query*.

        Returns a spoken summary of the top results.
        """

        if not query:
            return "What file are you looking for?"

        query = query.strip()
        results = self._search(query)

        if not results:
            return RESPONSES["file_not_found"].format(query=query)

        count = len(results)

        if count == 1:
            f = results[0]
            return (
                f"I found {f.name} in {f.parent.name}. "
                f"Size: {format_file_size(f.stat().st_size)}."
            )

        top = results[:5]
        names = ", ".join(f.name for f in top)

        return (
            RESPONSES["file_found"].format(count=count)
            + f" Top matches: {names}."
        )

    def find_by_type(self, file_type: str = "") -> str:
        """
        Find files by type (pdf, word, image, etc.).
        """

        if not file_type:
            return "What type of files should I look for?"

        file_type = file_type.strip().lower()

        # strip prefix words
        for word in ("find", "all", "files", "my"):
            file_type = file_type.replace(word, "").strip()

        # match to known extensions
        extensions = FILE_SEARCH_EXTENSIONS.get(file_type)

        if extensions is None:
            # try fuzzy match against type names
            matched = best_match(
                file_type,
                list(FILE_SEARCH_EXTENSIONS.keys()),
                threshold=60,
            )
            if matched:
                extensions = FILE_SEARCH_EXTENSIONS[matched]
                file_type = matched

        if extensions is None:
            return f"I don't know the file type '{file_type}'."

        results = []

        for search_dir in self.SEARCH_DIRS:
            if not search_dir.exists():
                continue

            for root, _, files in os.walk(search_dir):
                for f in files:
                    if any(f.lower().endswith(ext) for ext in extensions):
                        results.append(Path(root) / f)

        if not results:
            return f"I couldn't find any {file_type} files."

        count = len(results)
        top = results[:5]
        names = ", ".join(f.name for f in top)

        return f"I found {count} {file_type} files. Here are some: {names}."

    # ══════════════════════════════════════════════════════════
    #  File Operations
    # ══════════════════════════════════════════════════════════

    def open_file_by_name(self, name: str = "") -> str:
        """Find and open a file by name."""

        if not name:
            return "Which file should I open?"

        results = self._search(name.strip())

        if not results:
            return RESPONSES["file_not_found"].format(query=name)

        target = results[0]

        try:
            os.startfile(str(target))
            logger.info("Opened file: %s", target)
            return f"Opening {target.name}."

        except Exception as exc:
            return f"Couldn't open {target.name}: {exc}"

    def delete_file_by_name(self, name: str = "") -> str:
        """Find and delete a file by name."""

        if not name:
            return "Which file should I delete?"

        results = self._search(name.strip())

        if not results:
            return RESPONSES["file_not_found"].format(query=name)

        target = results[0]

        try:
            target.unlink()
            logger.info("Deleted: %s", target)
            return RESPONSES["file_deleted"].format(name=target.name)

        except Exception as exc:
            return f"Couldn't delete {target.name}: {exc}"

    def rename_file(self, old_path: Path, new_name: str) -> str:
        """Rename a file."""

        try:
            new_path = old_path.parent / new_name
            old_path.rename(new_path)
            return f"Renamed {old_path.name} to {new_name}."

        except Exception as exc:
            return f"Couldn't rename: {exc}"

    def copy_file(self, src: Path, dst: Path) -> str:
        """Copy a file."""

        try:
            shutil.copy2(str(src), str(dst))
            return f"Copied {src.name} to {dst}."

        except Exception as exc:
            return f"Couldn't copy: {exc}"

    def move_file(self, src: Path, dst: Path) -> str:
        """Move a file."""

        try:
            shutil.move(str(src), str(dst))
            return f"Moved {src.name} to {dst}."

        except Exception as exc:
            return f"Couldn't move: {exc}"

    # ══════════════════════════════════════════════════════════
    #  Recent Files
    # ══════════════════════════════════════════════════════════

    def get_recent_files_summary(self, n: int = 10) -> str:
        """List the most recently modified files."""

        all_files: list[tuple[Path, float]] = []

        for search_dir in self.SEARCH_DIRS:
            if not search_dir.exists():
                continue

            for root, _, files in os.walk(search_dir):
                depth = root.replace(str(search_dir), "").count(os.sep)
                if depth > 2:  # limit depth
                    continue

                for f in files:
                    p = Path(root) / f
                    try:
                        mtime = p.stat().st_mtime
                        all_files.append((p, mtime))
                    except OSError:
                        pass

        if not all_files:
            return "I couldn't find any recent files."

        all_files.sort(key=lambda x: x[1], reverse=True)
        top = all_files[:n]

        names = ", ".join(p.name for p, _ in top)
        return f"Recent files: {names}."

    # ══════════════════════════════════════════════════════════
    #  Internal
    # ══════════════════════════════════════════════════════════

    def _search(
        self,
        query: str,
        max_results: int = 20,
    ) -> list[Path]:
        """
        Walk search directories and fuzzy-match filenames.
        """

        candidates: list[tuple[Path, int]] = []

        for search_dir in self.SEARCH_DIRS:
            if not search_dir.exists():
                continue

            for root, _, files in os.walk(search_dir):
                depth = root.replace(str(search_dir), "").count(os.sep)
                if depth > 3:  # limit recursion depth
                    continue

                for f in files:
                    # skip hidden / system files
                    if f.startswith(".") or f.startswith("~"):
                        continue

                    matches = fuzzy_match(
                        query,
                        [f, Path(f).stem],
                        threshold=FUZZY_MATCH_THRESHOLD,
                        limit=1,
                    )

                    if matches:
                        score = matches[0][1]
                        candidates.append((Path(root) / f, score))

        # sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        return [p for p, _ in candidates[:max_results]]
