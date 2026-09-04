import aiohttp
import asyncio
from bot.config import LYRICS_API_KEY
from bot.services.metadata import SongData
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class LyricsService:
    def __init__(self):
        self.api_key = LYRICS_API_KEY

    async def search_by_lyrics(self, lyrics: str) -> SongData | None:
        try:
            import urllib.parse
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                encoded_term = urllib.parse.quote(lyrics)
                async with session.get(
                    f"https://api.lyrics.ovh/suggest/{encoded_term}"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("data"):
                            song = data["data"][0]
                            return SongData(
                                title=song.get("title", "Unknown"),
                                artist=song.get("artist", {}).get("name", "Unknown"),
                                preview_url=song.get("preview", ""),
                                album_art=song.get("artist", {}).get("picture", ""),
                                provider="lyrics",
                            )
        except Exception as e:
            logger.error(f"Lyrics search failed: {e}")

        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                params = {"q_instrumental": 0, "q_track": "", "q_artist": ""}
                headers = {"apikey": self.api_key} if self.api_key else {}
                async with session.get(
                    "https://api.genius.com/search",
                    params={"q": lyrics},
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        hits = data.get("response", {}).get("hits", [])
                        if hits:
                            hit = hits[0]["result"]
                            return SongData(
                                title=hit.get("title", "Unknown"),
                                artist=hit.get("primary_artist", {}).get("name", "Unknown"),
                                provider="genius",
                            )
        except Exception as e:
            logger.error(f"Genius search failed: {e}")

        return None
