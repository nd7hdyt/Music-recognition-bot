from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def settings_keyboard(user) -> InlineKeyboardMarkup:
    lang_text = f"\U0001f310 Language: {user.language.upper()}"
    auto_text = f"\U0001f4be Auto-save: {'ON' if user.auto_save else 'OFF'}"
    notif_text = f"\U0001f514 Notifications: {'ON' if user.notifications else 'OFF'}"
    platform_text = f"\U0001f3b5 Platform: {user.preferred_platform.title()}"
    results_text = f"\U0001f4ca Results: {user.results_count}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang_text, callback_data="set_lang")],
        [InlineKeyboardButton(text=auto_text, callback_data="set_auto_save")],
        [InlineKeyboardButton(text=notif_text, callback_data="set_notifications")],
        [InlineKeyboardButton(text=platform_text, callback_data="set_platform")],
        [InlineKeyboardButton(text=results_text, callback_data="set_results")],
        [InlineKeyboardButton(text="\u2190 Back to Menu", callback_data="main_menu")],
    ])


def language_options() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f1ec\U0001f1e7 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="\U0001f1f7\U0001f1fa Russian", callback_data="lang_ru")],
        [InlineKeyboardButton(text="\U0001f1e9\U0001f1ea German", callback_data="lang_de")],
        [InlineKeyboardButton(text="\U0001f1eb\U0001f1f7 French", callback_data="lang_fr")],
        [InlineKeyboardButton(text="\u2190 Back", callback_data="settings")],
    ])


def platform_options() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="YouTube", callback_data="platform_youtube")],
        [InlineKeyboardButton(text="Spotify", callback_data="platform_spotify")],
        [InlineKeyboardButton(text="Apple Music", callback_data="platform_apple")],
        [InlineKeyboardButton(text="\u2190 Back", callback_data="settings")],
    ])


def results_options() -> InlineKeyboardMarkup:
    buttons = []
    for n in [3, 5, 7, 10]:
        buttons.append([InlineKeyboardButton(text=str(n), callback_data=f"results_{n}")])
    buttons.append([InlineKeyboardButton(text="\u2190 Back", callback_data="settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
