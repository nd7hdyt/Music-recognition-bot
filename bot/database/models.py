from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    language: str = "en"
    auto_save: bool = False
    notifications: bool = True
    preferred_platform: str = "youtube"
    results_count: int = 5
    created_at: Optional[str] = None
    last_active: Optional[str] = None


@dataclass
class Song:
    song_id: Optional[int] = None
    title: str = ""
    artist: str = ""
    album: str = ""
    release_date: str = ""
    genre: str = ""
    duration: int = 0
    preview_url: str = ""
    youtube_url: str = ""
    album_art: str = ""
    provider: str = ""
    created_at: Optional[str] = None


@dataclass
class PlaylistItem:
    id: Optional[int] = None
    user_id: int = 0
    song_id: int = 0
    added_at: Optional[str] = None
    song: Optional[Song] = None


@dataclass
class RecognitionRecord:
    id: Optional[int] = None
    user_id: int = 0
    song_id: Optional[int] = None
    recognized_at: Optional[str] = None
    source: str = "voice"
    song: Optional[Song] = None
