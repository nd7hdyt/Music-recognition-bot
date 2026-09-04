import aiosqlite
from pathlib import Path
from bot.config import BASE_DIR
from bot.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = BASE_DIR / "data" / "musicbot.db"
_db_connection = None


async def get_db() -> aiosqlite.Connection:
    global _db_connection
    if _db_connection is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _db_connection = await aiosqlite.connect(str(DB_PATH))
        _db_connection.row_factory = aiosqlite.Row
    return _db_connection


async def close_db():
    global _db_connection
    if _db_connection is not None:
        await _db_connection.close()
        _db_connection = None
        logger.info("Database connection closed")


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                language TEXT DEFAULT 'en',
                auto_save INTEGER DEFAULT 0,
                notifications INTEGER DEFAULT 1,
                preferred_platform TEXT DEFAULT 'youtube',
                results_count INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS songs (
                song_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                album TEXT DEFAULT '',
                release_date TEXT DEFAULT '',
                genre TEXT DEFAULT '',
                duration INTEGER DEFAULT 0,
                preview_url TEXT DEFAULT '',
                youtube_url TEXT DEFAULT '',
                album_art TEXT DEFAULT '',
                provider TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, artist)
            );

            CREATE TABLE IF NOT EXISTS playlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                song_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (song_id) REFERENCES songs(song_id),
                UNIQUE(user_id, song_id)
            );

            CREATE TABLE IF NOT EXISTS recognition_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                song_id INTEGER,
                recognized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'voice',
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (song_id) REFERENCES songs(song_id)
            );

            CREATE INDEX IF NOT EXISTS idx_playlist_user ON playlist(user_id);
            CREATE INDEX IF NOT EXISTS idx_history_user ON recognition_history(user_id);
            CREATE INDEX IF NOT EXISTS idx_history_date ON recognition_history(recognized_at);
            CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title);
            CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs(artist);
        """)
        await db.commit()
    logger.info("Database initialized successfully")
