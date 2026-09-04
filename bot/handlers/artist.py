from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.services.music_search import MusicSearchService
from bot.keyboards.main import main_menu
from bot.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()

search_service = MusicSearchService()


@router.message(Command("artist"))
async def cmd_artist(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "\U0001f3a4 **Search for an artist**\n\n"
            "Usage: `/artist The Weeknd`",
            parse_mode="Markdown",
        )
        return

    query = args[1]
    await _search_artist(message, query)


async def _search_artist(message: Message, query: str):
    status = await message.answer(
        "\U0001f50e **Searching...**\n\n"
        f"Looking for: {query}",
        parse_mode="Markdown",
    )

    try:
        artist = await search_service.search_artist(query)

        if not artist:
            await status.edit_text(
                "\u274c **Artist not found.**\n\n"
                "Try a different name.",
                parse_mode="Markdown",
            )
            return

        text = (
            f"\U0001f3a4 **{artist.name}**\n\n"
            f"Popular songs:\n"
        )

        for i, song in enumerate(artist.top_songs, 1):
            text += f"{i}. **{song.title}**\n"

        await status.edit_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Artist search error: {e}")
        await status.edit_text(
            "\u274c Something went wrong.\nPlease try again.",
            parse_mode="Markdown",
        )


@router.callback_query(F.data == "search_artist")
async def callback_search_artist(callback: CallbackQuery):
    await callback.message.edit_text(
        "\U0001f3a4 **Search for an artist**\n\n"
        "Send me the artist name.\n\n"
        "Example: `The Weeknd`",
        parse_mode="Markdown",
    )
    await callback.answer()
