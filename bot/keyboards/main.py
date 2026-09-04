from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import SONGS_PER_PAGE, BOT_USERNAME
import bot.config as config


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f3b5 Recognize Music", callback_data="recognize"),
            InlineKeyboardButton(text="\U0001f50e Search Song", callback_data="search_song"),
        ],
        [
            InlineKeyboardButton(text="\U0001f3a4 Search Artist", callback_data="search_artist"),
            InlineKeyboardButton(text="\u2764\ufe0f My Playlist", callback_data="my_playlist"),
        ],
        [
            InlineKeyboardButton(text="\U0001f525 Top Songs", callback_data="top_songs"),
            InlineKeyboardButton(text="\u2699\ufe0f Settings", callback_data="settings"),
        ],
    ])


def recognize_result(song_data, user_id: int = 0, song_id: int = 0) -> InlineKeyboardMarkup:
    import urllib.parse
    search_query = urllib.parse.quote(f"{song_data.artist} {song_data.title}")
    artist_query = urllib.parse.quote(song_data.artist)

    buttons = [
        [
            InlineKeyboardButton(text="Google", url=f"https://www.google.com/search?q={search_query}"),
            InlineKeyboardButton(text="YouTube Music", url=f"https://music.youtube.com/search?q={search_query}"),
            InlineKeyboardButton(text="Spotify", url=f"https://open.spotify.com/search/{search_query}"),
        ],
        [InlineKeyboardButton(text="\U0001f50d Search by artist", url=f"https://t.me/{config.BOT_USERNAME}?start=artist_{artist_query}")],
        [InlineKeyboardButton(text="\u274c Wrong song \u274c", callback_data="wrong_song")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_results_keyboard(songs: list, query: str = "") -> InlineKeyboardMarkup:
    buttons = []
    for i, song in enumerate(songs):
        buttons.append([
            InlineKeyboardButton(
                text=f"{i+1}. {song.artist} \u2013 {song.title}",
                callback_data=f"song_select_{i}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="\u2190 Back to Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_results_numbered(songs: list, page: int = 0, total: int = 0) -> InlineKeyboardMarkup:
    buttons = []
    row1 = []
    row2 = []
    for i, song in enumerate(songs[:8]):
        btn = InlineKeyboardButton(text=str(i+1), callback_data=f"song_select_{i}")
        if i < 4:
            row1.append(btn)
        else:
            row2.append(btn)
    if row1:
        buttons.append(row1)
    if row2:
        buttons.append(row2)

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="\u25c0", callback_data=f"search_page_{page-1}"))
    nav_row.append(InlineKeyboardButton(text="\u274c", callback_data="main_menu"))
    if total > (page + 1) * 8:
        nav_row.append(InlineKeyboardButton(text="\u25b6", callback_data=f"search_page_{page+1}"))
    buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def playlist_keyboard(items: list, page: int, total: int) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        if item.song:
            buttons.append([
                InlineKeyboardButton(
                    text=f"\U0001f3b5 {item.song.title} \u2014 {item.song.artist}",
                    callback_data=f"playlist_open_{item.song_id}"
                )
            ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="\u25c0", callback_data=f"playlist_page_{page - 1}"))
    if (page + 1) * SONGS_PER_PAGE < total:
        nav_row.append(InlineKeyboardButton(text="\u25b6", callback_data=f"playlist_page_{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="\u2190 Back to Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def playlist_song_keyboard(song_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\u25b6\ufe0f Play", callback_data=f"playlist_listen_{song_id}"),
            InlineKeyboardButton(text="\U0001f517 YouTube", callback_data=f"playlist_yt_{song_id}"),
        ],
        [
            InlineKeyboardButton(text="\U0001f5d1\ufe0f Remove", callback_data=f"playlist_remove_{song_id}"),
        ],
        [
            InlineKeyboardButton(text="\u25c0 Back to Playlist", callback_data="my_playlist"),
        ],
    ])
