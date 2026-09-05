from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from bot.keyboards.main import main_menu
from bot.database.repositories import UserRepository
from bot.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await UserRepository.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    text = (
        "\U0001f3b5 **Music Recognition Bot**\n\n"
        "I'll help you find music! Send me any of these:\n\n"
        "\U0001f3b5 **Song title or artist**\n"
        "\U0001f524 **Lyrics from the song**\n"
        "\U0001f399 **Voice message with music**\n"
        "\U0001f4f9 **Video with music**\n"
        "\U0001f50a **Audio recording**\n"
        "\U0001f3a5 **Video message with music**\n"
        "\U0001f517 **YouTube, Instagram, TikTok or other supported links**\n\n"
        "I'll identify the song and give you useful information about it.\n\n"
        "**Try it now \u2014 send me a voice message and I'll Shazam it for you!**"
    )

    await message.answer(text, reply_markup=main_menu(), parse_mode="Markdown")


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
        "Tap \u2764\ufe0f Save on any song."
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="Markdown")


@router.message(Command("lang"))
async def cmd_lang(message: Message):
    from bot.keyboards.settings import settings_keyboard
    await message.answer("Choose your language:", reply_markup=settings_keyboard())


@router.message(Command("results"))
async def cmd_results(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5", callback_data="results_5"),
            InlineKeyboardButton(text="10", callback_data="results_10"),
            InlineKeyboardButton(text="15", callback_data="results_15"),
            InlineKeyboardButton(text="20", callback_data="results_20"),
        ]
    ])
    await message.answer("How many results per search?", reply_markup=kb)


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    from bot.keyboards.settings import settings_keyboard
    await message.answer("Settings:", reply_markup=settings_keyboard())


@router.message(Command("my"))
async def cmd_my(message: Message):
    from bot.handlers.playlist import cmd_my as playlist_cmd_my
    await playlist_cmd_my(message)


@router.message(Command("top"))
async def cmd_top(message: Message):
    from bot.handlers.admin import cmd_top as admin_cmd_top
    await admin_cmd_top(message)


@router.message(Command("song"))
async def cmd_song(message: Message):
    await message.answer("Send me the song name to search:")


@router.message(Command("artist"))
async def cmd_artist(message: Message):
    await message.answer("Send me the artist name to search:")


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    user = await UserRepository.get_or_create(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    text = (
        "\U0001f3b5 **Main Menu**\n\n"
        "Choose an option below:"
    )
    await callback.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
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
        "Tap \u2764\ufe0f Save on any song."
    )
    await callback.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    await callback.answer()
