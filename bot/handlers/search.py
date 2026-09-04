from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineQuery,
    InlineQueryResultArticle, InlineQueryResultAudio,
    InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.filters import Command
from bot.services.music_search import MusicSearchService
from bot.services.media_downloader import MediaDownloader
from bot.services.lyrics import LyricsService
from bot.services.metadata import SongData
from bot.database.repositories import SongRepository, UserRepository, HistoryRepository
from bot.keyboards.main import search_results_numbered, recognize_result, main_menu
from bot.config import MAX_SEARCH_RESULTS
import bot.config as config
from bot.utils.logger import get_logger
import time
import urllib.parse

logger = get_logger(__name__)
router = Router()

search_service = MusicSearchService()
downloader = MediaDownloader()
lyrics_service = LyricsService()

user_search_results = {}
MAX_CACHE_AGE = 3600  # 1 hour


def _cleanup_search_cache():
    now = time.time()
    expired = [uid for uid, data in user_search_results.items()
               if now - data.get("time", 0) > MAX_CACHE_AGE]
    for uid in expired:
        del user_search_results[uid]


@router.message(Command("song"))
async def cmd_song(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "\U0001f3b5 **Search for a song**\n\n"
            "Usage: `/song Blinding Lights`\n"
            "Or just send me the song title!",
            parse_mode="Markdown",
        )
        return

    query = args[1]
    await _search_and_respond(message, query)


@router.message(F.text & ~F.command)
async def handle_text_message(message: Message):
    text = message.text.strip()
    if len(text) < 2:
        return

    user = await UserRepository.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if downloader.is_supported_url(text) or downloader.extract_url(text):
        from bot.handlers.admin import _process_url
        url = text if downloader.is_supported_url(text) else downloader.extract_url(text)
        await _process_url(message, url)
        return

    if "\n" in text or (len(text.split()) > 5 and any(w.startswith(("I'", "I ", "the ", "a ", "my ")) for w in text.lower().split())):
        await _handle_lyrics(message, text)
        return

    await _search_and_respond(message, text)


async def _search_and_respond(message: Message, query: str):
    status = await message.answer(
        "\U0001f50e **Searching...**\n\n"
        f"Looking for: {query}",
        parse_mode="Markdown",
    )

    try:
        songs = await search_service.search_song(query, limit=MAX_SEARCH_RESULTS)

        if not songs:
            await status.edit_text(
                "\u274c **No results found.**\n\n"
                "Try a different search term.",
                parse_mode="Markdown",
            )
            return

        user = await UserRepository.get_or_create(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )

        results = songs[:8]
        text = f"\U0001f50d **{query}**\n"
        text += f"**Results 1-{len(results)} of {len(songs)}**\n\n"
        for i, song in enumerate(results, 1):
            duration = ""
            if song.duration:
                mins = song.duration // 60
                secs = song.duration % 60
                duration = f" {mins}:{secs:02d}"
            text += f"**{i}.** {song.artist} \u2013 {song.title}{duration}\n"

        for song in results:
            await SongRepository.get_or_create(
                title=song.title,
                artist=song.artist,
                album=song.album,
                release_date=song.release_date,
                duration=song.duration,
                preview_url=song.preview_url,
                album_art=song.album_art,
            )

        user_search_results[message.from_user.id] = {
            "songs": songs,
            "page": 0,
            "query": query,
            "time": time.time()
        }
        _cleanup_search_cache()

        from bot.keyboards.main import search_results_numbered
        await status.edit_text(
            text,
            reply_markup=search_results_numbered(results, page=0, total=len(songs)),
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        await status.edit_text(
            "\u274c Something went wrong while searching.\n\n"
            "Please try again.",
            parse_mode="Markdown",
        )


async def _handle_lyrics(message: Message, lyrics: str):
    status = await message.answer(
        "\U0001f3b6 **Searching by lyrics...**\n\n"
        "Analyzing your lyrics...",
        parse_mode="Markdown",
    )

    try:
        song = await lyrics_service.search_by_lyrics(lyrics)

        if song:
            text = (
                f"\U0001f3b5 **Found by lyrics!**\n\n"
                f"**{song.title}**\n"
                f"\U0001f464 {song.artist}\n"
            )
            buttons = []
            if song.preview_url:
                buttons.append([{"text": "\u25b6\ufe0f Listen", "url": song.preview_url}])
            buttons.append([{"text": "\u2190 Back to Menu", "callback_data": "main_menu"}])

            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="\u25b6\ufe0f Listen", url=song.preview_url)] if song.preview_url else [],
                [InlineKeyboardButton(text="\u2190 Back to Menu", callback_data="main_menu")],
            ])

            await status.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        else:
            await status.edit_text(
                "\u274c **Couldn't identify the song from these lyrics.**\n\n"
                "Try sending more lyrics or a different section.",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Lyrics search error: {e}")
        await status.edit_text(
            "\u274c Something went wrong.\nPlease try again.",
            parse_mode="Markdown",
        )


@router.callback_query(F.data.startswith("search_page_"))
async def callback_search_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    cache = user_search_results.get(user_id, {})
    if not isinstance(cache, dict) or "songs" not in cache:
        await callback.answer("Search expired", show_alert=True)
        return

    all_songs = cache["songs"]
    query = cache.get("query", "")
    start = page * 8
    end = start + 8
    songs_page = all_songs[start:end]

    if not songs_page:
        await callback.answer("No more results", show_alert=True)
        return

    text = f"\U0001f50d **{query}**\n"
    text += f"**Results {start+1}-{start+len(songs_page)} of {len(all_songs)}**\n\n"
    for i, song in enumerate(songs_page, 1):
        duration = ""
        if song.duration:
            mins = song.duration // 60
            secs = song.duration % 60
            duration = f" {mins}:{secs:02d}"
        text += f"**{i}.** {song.artist} \u2013 {song.title}{duration}\n"

    cache["page"] = page
    user_search_results[user_id] = cache

    from bot.keyboards.main import search_results_numbered
    await callback.message.edit_text(
        text,
        reply_markup=search_results_numbered(songs_page, page=page, total=len(all_songs)),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("song_select_"))
async def callback_song_select(callback: CallbackQuery):
    idx = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    cache = user_search_results.get(user_id, {})
    if not isinstance(cache, dict) or "songs" not in cache:
        await callback.answer("Search expired", show_alert=True)
        return

    all_songs = cache["songs"]
    page = cache.get("page", 0)
    actual_idx = page * 8 + idx

    if actual_idx >= len(all_songs):
        await callback.answer("Song not found", show_alert=True)
        return

    song = all_songs[actual_idx]
    await callback.answer()

    async def _send_search_audio():
        try:
            from bot.services.music_recognition import MusicRecognitionService
            from bot.handlers.recognition import embed_artwork
            from bot.utils.cleanup import cleanup_file

            rec = MusicRecognitionService()
            filepath = await rec.download_full_song(song.title, song.artist)

            if filepath:
                if song.album_art:
                    embed_artwork(filepath, song.album_art)
                from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
                audio = FSInputFile(filepath)
                import urllib.parse
                search_query = urllib.parse.quote(f"{song.artist} {song.title}")
                caption = f"@{config.BOT_USERNAME} | [info](https://open.spotify.com/search/{search_query})"
                db_song = await SongRepository.get_or_create(
                    title=song.title,
                    artist=song.artist,
                    album=song.album,
                    release_date=song.release_date,
                    duration=song.duration,
                    preview_url=song.preview_url,
                    album_art=song.album_art,
                )
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="\U0001f3b6 Lyrics", callback_data=f"lyrics_{db_song.song_id}"),
                        InlineKeyboardButton(text="\U0001f50d Search", switch_inline_query_current_chat=f"{song.artist} {song.title}"),
                    ]
                ])
                await callback.message.answer_audio(
                    audio=audio,
                    title=song.title,
                    performer=song.artist,
                    caption=caption,
                    reply_markup=kb,
                    parse_mode="Markdown",
                )
                await cleanup_file(filepath)
        except Exception as e:
            logger.error(f"Failed to send search audio: {e}")

    import asyncio
    asyncio.create_task(_send_search_audio())


@router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()
    if not query:
        await inline_query.answer([], cache_time=0)
        return

    results = await search_service.search_song(query, limit=5)
    if not results:
        await inline_query.answer([], cache_time=0)
        return

    audio_results = []
    for i, song in enumerate(results):
        if song.preview_url:
            audio_results.append(
                InlineQueryResultAudio(
                    id=str(i),
                    title=song.title,
                    performer=song.artist,
                    audio_url=song.preview_url,
                    thumbnail_url=song.album_art or "https://via.placeholder.com/100",
                )
            )

    if not audio_results:
        await inline_query.answer([], cache_time=0)
        return

    await inline_query.answer(audio_results, cache_time=300)
