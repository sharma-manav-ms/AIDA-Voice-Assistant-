"""
test_speaker.py
---------------
Test text-to-speech speaker module.
"""

import logging
from app.assistant.speaker import Speaker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def test_speaker_init():
    speaker = Speaker()
    assert speaker.engine is not None