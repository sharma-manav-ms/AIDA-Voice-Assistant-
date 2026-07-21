import logging

from assistant.speaker import Speaker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

speaker = Speaker()

speaker.speak(
    "Hello! I am AIDA. Your AI Desktop Assistant."
)