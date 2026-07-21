"""
Application configuration settings.
"""

from pathlib import Path

# Project Root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Audio Configuration
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024

# Recording
MAX_RECORD_SECONDS = 10
DEVICE_INDEX = None

# Logging
LOG_LEVEL = "INFO"