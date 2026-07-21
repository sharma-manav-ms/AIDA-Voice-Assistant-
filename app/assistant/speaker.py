"""
speaker.py
-----------
Handles Text-to-Speech (TTS) functionality for the AI Desktop Assistant.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import logging
from typing import Optional

import pyttsx3


class Speaker:
    """
    Text-to-Speech engine wrapper.

    This class provides a simple interface for speaking text while
    encapsulating all pyttsx3 configuration.
    """

    def __init__(
        self,
        rate: int = 170,
        volume: float = 1.0,
        voice_index: int = 0,
    ) -> None:
        """
        Initialize the speech engine.

        Parameters
        ----------
        rate : int
            Speech speed in words per minute.

        volume : float
            Volume between 0.0 and 1.0.

        voice_index : int
            Voice to use from installed system voices.
        """

        self.logger = logging.getLogger(self.__class__.__name__)

        try:
            self.engine = pyttsx3.init()

            self.engine.setProperty("rate", rate)
            self.engine.setProperty("volume", volume)

            voices = self.engine.getProperty("voices")

            if voices and voice_index < len(voices):
                self.engine.setProperty(
                    "voice",
                    voices[voice_index].id,
                )

            self.logger.info("Speaker initialized successfully.")

        except Exception as error:
            self.logger.exception(
                "Failed to initialize speech engine."
            )
            raise RuntimeError(
                "Unable to initialize TTS engine."
            ) from error

    def speak(self, text: str) -> None:
        """
        Convert text into speech.

        Parameters
        ----------
        text : str
            Text to be spoken.
        """

        if not text.strip():
            self.logger.warning(
                "Empty text received for speech."
            )
            return

        self.logger.info("Speaking: %s", text)

        try:
            self.engine.say(text)
            self.engine.runAndWait()

        except Exception:
            self.logger.exception(
                "Speech synthesis failed."
            )

    def stop(self) -> None:
        """
        Stop any ongoing speech.
        """

        try:
            self.engine.stop()

        except Exception:
            self.logger.exception(
                "Unable to stop speech engine."
            )

    def list_voices(self) -> None:
        """
        Print all installed system voices.
        """

        voices = self.engine.getProperty("voices")

        print("\nInstalled Voices\n")

        for index, voice in enumerate(voices):
            print("-" * 40)
            print(f"Index : {index}")
            print(f"Name  : {voice.name}")
            print(f"ID    : {voice.id}")
            print(f"Lang  : {voice.languages}")
            print()

    def change_voice(self, index: int) -> bool:
        """
        Change voice by index.

        Returns
        -------
        bool
            True if successful.
        """

        voices = self.engine.getProperty("voices")

        if index >= len(voices):
            self.logger.error("Invalid voice index.")
            return False

        self.engine.setProperty(
            "voice",
            voices[index].id,
        )

        self.logger.info("Voice changed.")

        return True