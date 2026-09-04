from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.database.repositories import UserRepository
from bot.keyboards.settings import settings_keyboard, language_options, platform_options, results_options
from bot.keyboards.main import main_menu
from bot.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    user = await UserRepository.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    text = (
        "\u2699\ufe0f **Settings**\n\n"
        "Configure your bot preferences:"
    )
    await message.answer(text, reply_markup=settings_keyboard(user), parse_mode="Markdown")


@router.callback_query(F.data == "settings")
async def callback_settings(callback: CallbackQuery):
    user = await UserRepository.get_or_create(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    text = (
        "\u2699\ufe0f **Settings**\n\n"
        "Configure your bot preferences:"
    )
    await callback.message.edit_text(text, reply_markup=settings_keyboard(user), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "set_lang")
async def callback_set_lang(callback: CallbackQuery):
    await callback.message.edit_text(
        "\U0001f310 **Select Language**",
        reply_markup=language_options(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def callback_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await UserRepository.update_settings(callback.from_user.id, language=lang)
    await callback.answer(f"\u2705 Language set to {lang.upper()}", show_alert=True)

    user = await UserRepository.get_or_create(user_id=callback.from_user.id)
    await callback.message.edit_text(
        "\u2699\ufe0f **Settings**\n\nConfigure your bot preferences:",
        reply_markup=settings_keyboard(user),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "set_auto_save")
async def callback_set_auto_save(callback: CallbackQuery):
    user = await UserRepository.get_or_create(user_id=callback.from_user.id)
    new_val = 0 if user.auto_save else 1
    await UserRepository.update_settings(callback.from_user.id, auto_save=new_val)
    status = "ON" if new_val else "OFF"
    await callback.answer(f"\U0001f4be Auto-save: {status}", show_alert=True)

    user = await UserRepository.get_or_create(user_id=callback.from_user.id)
    await callback.message.edit_text(
        "\u2699\ufe0f **Settings**\n\nConfigure your bot preferences:",
        reply_markup=settings_keyboard(user),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "set_notifications")
async def callback_set_notifications(callback: CallbackQuery):
    user = await UserRepository.get_or_create(user_id=callback.from_user.id)
    new_val = 0 if user.notifications else 1
    await UserRepository.update_settings(callback.from_user.id, notifications=new_val)
    status = "ON" if new_val else "OFF"
    await callback.answer(f"\U0001f514 Notifications: {status}", show_alert=True)

    user = await UserRepository.get_or_create(user_id=callback.from_user.id)
    await callback.message.edit_text(
        "\u2699\ufe0f **Settings**\n\nConfigure your bot preferences:",
        reply_markup=settings_keyboard(user),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "set_platform")
async def callback_set_platform(callback: CallbackQuery):
    await callback.message.edit_text(
        "\U0001f3b5 **Select Preferred Platform**",
        reply_markup=platform_options(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("platform_"))
async def callback_platform(callback: CallbackQuery):
    platform = callback.data.split("_")[1]
    await UserRepository.update_settings(callback.from_user.id, preferred_platform=platform)
    await callback.answer(f"\u2705 Platform set to {platform.title()}", show_alert=True)

    user = await UserRepository.get_or_create(user_id=callback.from_user.id)
    await callback.message.edit_text(
        "\u2699\ufe0f **Settings**\n\nConfigure your bot preferences:",
        reply_markup=settings_keyboard(user),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "set_results")
async def callback_set_results(callback: CallbackQuery):
    await callback.message.edit_text(
        "\U0001f4ca **Results per page**",
        reply_markup=results_options(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("results_"))
async def callback_results(callback: CallbackQuery):
    count = int(callback.data.split("_")[1])
    await UserRepository.update_settings(callback.from_user.id, results_count=count)
    await callback.answer(f"\U0001f4ca Results set to {count}", show_alert=True)

    user = await UserRepository.get_or_create(user_id=callback.from_user.id)
    await callback.message.edit_text(
        "\u2699\ufe0f **Settings**\n\nConfigure your bot preferences:",
        reply_markup=settings_keyboard(user),
        parse_mode="Markdown",
    )
