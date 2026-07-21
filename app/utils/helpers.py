"""
helpers.py
----------
Utility functions used across the application.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from rapidfuzz import fuzz, process


# ── Text Cleaning ────────────────────────────────────────────────

def sanitize_text(text: str) -> str:
    """
    Clean raw Whisper output.

    Strips leading/trailing whitespace, collapses multiple spaces,
    removes common Whisper hallucinations (e.g. "Thank you." when
    no speech was present).
    """

    if not text:
        return ""

    # common whisper hallucinations on silence
    hallucinations = {
        "thank you.",
        "thanks for watching.",
        "you",
        ".",
        "thank you for watching.",
        "the end.",
        "bye.",
        "thanks.",
        "thank you very much.",
        "subtitles by the amara.org community",
    }

    cleaned = text.strip()

    if cleaned.lower() in hallucinations:
        return ""

    # collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned


def extract_target(text: str, trigger_words: list[str]) -> str:
    """
    Extract the meaningful target from a command after removing
    the trigger words.

    Example
    -------
    >>> extract_target("open google chrome", ["open"])
    'google chrome'
    """

    lower = text.lower()

    for word in trigger_words:
        lower = lower.replace(word.lower(), "", 1)

    return lower.strip()


# ── Fuzzy Matching ───────────────────────────────────────────────

def fuzzy_match(
    query: str,
    choices: list[str],
    threshold: int = 65,
    limit: int = 1,
) -> list[tuple[str, int]]:
    """
    Find the closest matches to *query* from *choices*.

    Parameters
    ----------
    query : str
        The user's spoken text.
    choices : list[str]
        Known commands / names to match against.
    threshold : int
        Minimum similarity score (0–100).
    limit : int
        Max results to return.

    Returns
    -------
    list[tuple[str, int]]
        List of ``(matched_string, score)`` tuples.
    """

    if not query or not choices:
        return []

    results = process.extract(
        query.lower(),
        [c.lower() for c in choices],
        scorer=fuzz.WRatio,
        limit=limit,
    )

    return [
        (match, int(score))
        for match, score, _idx in results
        if score >= threshold
    ]


def best_match(
    query: str,
    choices: list[str],
    threshold: int = 65,
) -> Optional[str]:
    """Return the single best fuzzy match, or None."""

    matches = fuzzy_match(query, choices, threshold, limit=1)
    return matches[0][0] if matches else None


# ── Keyword Extraction ───────────────────────────────────────────

# Words that carry no actionable meaning
_STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "and",
    "but", "or", "so", "if", "then", "than", "that", "this",
    "it", "its", "my", "your", "me", "i", "you", "we", "they",
    "he", "she", "please", "just", "also", "very", "really",
    "hey", "hi", "hello", "aida", "okay", "ok",
}


def extract_keywords(text: str) -> list[str]:
    """
    Pull meaningful action/target words from a command.

    Removes stop words and returns remaining tokens in order.
    """

    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [w for w in words if w not in _STOP_WORDS]


# ── Path Helpers ─────────────────────────────────────────────────

def safe_path(path_str: str) -> Optional[Path]:
    """
    Validate and return a resolved Path, or None if invalid.
    """

    try:
        p = Path(path_str).resolve()

        if p.exists():
            return p

        return None

    except (OSError, ValueError):
        return None


def format_file_size(size_bytes: int) -> str:
    """Human-readable file size."""

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024

    return f"{size_bytes:.1f} PB"


def get_time_greeting() -> str:
    """Return a time-appropriate greeting key."""

    from datetime import datetime

    hour = datetime.now().hour

    if hour < 12:
        return "greeting_morning"

    if hour < 17:
        return "greeting_afternoon"

    return "greeting_evening"
