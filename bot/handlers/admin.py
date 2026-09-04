import os
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.config import TEMP_DIR, ADMIN_IDS
from bot.services.media_downloader import MediaDownloader
from bot.database.repositories import HistoryRepository, UserRepository
from bot.keyboards.main import main_menu
from bot.utils.audio import extract_audio
from bot.utils.cleanup import cleanup_file
from bot.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()

downloader = MediaDownloader()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("top"))
async def cmd_top(message: Message):
    from bot.services.music_search import MusicSearchService
    search = MusicSearchService()

    status = await message.answer(
        "\U0001f525 **Loading popular songs...**",
        parse_mode="Markdown",
    )

    songs = await search.get_trending()

    if not songs:
        await status.edit_text(
            "\u274c Couldn't load popular songs.\nPlease try again later.",
            parse_mode="Markdown",
        )
        return

    text = "\U0001f525 **Popular Songs**\n\n"
    for i, song in enumerate(songs, 1):
        text += f"{i}. **{song.title}** \u2014 {song.artist}\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for i, song in enumerate(songs):
        buttons.append([
            InlineKeyboardButton(
                text=f"\U0001f3b5 {song.title}",
                callback_data=f"top_select_{i}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="\u2190 Back to Menu", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await status.edit_text(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "top_songs")
async def callback_top_songs(callback: CallbackQuery):
    from bot.services.music_search import MusicSearchService
    search = MusicSearchService()

    await callback.answer()

    status = await callback.message.answer(
        "\U0001f525 **Loading popular songs...**",
        parse_mode="Markdown",
    )

    songs = await search.get_trending()

    if not songs:
        await status.edit_text(
            "\u274c Couldn't load popular songs.\nPlease try again later.",
            parse_mode="Markdown",
        )
        return

    text = "\U0001f525 **Popular Songs**\n\n"
    for i, song in enumerate(songs, 1):
        text += f"{i}. **{song.title}** \u2014 {song.artist}\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for i, song in enumerate(songs):
        buttons.append([
            InlineKeyboardButton(
                text=f"\U0001f3b5 {song.title}",
                callback_data=f"top_select_{i}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="\u2190 Back to Menu", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await status.edit_text(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("top_select_"))
async def callback_top_select(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "\U0001f3b5 **Song selected**\n\n"
        "Send /song <title> to search for this song.",
        parse_mode="Markdown",
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("\u274c Access denied.")
        return

    stats = await HistoryRepository.get_stats()

    text = (
        "\U0001f4ca **Bot Statistics**\n\n"
        f"\U0001f465 Total users: **{stats['total_users']}**\n"
        f"\U0001f3b5 Total recognitions: **{stats['total_recognitions']}**\n"
        f"\U0001f4bf Total songs: **{stats['total_songs']}**\n"
        f"\u2764\ufe0f Saved songs: **{stats['total_saved']}**\n"
        f"\U0001f4c5 Users today: **{stats['users_today']}**\n"
        f"\U0001f4ca Recognitions today: **{stats['recognitions_today']}**"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("\u274c Access denied.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: `/broadcast <message>`",
            parse_mode="Markdown",
        )
        return

    broadcast_text = args[1]
    user_ids = await UserRepository.get_all_user_ids()

    sent = 0
    failed = 0

    status = await message.answer(
        f"\U0001f4e2 Broadcasting to {len(user_ids)} users...",
        parse_mode="Markdown",
    )

    for user_id in user_ids:
        try:
            await message.bot.send_message(user_id, broadcast_text, parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await status.edit_text(
        f"\u2705 Broadcast complete!\n\n"
        f"Sent: {sent}\nFailed: {failed}",
        parse_mode="Markdown",
    )


@router.message(Command("url"))
async def cmd_url(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "\U0001f517 **Identify from URL**\n\n"
            "Send a URL with the command:\n"
            "`/url https://youtube.com/watch?v=...`\n\n"
            "Or just send me a link directly!",
            parse_mode="Markdown",
        )
        return

    url = args[1].strip()
    await _process_url(message, url)


async def _process_url(message: Message, url: str):
    if not downloader.is_supported_url(url):
        await message.answer(
            "\u274c **Unsupported URL.**\n\n"
            "Supported platforms:\n"
            "\u2022 YouTube\n"
            "\u2022 Instagram\n"
            "\u2022 TikTok\n"
            "\u2022 Facebook\n"
            "\u2022 Twitter/X\n"
            "\u2022 SoundCloud",
            parse_mode="Markdown",
        )
        return

    status = await message.answer(
        "\U0001f517 **Analyzing video...**\n\n"
        "\u23f3 Downloading audio...",
        parse_mode="Markdown",
    )

    audio_path = None
    clip_path = None

    try:
        audio_path = await downloader.download_from_url(url)

        if not audio_path:
            await status.edit_text(
                "\u274c **Failed to download.**\n\n"
                "The link might be:\n"
                "\u2022 Private or restricted\n"
                "\u2022 Not a supported format\n"
                "\u2022 Temporarily unavailable",
                parse_mode="Markdown",
            )
            return

        await status.edit_text(
            "\U0001f517 **Analyzing video...**\n\n"
            "\U0001f50e Identifying music...",
            parse_mode="Markdown",
        )

        from bot.utils.audio import prepare_recognition_clip
        try:
            clip_path = await prepare_recognition_clip(audio_path)
        except Exception as e:
            logger.warning(f"Clip preparation failed, falling back to raw download: {e}")
            clip_path = audio_path

        from bot.services.music_recognition import MusicRecognitionService
        recognition = MusicRecognitionService()
        song = await recognition.recognize_file(clip_path)

        if song:
            text = (
                f"\U0001f3b5 **Song Identified!**\n\n"
                f"**Song:** {song.title}\n"
                f"**Artist:** {song.artist}\n"
            )
            if song.album:
                text += f"**Album:** {song.album}\n"

            from bot.keyboards.main import recognize_result
            from bot.database.repositories import SongRepository
            from bot.database.models import Song

            db_song = await SongRepository.get_or_create(
                title=song.title,
                artist=song.artist,
                album=song.album,
                release_date=song.release_date,
                genre=song.genre,
                duration=song.duration,
                preview_url=song.preview_url,
                youtube_url=song.youtube_url,
                album_art=song.album_art,
            )

            await status.edit_text(
                text,
                reply_markup=recognize_result(song, message.from_user.id, db_song.song_id),
                parse_mode="Markdown",
            )
        else:
            await status.edit_text(
                "\u274c **Couldn't identify the song.**\n\n"
                "The video might not contain recognizable music.",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"URL processing error: {e}")
        await status.edit_text(
            "\u274c Something went wrong.\nPlease try again.",
            parse_mode="Markdown",
        )
    finally:
        await cleanup_file(audio_path)
        if clip_path and clip_path != audio_path:
            await cleanup_file(clip_path)


@router.message(F.text & F.text.func(lambda t: MediaDownloader().extract_url(t) is not None))
async def handle_url(message: Message):
    url = MediaDownloader.extract_url(message.text)
    if url:
        await _process_url(message, url)
