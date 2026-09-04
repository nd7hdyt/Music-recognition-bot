from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def song_detail_keyboard(song) -> InlineKeyboardMarkup:
    buttons = []
    if song.preview_url:
        buttons.append([InlineKeyboardButton(text="\u25b6\ufe0f Preview", url=song.preview_url)])
    if song.youtube_url:
        buttons.append([InlineKeyboardButton(text="\U0001f517 YouTube", url=song.youtube_url)])
    if song.album_art:
        buttons.append([InlineKeyboardButton(text="\U0001f5bc\ufe0f Album Art", url=song.album_art)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
