"""
Application Entry Point
"""

from app.audio.listener import Listener


def main():

    listener = Listener()

    audio = listener.listen(duration=5)

    print(type(audio))
    print(audio.shape)


if __name__ == "__main__":
    main()