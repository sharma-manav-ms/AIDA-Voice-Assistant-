"""
listener.py
-----------
Handles Speech-to-Text using Whisper.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import logging
from typing import Optional

import speech_recognition as sr
import whisper


class Listener:
    """
    Speech-to-Text Listener using Whisper.
    """

    def __init__(
        self,
        model_name: str = "large-v3",
        energy_threshold: int = 300,
        pause_threshold: float = 0.8,
    ) -> None:

        self.logger = logging.getLogger(self.__class__.__name__)

        self.recognizer = sr.Recognizer()

        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold

        self.logger.info("Loading Whisper model...")

        self.model = whisper.load_model(model_name)

        self.logger.info("Whisper model loaded successfully.")

    def listen(
        self,
        timeout: int = 5,
        phrase_time_limit: int = 10,
    ) -> Optional[str]:
        """
        Listen from microphone and return recognized text.

        Returns
        -------
        str | None
        """

        try:

            with sr.Microphone() as source:

                self.logger.info("Adjusting for ambient noise...")

                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=1
                )

                print("\n🎤 Listening...")

                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

                self.logger.info("Audio captured.")

                wav_file = "temp_audio.wav"

                with open(wav_file, "wb") as file:
                    file.write(audio.get_wav_data())

                result = self.model.transcribe(
                    wav_file,
                    fp16=False
                )

                text = result["text"].strip()

                self.logger.info("Recognized: %s", text)

                return text

        except sr.WaitTimeoutError:

            self.logger.warning("Listening timed out.")

            return None

        except Exception:

            self.logger.exception(
                "Speech recognition failed."
            )

            return None