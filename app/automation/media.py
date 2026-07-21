"""
media.py
--------
Media playback and information services.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import json
import subprocess
import webbrowser
from typing import Optional
from urllib.parse import quote_plus

from app.utils.constants import RESPONSES
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MediaController:
    """
    Media playback controls and information services.
    """

    # ══════════════════════════════════════════════════════════
    #  Spotify (keyboard simulation)
    # ══════════════════════════════════════════════════════════

    def play_spotify(self) -> str:
        """Open Spotify and start playback."""

        try:
            import pyautogui
            from app.automation.app_control import AppController

            ctrl = AppController()
            ctrl.open_app("spotify")

            # give Spotify time to open
            import time
            time.sleep(3)

            # send play/pause media key
            pyautogui.press("playpause")

            return "Playing music on Spotify."

        except Exception as exc:
            logger.error("Spotify play failed: %s", exc)
            return "Couldn't start Spotify playback."

    def pause_spotify(self) -> str:
        """Pause Spotify playback."""

        try:
            import pyautogui
            pyautogui.press("playpause")
            return "Music paused."

        except Exception:
            return "Couldn't pause music."

    def next_track(self) -> str:
        """Skip to next track."""

        try:
            import pyautogui
            pyautogui.press("nexttrack")
            return "Playing next track."

        except Exception:
            return "Couldn't skip track."

    def previous_track(self) -> str:
        """Go to previous track."""

        try:
            import pyautogui
            pyautogui.press("prevtrack")
            return "Playing previous track."

        except Exception:
            return "Couldn't go back."

    # ══════════════════════════════════════════════════════════
    #  YouTube
    # ══════════════════════════════════════════════════════════

    def play_youtube(self, query: str = "") -> str:
        """Play a video on YouTube."""

        if not query:
            return "What should I play on YouTube?"

        url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(query)
        )
        webbrowser.open(url)

        return RESPONSES["playing"].format(item=query + " on YouTube")

    # ══════════════════════════════════════════════════════════
    #  Weather
    # ══════════════════════════════════════════════════════════

    def get_weather(self, city: str = "") -> str:
        """
        Get current weather using wttr.in (no API key required).
        """

        if not city:
            city = ""  # wttr.in auto-detects location

        # strip common prefixes
        for prefix in ("in", "for", "at", "of", "weather"):
            city = city.replace(prefix, "").strip()

        try:
            import requests

            url = f"https://wttr.in/{quote_plus(city)}?format=j1"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            current = data.get("current_condition", [{}])[0]
            area = data.get("nearest_area", [{}])[0]

            temp_c = current.get("temp_C", "?")
            temp_f = current.get("temp_F", "?")
            desc = current.get("weatherDesc", [{}])[0].get("value", "")
            humidity = current.get("humidity", "?")
            feels_like = current.get("FeelsLikeC", "?")

            location = area.get("areaName", [{}])[0].get("value", city or "your location")

            return (
                f"In {location}, it's currently {temp_c} degrees Celsius "
                f"({temp_f} Fahrenheit), {desc.lower()}. "
                f"Feels like {feels_like} degrees. "
                f"Humidity is {humidity}%."
            )

        except Exception as exc:
            logger.error("Weather fetch failed: %s", exc)
            return "I couldn't get the weather right now."

    # ══════════════════════════════════════════════════════════
    #  News
    # ══════════════════════════════════════════════════════════

    def get_headlines(self, category: str = "") -> str:
        """
        Get top news headlines using Google News RSS.
        """

        try:
            import requests
            import xml.etree.ElementTree as ET

            url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            items = root.findall(".//item")

            if not items:
                return "I couldn't find any news headlines."

            headlines = []

            for item in items[:5]:
                title = item.find("title")
                if title is not None and title.text:
                    headlines.append(title.text)

            if not headlines:
                return "No headlines available right now."

            result = "Here are the top headlines: "
            for i, h in enumerate(headlines, 1):
                result += f"{i}. {h}. "

            return result

        except Exception as exc:
            logger.error("News fetch failed: %s", exc)
            return "I couldn't fetch the news right now."
