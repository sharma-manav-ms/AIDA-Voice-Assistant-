print("AI Desktop Assistant setup successful!")

import logging

from assistant.listener import Listener
from assistant.speaker import Speaker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

speaker = Speaker()
listener = Listener()

speaker.speak("Hello! I am AIDA.")

while True:

    text = listener.listen()

    if text is None:
        continue

    print(f"\nYou : {text}")

    speaker.speak(f"You said {text}")

    if text.lower() == "exit":
        speaker.speak("Goodbye.")
        break