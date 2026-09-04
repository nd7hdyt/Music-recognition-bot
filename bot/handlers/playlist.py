from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.database.repositories import PlaylistRepository, SongRepository
from bot.keyboards.main import playlist_keyboard, playlist_song_keyboard, main_menu
from bot.config import SONGS_PER_PAGE
from bot.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("my"))
async def cmd_my(message: Message):
    await _show_playlist(message.from_user.id, message, page=0)


@router.callback_query(F.data == "my_playlist")
async def callback_my_playlist(callback: CallbackQuery):
    await _show_playlist(callback.from_user.id, callback.message, page=0, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("playlist_page_"))
async def callback_playlist_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[-1])
    await _show_playlist(callback.from_user.id, callback.message, page=page, edit=True)
    await callback.answer()


async def _show_playlist(user_id: int, message, page: int = 0, edit: bool = False):
    offset = page * SONGS_PER_PAGE
    items, total = await PlaylistRepository.get_user_playlist(user_id, offset, SONGS_PER_PAGE)

    if not items:
        text = (
            "\u2764\ufe0f **My Playlist**\n\n"
            "Your playlist is empty!\n\n"
            "Send me music to identify, then tap Save."
        )
        kb = main_menu()
    else:
        text = (
            f"\u2764\ufe0f **My Playlist**\n"
            f"(Page {page + 1} of {(total + SONGS_PER_PAGE - 1) // SONGS_PER_PAGE})\n\n"
        )
        for i, item in enumerate(items, offset + 1):
            if item.song:
                text += f"{i}. **{item.song.title}** \u2014 {item.song.artist}\n"

        kb = playlist_keyboard(items, page, total)

    if edit:
        try:
            await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("playlist_open_"))
async def callback_playlist_open(callback: CallbackQuery):
    song_id = int(callback.data.split("_")[-1])
    song = await SongRepository.get_by_id(song_id)

    if not song:
        await callback.answer("Song not found", show_alert=True)
        return

    text = (
        f"\U0001f3b5 **{song.title}**\n\n"
        f"\U0001f464 {song.artist}\n"
    )
    if song.album:
        text += f"\U0001f4bf {song.album}\n"
    if song.release_date:
        text += f"\U0001f4c5 {song.release_date}\n"

    await callback.message.edit_text(
        text,
        reply_markup=playlist_song_keyboard(song_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("playlist_remove_"))
async def callback_playlist_remove(callback: CallbackQuery):
    song_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    await PlaylistRepository.remove(user_id, song_id)
    await callback.answer("\U0001f5d1\ufe0f Removed from playlist!", show_alert=True)

    await _show_playlist(user_id, callback.message, page=0, edit=True)


@router.callback_query(F.data.startswith("playlist_yt_"))
async def callback_playlist_youtube(callback: CallbackQuery):
    song_id = int(callback.data.split("_")[-1])
    song = await SongRepository.get_by_id(song_id)

    if song and song.youtube_url:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\U0001f517 Open YouTube", url=song.youtube_url)]
        ])
        await callback.message.edit_text(
            f"\U0001f517 **{song.title}**\n\nOpening YouTube...",
            reply_markup=kb,
            parse_mode="Markdown",
        )
        await callback.answer()
    else:
        await callback.answer("No YouTube link available", show_alert=True)
