import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

if (BASE_DIR / ".env").exists():
    load_dotenv(BASE_DIR / ".env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
MUSIC_API_KEY = os.getenv("MUSIC_API_KEY", "")
LYRICS_API_KEY = os.getenv("LYRICS_API_KEY", "")
ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i.strip().isdigit()]
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'musicbot.db'}")

TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024
AUDIO_FORMATS = ["mp3", "wav", "ogg", "flac", "m4a", "aac"]
VIDEO_FORMATS = ["mp4", "avi", "mkv", "mov", "webm", "gif"]
PROCESSING_TIMEOUT = 30
RECOGNITION_TIMEOUT = 30
MAX_RECONGNITIONS_PER_DAY = 50
MAX_SEARCH_RESULTS = 10
SONGS_PER_PAGE = 5

RECOGNITION_CLIP_SECONDS = 12
