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

import numpy as np
import speech_recognition as sr
import whisper

from app.config.settings import WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_FP16


class Listener:
    """
    Speech-to-Text Listener using Whisper.
    """

    def __init__(
        self,
        model_name: str = WHISPER_MODEL,
        energy_threshold: int = 300,
        pause_threshold: float = 0.8,
    ) -> None:

        self.logger = logging.getLogger(self.__class__.__name__)

        self.recognizer = sr.Recognizer()

        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold

        self.logger.info("Loading Whisper model: %s...", model_name)

        self.model = whisper.load_model(model_name)

        self.logger.info("Whisper model loaded successfully.")

    def listen(
        self,
        timeout: int = 5,
        phrase_time_limit: int = 10,
    ) -> Optional[str]:
        """
        Listen from microphone and return recognized text.

        Bypasses ffmpeg by passing float32 numpy audio directly to Whisper.

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

                # Extract 16kHz 16-bit PCM bytes and convert directly to float32 numpy array.
                # This avoids external calls to ffmpeg.
                raw_bytes = audio.get_raw_data(convert_rate=16000, convert_width=2)
                audio_np = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

                result = self.model.transcribe(
                    audio_np,
                    fp16=WHISPER_FP16,
                    language=WHISPER_LANGUAGE,
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