"""
Microphone Listener

Responsibility:
- Open microphone
- Record raw audio
- Return PCM bytes

This module DOES NOT:
- Recognize speech
- Detect voice
- Call AI
"""

from __future__ import annotations

import sounddevice as sd
from typing import Optional

from app.config.settings import (
    SAMPLE_RATE,
    CHANNELS,
    DEVICE_INDEX,
)

from app.utils.logger import get_logger


logger = get_logger(__name__)


class Listener:
    """
    Handles microphone recording only.
    """

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        channels: int = CHANNELS,
        device: Optional[int] = DEVICE_INDEX,
    ) -> None:

        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device

        logger.info("Listener initialized.")

    def listen(self, duration: float = 5.0):
        """
        Record raw microphone audio.

        Parameters
        ----------
        duration : float
            Recording duration in seconds.

        Returns
        -------
        numpy.ndarray
            Raw PCM audio.
        """

        logger.info("Recording started...")

        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            device=self.device,
        )

        sd.wait()

        logger.info("Recording finished.")

        return audio