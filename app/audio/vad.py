from __future__ import annotations

import numpy as np
import torch

from silero_vad import (
    load_silero_vad,
    get_speech_timestamps,
)

from app.config.settings import SAMPLE_RATE
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VoiceActivityDetector:

    def __init__(self):

        logger.info("Loading Silero VAD...")

        self.model = load_silero_vad()

        logger.info("Silero VAD Loaded.")

    def is_speech(self, audio: np.ndarray) -> bool:
        """
        Check whether a chunk contains speech.
        """

        audio_tensor = torch.from_numpy(
            audio.flatten()
        ).float()

        timestamps = get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=SAMPLE_RATE,
        )

        return len(timestamps) > 0

    def collect_speech(self, stream):

        speech_chunks = []

        recording = False

        silence = 0

        logger.info("Waiting for speech...")

        for chunk in stream:

            if self.is_speech(chunk):

                if not recording:

                    logger.info("Speech Started")

                recording = True

                silence = 0

                speech_chunks.append(chunk)

            elif recording:

                silence += 1

                speech_chunks.append(chunk)

                if silence > 20:

                    logger.info("Speech Ended")

                    break

        return np.concatenate(
            speech_chunks,
            axis=0
        )