from dataclasses import dataclass
from typing import Optional


@dataclass
class SongData:
    title: str
    artist: str
    album: str = ""
    release_date: str = ""
    genre: str = ""
    duration: int = 0
    preview_url: str = ""
    youtube_url: str = ""
    album_art: str = ""
    lyrics: str = ""
    provider: str = ""

    @property
    def duration_str(self) -> str:
        if not self.duration:
            return ""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"

    @classmethod
    def from_audd(cls, data: dict) -> "SongData":
        result = data.get("result", {})
        if not result:
            return cls(title="Unknown", artist="Unknown")

        spotify = result.get("spotify", {}) if isinstance(result.get("spotify"), dict) else {}

        preview = result.get("preview", "")
        if not preview and spotify:
            previews = spotify.get("previews", [])
            if previews and isinstance(previews, list) and len(previews) > 0:
                preview = previews[0].get("url", "")

        album_art = ""
        if spotify:
            album = spotify.get("album", {})
            if isinstance(album, dict):
                album_art = album.get("cover_url", "")
                if not album_art:
                    images = album.get("images", [])
                    if images and isinstance(images, list) and len(images) > 0:
                        album_art = images[0].get("url", "")

        return cls(
            title=result.get("title", "Unknown"),
            artist=result.get("artist", "Unknown"),
            album=result.get("album", ""),
            release_date=result.get("release_date", ""),
            genre=result.get("genre", ""),
            duration=result.get("duration", 0),
            preview_url=preview,
            youtube_url=result.get("song_link", ""),
            album_art=album_art,
            lyrics=result.get("lyrics", ""),
            provider="audd",
        )

    @classmethod
    def from_search(cls, title: str, artist: str, **kwargs) -> "SongData":
        return cls(title=title, artist=artist, **kwargs)


@dataclass
class ArtistData:
    name: str
    image_url: str = ""
    listeners: str = ""
    top_songs: list = None
    bio: str = ""

    def __post_init__(self):
        if self.top_songs is None:
            self.top_songs = []
