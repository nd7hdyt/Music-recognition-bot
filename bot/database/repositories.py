from datetime import datetime, timedelta
from bot.database.database import get_db
from bot.database.models import User, Song, PlaylistItem, RecognitionRecord
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class UserRepository:
    @staticmethod
    async def get_or_create(user_id: int, username: str = None, first_name: str = None) -> User:
        db = await get_db()
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP, username = ?, first_name = ? WHERE user_id = ?",
                (username, first_name, user_id)
            )
            await db.commit()
            return User(**dict(row))
        await db.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()
        return User(user_id=user_id, username=username, first_name=first_name)

    @staticmethod
    async def update_settings(user_id: int, **kwargs):
        db = await get_db()
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in ("language", "auto_save", "notifications", "preferred_platform", "results_count"):
                sets.append(f"{k} = ?")
                vals.append(v)
        if sets:
            vals.append(user_id)
            await db.execute(f"UPDATE users SET {', '.join(sets)} WHERE user_id = ?", vals)
            await db.commit()

    @staticmethod
    async def get_all_user_ids() -> list[int]:
        db = await get_db()
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


class SongRepository:
    @staticmethod
    async def get_or_create(title: str, artist: str, **kwargs) -> Song:
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM songs WHERE title = ? AND artist = ?",
            (title, artist)
        )
        row = await cursor.fetchone()
        if row:
            return Song(**dict(row))
        cols = ["title", "artist"]
        vals = [title, artist]
        for k, v in kwargs.items():
            if v and k in ("album", "release_date", "genre", "duration", "preview_url", "youtube_url", "album_art", "provider"):
                cols.append(k)
                vals.append(v)
        placeholders = ", ".join(["?" for _ in cols])
        col_names = ", ".join(cols)
        await db.execute(f"INSERT INTO songs ({col_names}) VALUES ({placeholders})", vals)
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM songs WHERE title = ? AND artist = ?", (title, artist)
        )
        row = await cursor.fetchone()
        return Song(**dict(row)) if row else Song(title=title, artist=artist)

    @staticmethod
    async def search(query: str, limit: int = 10) -> list[Song]:
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM songs WHERE title LIKE ? OR artist LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        )
        rows = await cursor.fetchall()
        return [Song(**dict(row)) for row in rows]

    @staticmethod
    async def get_by_id(song_id: int) -> Song | None:
        db = await get_db()
        cursor = await db.execute("SELECT * FROM songs WHERE song_id = ?", (song_id,))
        row = await cursor.fetchone()
        return Song(**dict(row)) if row else None


class PlaylistRepository:
    @staticmethod
    async def add(user_id: int, song_id: int) -> bool:
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO playlist (user_id, song_id) VALUES (?, ?)",
                (user_id, song_id)
            )
            await db.commit()
            return True
        except Exception:
            return False

    @staticmethod
    async def remove(user_id: int, song_id: int) -> bool:
        db = await get_db()
        await db.execute(
            "DELETE FROM playlist WHERE user_id = ? AND song_id = ?",
            (user_id, song_id)
        )
        await db.commit()
        return True

    @staticmethod
    async def get_user_playlist(user_id: int, offset: int = 0, limit: int = 5) -> tuple[list[PlaylistItem], int]:
        db = await get_db()
        cursor = await db.execute(
            "SELECT COUNT(*) FROM playlist WHERE user_id = ?", (user_id,)
        )
        total = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """SELECT p.id, p.user_id, p.song_id, p.added_at,
               s.title, s.artist, s.album, s.release_date, s.genre,
               s.duration, s.preview_url, s.youtube_url, s.album_art
               FROM playlist p
               JOIN songs s ON p.song_id = s.song_id
               WHERE p.user_id = ?
               ORDER BY p.added_at DESC
               LIMIT ? OFFSET ?""",
            (user_id, limit, offset)
        )
        rows = await cursor.fetchall()
        items = []
        for row in rows:
            row_dict = dict(row)
            song = Song(
                title=row_dict["title"], artist=row_dict["artist"],
                album=row_dict["album"], release_date=row_dict["release_date"],
                genre=row_dict["genre"], duration=row_dict["duration"],
                preview_url=row_dict["preview_url"], youtube_url=row_dict["youtube_url"],
                album_art=row_dict["album_art"]
            )
            items.append(PlaylistItem(
                id=row_dict["id"], user_id=row_dict["user_id"],
                song_id=row_dict["song_id"], added_at=row_dict["added_at"],
                song=song
            ))
        return items, total

    @staticmethod
    async def is_saved(user_id: int, song_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "SELECT 1 FROM playlist WHERE user_id = ? AND song_id = ?",
            (user_id, song_id)
        )
        return await cursor.fetchone() is not None


class HistoryRepository:
    @staticmethod
    async def add(user_id: int, song_id: int, source: str = "voice"):
        db = await get_db()
        await db.execute(
            "INSERT INTO recognition_history (user_id, song_id, source) VALUES (?, ?, ?)",
            (user_id, song_id, source)
        )
        await db.commit()

    @staticmethod
    async def get_user_history(user_id: int, limit: int = 10) -> list[RecognitionRecord]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT h.id, h.user_id, h.song_id, h.recognized_at, h.source,
               s.title, s.artist, s.album, s.release_date
               FROM recognition_history h
               LEFT JOIN songs s ON h.song_id = s.song_id
               WHERE h.user_id = ?
               ORDER BY h.recognized_at DESC
               LIMIT ?""",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        records = []
        for row in rows:
            row_dict = dict(row)
            song = None
            if row_dict["title"]:
                song = Song(
                    title=row_dict["title"], artist=row_dict["artist"],
                    album=row_dict["album"], release_date=row_dict["release_date"]
                )
            records.append(RecognitionRecord(
                id=row_dict["id"], user_id=row_dict["user_id"],
                song_id=row_dict["song_id"], recognized_at=row_dict["recognized_at"],
                source=row_dict["source"], song=song
            ))
        return records

    @staticmethod
    async def get_stats() -> dict:
        db = await get_db()
        stats = {}

        cursor = await db.execute("SELECT COUNT(*) FROM users")
        stats["total_users"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM recognition_history")
        stats["total_recognitions"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM songs")
        stats["total_songs"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM playlist")
        stats["total_saved"] = (await cursor.fetchone())[0]

        today = datetime.now().strftime("%Y-%m-%d")
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE DATE(last_active) = ?", (today,)
        )
        stats["users_today"] = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM recognition_history WHERE DATE(recognized_at) = ?",
            (today,)
        )
        stats["recognitions_today"] = (await cursor.fetchone())[0]

        return stats
