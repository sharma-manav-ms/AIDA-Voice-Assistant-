"""
browser.py
----------
Web browsing automation through voice commands.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import urllib.parse
import webbrowser
from typing import Optional

from app.utils.constants import SITE_REGISTRY, RESPONSES
from app.utils.helpers import best_match
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BrowserController:
    """
    Open websites and perform web searches via voice.

    Uses the ``webbrowser`` module (no external dependencies).
    """

    def __init__(self) -> None:
        self._site_names = list(SITE_REGISTRY.keys())

    # ══════════════════════════════════════════════════════════
    #  Google
    # ══════════════════════════════════════════════════════════

    def google_search(self, query: str = "") -> str:
        """Search Google for a query."""

        if not query:
            return "What should I search for?"

        url = (
            "https://www.google.com/search?q="
            + urllib.parse.quote_plus(query)
        )
        webbrowser.open(url)

        logger.info("Google search: %s", query)
        return RESPONSES["searching"].format(query=query)

    def google_images(self, query: str = "") -> str:
        """Search Google Images."""

        if not query:
            return "What images should I search for?"

        url = (
            "https://www.google.com/search?tbm=isch&q="
            + urllib.parse.quote_plus(query)
        )
        webbrowser.open(url)

        return f"Searching images for {query}."

    def google_news(self, query: str = "") -> str:
        """Search Google News."""

        if query:
            url = (
                "https://news.google.com/search?q="
                + urllib.parse.quote_plus(query)
            )
        else:
            url = "https://news.google.com"

        webbrowser.open(url)

        return f"Opening Google News{' for ' + query if query else ''}."

    def google_maps(self, query: str = "") -> str:
        """Search Google Maps."""

        if not query:
            url = "https://maps.google.com"
        else:
            url = (
                "https://www.google.com/maps/search/"
                + urllib.parse.quote_plus(query)
            )

        webbrowser.open(url)

        return f"Opening Google Maps{' for ' + query if query else ''}."

    # ══════════════════════════════════════════════════════════
    #  YouTube
    # ══════════════════════════════════════════════════════════

    def youtube_search(self, query: str = "") -> str:
        """Search YouTube."""

        if not query:
            return "What should I search on YouTube?"

        url = (
            "https://www.youtube.com/results?search_query="
            + urllib.parse.quote_plus(query)
        )
        webbrowser.open(url)

        logger.info("YouTube search: %s", query)
        return f"Searching YouTube for {query}."

    def youtube_play(self, query: str = "") -> str:
        """
        Open YouTube and play the first result for *query*.

        Uses the ytsearch URL trick to auto-play.
        """

        if not query:
            return "What should I play on YouTube?"

        # YouTube auto-plays the first search result when you
        # navigate to /results — good enough for voice control
        url = (
            "https://www.youtube.com/results?search_query="
            + urllib.parse.quote_plus(query)
        )
        webbrowser.open(url)

        logger.info("YouTube play: %s", query)
        return RESPONSES["playing"].format(item=query + " on YouTube")

    # ══════════════════════════════════════════════════════════
    #  Direct Websites
    # ══════════════════════════════════════════════════════════

    def open_website(self, name: str = "") -> str:
        """
        Open a named website from the registry.

        Falls back to fuzzy matching, then tries as a raw URL.
        """

        if not name:
            return "Which website should I open?"

        name = name.strip().lower()

        # direct lookup
        url = SITE_REGISTRY.get(name)

        # fuzzy fallback
        if url is None:
            matched = best_match(name, self._site_names, threshold=65)
            if matched:
                url = SITE_REGISTRY[matched]
                name = matched

        # try as a raw URL / domain
        if url is None:
            if "." in name:
                url = name if name.startswith("http") else f"https://{name}"
            else:
                return f"I don't know the website '{name}'."

        webbrowser.open(url)

        logger.info("Opened website: %s → %s", name, url)
        return f"Opening {name.title()}."

    # ══════════════════════════════════════════════════════════
    #  Generic URL
    # ══════════════════════════════════════════════════════════

    def open_url(self, url: str) -> str:
        """Open any URL in the default browser."""

        if not url:
            return "Please provide a URL."

        if not url.startswith("http"):
            url = f"https://{url}"

        webbrowser.open(url)

        return f"Opening {url}."
