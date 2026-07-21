"""
validators.py
-------------
Input validation utilities.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse


def validate_email(email: str) -> bool:
    """
    Basic RFC-style email validation.

    Parameters
    ----------
    email : str
        Email address to validate.

    Returns
    -------
    bool
        True if the email looks valid.
    """

    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_file_path(path: str) -> bool:
    """
    Check that a path string resolves to an existing file.
    """

    try:
        return Path(path).resolve().is_file()

    except (OSError, ValueError):
        return False


def validate_dir_path(path: str) -> bool:
    """
    Check that a path string resolves to an existing directory.
    """

    try:
        return Path(path).resolve().is_dir()

    except (OSError, ValueError):
        return False


def validate_url(url: str) -> bool:
    """
    Basic URL validation — checks scheme and netloc.
    """

    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])

    except Exception:
        return False


def sanitize_filename(name: str) -> str:
    """
    Remove or replace characters that are invalid in Windows filenames.
    """

    # characters illegal in Windows filenames
    illegal = r'[<>:"/\\|?*]'
    cleaned = re.sub(illegal, "_", name)

    # collapse runs of underscores
    cleaned = re.sub(r"_+", "_", cleaned)

    return cleaned.strip("_. ")
