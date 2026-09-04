import aiohttp
import asyncio
from bot.services.metadata import SongData, ArtistData
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class MusicSearchService:
    ITUNES_SEARCH = "https://itunes.apple.com/search"
    ITUNES_LOOKUP = "https://itunes.apple.com/lookup"

    @staticmethod
    async def search_song(query: str, limit: int = 5) -> list[SongData]:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                params = {
                    "term": query,
                    "media": "music",
                    "entity": "song",
                    "limit": limit,
                }
                async with session.get(MusicSearchService.ITUNES_SEARCH, params=params) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        import json
                        data = json.loads(text)
                        results = []
                        for item in data.get("results", []):
                            results.append(SongData(
                                title=item.get("trackName", "Unknown"),
                                artist=item.get("artistName", "Unknown"),
                                album=item.get("collectionName", ""),
                                release_date=item.get("releaseDate", "")[:4],
                                duration=item.get("trackTimeMillis", 0) // 1000,
                                preview_url=item.get("previewUrl", ""),
                                album_art=item.get("artworkUrl100", "").replace("100x100", "600x600"),
                                provider="itunes",
                            ))
                        return results
        except Exception as e:
            logger.error(f"Song search failed: {e}")
        return []

    @staticmethod
    async def search_artist(artist_name: str, limit: int = 1) -> ArtistData | None:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                params = {
                    "term": artist_name,
                    "entity": "musicArtist",
                    "limit": limit,
                }
                async with session.get(MusicSearchService.ITUNES_SEARCH, params=params) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        import json
                        data = json.loads(text)
                        results = data.get("results", [])
                        if results:
                            artist = results[0]
                            artist_id = artist.get("artistId")
                            top_songs = await MusicSearchService._get_artist_top_songs(session, artist_id)
                            return ArtistData(
                                name=artist.get("artistName", "Unknown"),
                                image_url=artist.get("artworkUrl100", "").replace("100x100", "600x600"),
                                listeners=str(artist.get("primaryGenreName", "")),
                                top_songs=top_songs,
                            )
        except Exception as e:
            logger.error(f"Artist search failed: {e}")
        return None

    @staticmethod
    async def _get_artist_top_songs(session: aiohttp.ClientSession, artist_id: int, limit: int = 5) -> list[SongData]:
        try:
            params = {
                "id": artist_id,
                "entity": "song",
                "limit": limit + 5,
                "sort": "popularity",
            }
            async with session.get(MusicSearchService.ITUNES_LOOKUP, params=params) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    import json
                    data = json.loads(text)
                    songs = []
                    for item in data.get("results", []):
                        if item.get("wrapperType") == "track":
                            songs.append(SongData(
                                title=item.get("trackName", "Unknown"),
                                artist=item.get("artistName", "Unknown"),
                                album=item.get("collectionName", ""),
                                duration=item.get("trackTimeMillis", 0) // 1000,
                                preview_url=item.get("previewUrl", ""),
                                album_art=item.get("artworkUrl100", "").replace("100x100", "600x600"),
                            ))
                            if len(songs) >= limit:
                                break
                    return songs
        except Exception as e:
            logger.error(f"Top songs fetch failed: {e}")
        return []

    @staticmethod
    async def get_trending() -> list[SongData]:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                params = {
                    "term": "top hits 2024",
                    "media": "music",
                    "entity": "song",
                    "limit": 10,
                }
                async with session.get(MusicSearchService.ITUNES_SEARCH, params=params) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        import json
                        data = json.loads(text)
                        results = []
                        for item in data.get("results", []):
                            results.append(SongData(
                                title=item.get("trackName", "Unknown"),
                                artist=item.get("artistName", "Unknown"),
                                album=item.get("collectionName", ""),
                                release_date=item.get("releaseDate", "")[:4],
                                duration=item.get("trackTimeMillis", 0) // 1000,
                                preview_url=item.get("previewUrl", ""),
                                album_art=item.get("artworkUrl100", "").replace("100x100", "600x600"),
                            ))
                        return results
        except Exception as e:
            logger.error(f"Trending fetch failed: {e}")
        return []
