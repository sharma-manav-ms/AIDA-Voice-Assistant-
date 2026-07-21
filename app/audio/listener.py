"""
Microphone Stream
"""

from __future__ import annotations

import sounddevice as sd
from queue import Queue

from app.config.settings import (
    SAMPLE_RATE,
    CHANNELS,
    CHUNK_SIZE,
)

from app.utils.logger import get_logger

logger = get_logger(__name__)


class Listener:

    def __init__(self):

        self.queue = Queue()

    def callback(self, indata, frames, time, status):

        if status:
            logger.warning(status)

        self.queue.put(indata.copy())

    def stream(self):

        logger.info("Listening...")

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            blocksize=CHUNK_SIZE,
            callback=self.callback,
            dtype="float32",
        ):

            while True:
                yield self.queue.get()