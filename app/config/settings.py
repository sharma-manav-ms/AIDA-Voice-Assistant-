"""
settings.py
-----------
Application-wide constants and default values.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

# ── Audio ────────────────────────────────────────────────────────

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 512

DEVICE_INDEX = None

# ── VAD ──────────────────────────────────────────────────────────

SPEECH_PADDING_MS = 200
MIN_SILENCE_MS = 800
SILENCE_CHUNKS_THRESHOLD = 20  # chunks of silence before speech ends

# ── Whisper ──────────────────────────────────────────────────────

WHISPER_MODEL = "base"  # tiny | base | small | medium | large-v3
WHISPER_LANGUAGE = "en"
WHISPER_FP16 = False

# ── TTS ──────────────────────────────────────────────────────────

TTS_RATE = 170         # words per minute
TTS_VOLUME = 1.0       # 0.0 to 1.0
TTS_VOICE_INDEX = 1    # 0 = male (usually), 1 = female

# ── LLM ──────────────────────────────────────────────────────────

LLM_PROVIDER = "gemini"          # gemini | openai
GEMINI_MODEL = "gemini-2.0-flash"
OPENAI_MODEL = "gpt-4.1-nano"
LLM_MAX_TOKENS = 1024
LLM_TEMPERATURE = 0.7
LLM_MAX_HISTORY_TURNS = 20

# ── Desktop Automation ───────────────────────────────────────────

VOLUME_STEP = 10       # percentage per step
BRIGHTNESS_STEP = 10   # percentage per step

SCREENSHOT_FORMAT = "png"

# ── File Manager ─────────────────────────────────────────────────

FILE_SEARCH_EXTENSIONS = {
    "pdf":   [".pdf"],
    "word":  [".doc", ".docx"],
    "excel": [".xls", ".xlsx"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "video": [".mp4", ".avi", ".mkv", ".mov"],
    "audio": [".mp3", ".wav", ".flac", ".aac"],
    "code":  [".py", ".js", ".java", ".cpp", ".html", ".css"],
}

FUZZY_MATCH_THRESHOLD = 65  # minimum score for RapidFuzz matches

# ── Email ────────────────────────────────────────────────────────

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# ── Productivity ─────────────────────────────────────────────────

MAX_NOTES = 500
MAX_TODOS = 200
REMINDER_CHECK_INTERVAL = 30  # seconds

# ── GUI ──────────────────────────────────────────────────────────

APP_NAME = "AIDA"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600
DEFAULT_THEME = "dark"