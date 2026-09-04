from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.keyboards.main import main_menu
from bot.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "\U0001f3b5 **How to use the bot**\n\n"
        "**1. Identify music**\n"
        "Send a voice message, audio, video, or video note containing music.\n\n"
        "**2. Search**\n"
        "Send a song title or use `/song`.\n\n"
        "**3. Find an artist**\n"
        "Use `/artist`.\n\n"
        "**4. Search lyrics**\n"
        "Send a few lines of lyrics.\n\n"
        "**5. Identify online videos**\n"
        "Send a YouTube, TikTok, Instagram, or supported platform link.\n\n"
        "**6. Save music**\n"
        "Tap \u2764\ufe0f Save on any song.\n\n"
        "---\n\n"
        "**Commands:**\n"
        "• `/song` \u2014 Search for a song\n"
        "• `/artist` \u2014 Search for an artist\n"
        "• `/my` \u2014 View your saved songs\n"
        "• `/top` \u2014 Popular songs\n"
        "• `/settings` \u2014 Change bot settings\n"
        "• `/help` \u2014 Show this help"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="Markdown")
