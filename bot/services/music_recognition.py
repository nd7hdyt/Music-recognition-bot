import aiohttp
import asyncio
import os
import urllib.parse
from bot.config import MUSIC_API_KEY, TEMP_DIR
from bot.services.metadata import SongData
from bot.utils.logger import get_logger

logger = get_logger(__name__)

AUDD_API_URL = "https://api.audd.io/"
DEEZER_API = "https://api.deezer.com"
JIOSAAVN_API = "https://www.jiosaavn.com/api.php"
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"


class MusicRecognitionService:
    def __init__(self):
        self.api_key = MUSIC_API_KEY

    async def recognize_file(self, file_path: str) -> SongData | None:
        if not self.api_key:
            logger.error("Audd API key not configured")
            return None

        try:
            with open(file_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("file", f, filename="audio.mp3", content_type="audio/mpeg")
                data.add_field("api_token", self.api_key)
                data.add_field("return", "spotify")

                timeout = aiohttp.ClientTimeout(total=20)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(AUDD_API_URL, data=data) as resp:
                        import json
                        result_text = await resp.text()
                        logger.info(f"Audd response status: {resp.status}")
                        logger.info(f"Audd response: {result_text[:500]}")
                        if resp.status == 200:
                            result = json.loads(result_text)
                            if result.get("result"):
                                return SongData.from_audd(result)
                        return None
        except Exception as e:
            logger.error(f"Recognition failed: {e}")
            return None

    async def search_deezer(self, title: str, artist: str) -> str | None:
        try:
            query = urllib.parse.quote(f"{artist} {title}")
            url = f"{DEEZER_API}/search?q={query}&limit=1"
            timeout = aiohttp.ClientTimeout(total=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        import json
                        data = json.loads(await resp.text())
                        tracks = data.get("data", [])
                        if tracks:
                            preview = tracks[0].get("preview", "")
                            if preview:
                                logger.info(f"Deezer preview found: {preview[:50]}")
                                return preview
        except Exception as e:
            logger.error(f"Deezer search failed: {e}")
        return ""

    async def search_jiosaavn(self, title: str, artist: str) -> str | None:
        try:
            query = urllib.parse.quote(f"{artist} {title}")
            url = f"{JIOSAAVN_API}?__call=autocomplete.get&_format=results&cc=in&includeMetaTags=1&query={query}"
            timeout = aiohttp.ClientTimeout(total=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        import json
                        data = json.loads(await resp.text())
                        songs = data.get("songs", {}).get("data", [])
                        if songs and songs[0].get("url"):
                            return songs[0]["url"]
        except Exception as e:
            logger.error(f"JioSaavn search failed: {e}")
        return ""

    async def search_itunes(self, title: str, artist: str) -> str | None:
        try:
            query = urllib.parse.quote(f"{artist} {title}")
            url = f"{ITUNES_SEARCH_URL}?term={query}&media=music&entity=song&limit=1"
            timeout = aiohttp.ClientTimeout(total=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        import json
                        data = json.loads(await resp.text())
                        results = data.get("results", [])
                        if results:
                            preview = results[0].get("previewUrl", "")
                            if preview:
                                logger.info(f"iTunes preview found: {preview[:50]}")
                                return preview
        except Exception as e:
            logger.error(f"iTunes search failed: {e}")
        return ""

    async def download_from_url(self, url: str) -> str | None:
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        import hashlib
                        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
                        filepath = str(TEMP_DIR / f"jiosaavn_{url_hash}.mp3")
                        with open(filepath, "wb") as f:
                            f.write(await resp.read())
                        if os.path.getsize(filepath) > 10000:
                            return filepath
                        else:
                            os.remove(filepath)
        except Exception as e:
            logger.error(f"URL download failed: {e}")
        return ""

    async def download_full_song(self, title: str, artist: str) -> str | None:
        import aiohttp
        import uuid

        cobalt_url = os.getenv("COBALT_API_URL", "").strip().rstrip("/")

        if cobalt_url:
            try:
                query = f"{artist} {title}"

                import yt_dlp
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "socket_timeout": 10,
                    "noplaylist": True,
                    "extract_flat": True,
                }

                loop = asyncio.get_event_loop()

                def _search():
                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                            if info and "entries" in info:
                                entries = [e for e in info["entries"] if e]
                                if entries:
                                    entry = entries[0]
                                    video_id = entry.get("id") or entry.get("url", "")
                                    if video_id:
                                        return f"https://www.youtube.com/watch?v={video_id}"
                    except Exception as e:
                        logger.warning(f"yt-dlp search failed: {e}")
                    return None

                video_url = await loop.run_in_executor(None, _search)

                if video_url:
                    headers = {
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "url": video_url,
                        "downloadMode": "audio",
                        "audioFormat": "mp3",
                    }

                    timeout = aiohttp.ClientTimeout(total=30)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(f"{cobalt_url}/", json=payload, headers=headers) as resp:
                            if resp.status == 200:
                                result = await resp.json()
                                download_url = result.get("url")
                                if download_url:
                                    filepath = str(TEMP_DIR / f"cobalt_{uuid.uuid4().hex[:8]}.mp3")
                                    async with session.get(download_url) as dl_resp:
                                        if dl_resp.status == 200:
                                            with open(filepath, "wb") as f:
                                                f.write(await dl_resp.read())
                                            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                                                logger.info(f"Cobalt downloaded: {filepath}")
                                                return filepath
                            logger.warning(f"Cobalt failed: {resp.status} {await resp.text()}")
            except Exception as e:
                logger.warning(f"Cobalt download failed: {e}")

        try:
            import yt_dlp

            query = f"{artist} {title} official"
            ydl_opts = {
                "format": "bestaudio[ext=mp3]/bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",
                }],
                "outtmpl": str(TEMP_DIR / "yt_%(id)s.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 10,
                "retries": 3,
                "geo_bypass": True,
                "no_check_certificates": True,
                "ignoreerrors": True,
                "noplaylist": True,
                "extractor_args": {"youtube": {"skip": ["dash"]}},
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            }

            loop = asyncio.get_event_loop()

            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                    if info and "entries" in info:
                        info = info["entries"][0]
                    return info

            info = await loop.run_in_executor(None, _download)

            if info:
                for f in TEMP_DIR.iterdir():
                    if f.suffix == ".mp3" and "yt_" in f.name:
                        return str(f)

            return None

        except Exception as e:
            logger.error(f"YouTube download failed: {e}")
            return None

    async def recognize_url(self, url: str) -> SongData | None:
        if not self.api_key:
            return None

        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                data = aiohttp.FormData()
                data.add_field("url", url)
                data.add_field("api_token", self.api_key)
                data.add_field("return", "spotify")

                async with session.post(AUDD_API_URL, data=data) as resp:
                    if resp.status == 200:
                        import json
                        result = json.loads(await resp.text())
                        if result.get("result"):
                            return SongData.from_audd(result)
                    return None
        except Exception as e:
            logger.error(f"URL recognition failed: {e}")
            return None
