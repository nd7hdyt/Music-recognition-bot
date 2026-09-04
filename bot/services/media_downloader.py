import aiohttp
import asyncio
import re
from urllib.parse import urlparse
from bot.config import TEMP_DIR
from bot.utils.logger import get_logger
from bot.utils.audio import extract_audio
from bot.utils.cleanup import cleanup_file

logger = get_logger(__name__)

SUPPORTED_DOMAINS = {
    "youtube.com", "youtu.be", "www.youtube.com", "m.youtube.com",
    "instagram.com", "www.instagram.com",
    "tiktok.com", "www.tiktok.com", "vm.tiktok.com",
    "facebook.com", "www.facebook.com", "fb.watch",
    "twitter.com", "www.twitter.com", "x.com", "www.x.com",
    "pinterest.com", "www.pinterest.com",
    "soundcloud.com", "www.soundcloud.com",
    "spotify.com", "open.spotify.com",
}


class MediaDownloader:
    @staticmethod
    def is_supported_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().lstrip("www.")
            return any(d in domain or domain.endswith("." + d.lstrip("www."))
                       for d in SUPPORTED_DOMAINS)
        except Exception:
            return False

    @staticmethod
    def extract_url(text: str) -> str | None:
        url_pattern = r'https?://[^\s<>"\')\]]+'
        match = re.search(url_pattern, text)
        return match.group(0) if match else None

    @staticmethod
    async def download_from_url(url: str) -> str | None:
        try:
            import yt_dlp

            output_template = str(TEMP_DIR / "%(id)s.%(ext)s")
            ydl_opts = {
                "outtmpl": output_template,
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 30,
            }

            loop = asyncio.get_event_loop()

            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return info

            info = await loop.run_in_executor(None, _download)

            if info:
                filename = ydl_opts["outtmpl"] % {
                    "id": info.get("id", "unknown"),
                    "ext": "mp3",
                }
                if not filename.endswith(".mp3"):
                    filename = filename.rsplit(".", 1)[0] + ".mp3"
                import os
                if os.path.exists(filename):
                    return filename

                for f in TEMP_DIR.iterdir():
                    if f.suffix == ".mp3" and info.get("id", "") in f.name:
                        return str(f)

            return None

        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            return None

    @staticmethod
    async def download_telegram_media(message, file_path: str) -> str | None:
        try:
            await message.download(file_path)
            return file_path
        except Exception as e:
            logger.error(f"Telegram download failed: {e}")
            return None
