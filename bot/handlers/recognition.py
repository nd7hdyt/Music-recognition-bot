import os
import asyncio
import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.config import TEMP_DIR, MAX_FILE_SIZE
import bot.config as config
from bot.services.music_recognition import MusicRecognitionService
from bot.services.media_downloader import MediaDownloader
from bot.services.metadata import SongData
from bot.database.repositories import SongRepository, UserRepository, HistoryRepository, PlaylistRepository
from bot.keyboards.main import recognize_result, main_menu
from bot.utils.audio import prepare_recognition_clip
from bot.utils.cleanup import cleanup_file
from bot.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()

recognition_service = MusicRecognitionService()
downloader = MediaDownloader()

recognition_semaphore = asyncio.Semaphore(3)
user_states = {}


@router.message(F.voice | F.audio | F.video | F.video_note)
async def handle_media(message: Message):
    user = await UserRepository.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if message.voice:
        file_id = message.voice.file_id
        file_name = "voice.ogg"
        source = "voice"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "audio.mp3"
        source = "audio"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "video.mp4"
        source = "video"
    elif message.video_note:
        file_id = message.video_note.file_id
        file_name = "video_note.mp4"
        source = "video_note"
    else:
        return

    status_msg = await message.answer(
        "\U0001f3a7 **Listening...**\n\n"
        "Processing your audio...",
        parse_mode="Markdown",
    )

    if recognition_semaphore.locked():
        await status_msg.edit_text(
            "\u23f3 **Processing...**\n\n"
            "Too many requests. Please wait a moment.",
            parse_mode="Markdown",
        )

    input_path = None
    audio_path = None

    async with recognition_semaphore:
        try:
            file = await message.bot.get_file(file_id)
            if file.file_size and file.file_size > MAX_FILE_SIZE:
                await status_msg.edit_text(
                    "\u274c **File too large.**\n\n"
                    "Please send a file smaller than 50MB.",
                    parse_mode="Markdown",
                )
                return

            input_path = str(TEMP_DIR / f"{message.from_user.id}_{file_name}")
            await message.bot.download_file(file.file_path, input_path)

            await status_msg.edit_text(
                "\U0001f50e **Identifying the song...**",
                parse_mode="Markdown",
            )

            audio_path = input_path
            try:
                audio_path = await prepare_recognition_clip(input_path)
            except Exception as e:
                logger.warning(f"Clip preparation failed, falling back to raw file: {e}")
                audio_path = input_path

            song_data = await recognition_service.recognize_file(audio_path)

            if song_data:
                logger.info(f"Recognized: {song_data.title} by {song_data.artist}")

                song = await SongRepository.get_or_create(
                    title=song_data.title,
                    artist=song_data.artist,
                    album=song_data.album,
                    release_date=song_data.release_date,
                    genre=song_data.genre,
                    duration=song_data.duration,
                    preview_url=song_data.preview_url,
                    youtube_url=song_data.youtube_url,
                    album_art=song_data.album_art,
                    provider=song_data.provider,
                )

                await HistoryRepository.add(
                    user_id=message.from_user.id,
                    song_id=song.song_id,
                    source=source,
                )

                if user.auto_save:
                    await PlaylistRepository.add(user_id=message.from_user.id, song_id=song.song_id)

                async def _send_audio():
                    try:
                        filepath = await recognition_service.download_full_song(song_data.title, song_data.artist)

                        if filepath:
                            if song_data.album_art:
                                embed_artwork(filepath, song_data.album_art)
                            from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
                            audio = FSInputFile(filepath)
                            import urllib.parse
                            search_query = urllib.parse.quote(f"{song_data.artist} {song_data.title}")
                            caption = f"@{config.BOT_USERNAME} | [info](https://open.spotify.com/search/{search_query})"
                            kb = InlineKeyboardMarkup(inline_keyboard=[
                                [
                                    InlineKeyboardButton(text="\U0001f3b6 Lyrics", callback_data=f"lyrics_{song.song_id}"),
                                    InlineKeyboardButton(text="\U0001f50d Search", switch_inline_query_current_chat=f"{song_data.artist} {song_data.title}"),
                                ]
                            ])
                            await message.answer_audio(
                                audio=audio,
                                title=song_data.title,
                                performer=song_data.artist,
                                caption=caption,
                                reply_markup=kb,
                                parse_mode="Markdown",
                            )
                            await cleanup_file(filepath)
                    except Exception as e:
                        logger.error(f"Failed to send audio: {e}")

                asyncio.create_task(_send_audio())

                await send_recognition_result(message, song_data, song.song_id)
                await status_msg.delete()
            else:
                await status_msg.edit_text(
                    "\u274c **I couldn't identify this song.**\n\n"
                    "Try sending:\n"
                    "\u2022 A longer audio clip\n"
                    "\u2022 A clearer recording\n"
                    "\u2022 Less background noise\n"
                    "\u2022 Another section of the song",
                    reply_markup=main_menu(),
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Recognition error: {e}")
            await status_msg.edit_text(
                "\u274c Something went wrong while processing your audio.\n\n"
                "Please try again in a few seconds.",
                reply_markup=main_menu(),
                parse_mode="Markdown",
            )
        finally:
            await cleanup_file(input_path)
            if audio_path != input_path:
                await cleanup_file(audio_path)


@router.callback_query(F.data == "recognize")
async def callback_recognize(callback: CallbackQuery):
    await callback.message.edit_text(
        "\U0001f3a7 **Send me audio!**\n\n"
        "Send a voice message, audio file, video, or video note containing music.\n\n"
        "I'll identify the song for you!",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "wrong_song")
async def callback_wrong_song(callback: CallbackQuery):
    await callback.answer("Sorry about that! Send another audio to try again.", show_alert=True)


@router.callback_query(F.data.startswith("listen_"))
async def callback_listen(callback: CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("Invalid request", show_alert=True)
        return

    song_id = int(parts[1])
    song = await SongRepository.get_by_id(song_id)

    if not song or not song.preview_url:
        await callback.answer("Preview not available", show_alert=True)
        return

    await callback.answer("\u23f3 Downloading preview...")

    filename = f"preview_{song_id}.mp3"
    filepath = await download_preview(song.preview_url, filename)

    if filepath:
        try:
            from aiogram.types import FSInputFile
            audio = FSInputFile(filepath)
            await callback.message.answer_audio(
                audio=audio,
                title=song.title,
                performer=song.artist,
                caption=f"\U0001f3b5 {song.title} - {song.artist}",
            )
        except Exception as e:
            logger.error(f"Failed to send audio: {e}")
            await callback.message.answer(
                "\u25b6\ufe0f [Listen on web](" + song.preview_url + ")",
                parse_mode="Markdown",
            )
        finally:
            await cleanup_file(filepath)
    else:
        await callback.message.answer(
            "\u25b6\ufe0f [Listen on web](" + song.preview_url + ")",
            parse_mode="Markdown",
        )


@router.callback_query(F.data.startswith("save_"))
async def callback_save(callback: CallbackQuery):
    song_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    from bot.database.repositories import PlaylistRepository
    added = await PlaylistRepository.add(user_id, song_id)

    if added:
        await callback.answer("\u2764\ufe0f Saved to your playlist!", show_alert=True)
    else:
        await callback.answer("\U0001f514 Already in your playlist!", show_alert=True)


@router.callback_query(F.data.startswith("lyrics_"))
async def callback_lyrics(callback: CallbackQuery):
    song_id = int(callback.data.split("_")[1])
    song = await SongRepository.get_by_id(song_id)

    if not song:
        await callback.answer("Song not found", show_alert=True)
        return

    await callback.answer("\U0001f50d Searching lyrics...")

    import aiohttp
    import urllib.parse

    search_query = urllib.parse.quote(f"{song.artist} {song.title}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.lyrics.ovh/v1/{song.artist}/{song.title}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics = data.get("lyrics", "")
                    if lyrics:
                        if len(lyrics) > 4000:
                            lyrics = lyrics[:4000] + "..."
                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="\u2190 Back", callback_data="main_menu")]
                        ])
                        await callback.message.answer(
                            f"\U0001f3b6 **{song.title}**\nBy {song.artist}\n\n{lyrics}",
                            reply_markup=kb,
                            parse_mode="Markdown",
                        )
                        return
    except Exception:
        pass

    import urllib.parse
    search_query = urllib.parse.quote(f"{song.artist} {song.title} lyrics")
    lyrics_url = f"https://www.google.com/search?q={search_query}"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f3b6 Search Lyrics", url=lyrics_url)],
        [InlineKeyboardButton(text="\u2190 Back", callback_data="main_menu")],
    ])

    await callback.message.answer(
        f"\U0001f3b6 **Lyrics for {song.title}**\n\n"
        f"By {song.artist}\n\n"
        "Sorry, lyrics not available in my database.\nTap below to search online:",
        reply_markup=kb,
        parse_mode="Markdown",
    )


def format_song_result(song: SongData, chat_id: int = 0) -> str:
    link = song.album_art if song.album_art else f"https://t.me/{config.BOT_USERNAME}"
    return f"<code>{song.title} — {song.artist}</code>\n\n<a href=\"{link}\">PD Music Bot</a>"


async def send_recognition_result(message, song_data, song_id):
    text = format_song_result(song_data, message.chat.id)
    kb = recognize_result(song_data, message.from_user.id, song_id)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


async def download_preview(url: str, filename: str) -> str | None:
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    path = str(TEMP_DIR / filename)
                    with open(path, "wb") as f:
                        f.write(await resp.read())
                    return path
    except Exception as e:
        logger.error(f"Download failed: {e}")
    return None


def embed_artwork(audio_path: str, art_url: str):
    try:
        import requests
        from mutagen.mp3 import MP3
        from mutagen.mp4 import MP4
        from mutagen.id3 import ID3, APIC
        from mutagen.easyid3 import EasyID3

        response = requests.get(art_url, timeout=10)
        if response.status_code != 200:
            return

        art_data = response.content

        if audio_path.endswith(".m4a") or audio_path.endswith(".aac"):
            audio = MP4(audio_path)
            audio["covr"] = [art_data]
            audio.save()
            logger.info("Artwork embedded in M4A")
        elif audio_path.endswith(".mp3"):
            audio = MP3(audio_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            audio.tags.add(APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=art_data
            ))
            audio.save()
            logger.info("Artwork embedded in MP3")
    except Exception as e:
        logger.warning(f"Failed to embed artwork: {e}")
