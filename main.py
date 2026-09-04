import asyncio
import signal
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN, BOT_USERNAME
import bot.config as config
from bot.database.database import init_db, close_db
from bot.handlers import start, recognition, search, artist, playlist, settings, help, admin
from bot.utils.logger import get_logger
from bot.utils.cleanup import cleanup_temp_files
from bot.utils.network import RetryAiohttpSession

logger = get_logger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Please configure your .env file.")
        sys.exit(1)

    await init_db()
    logger.info("Database initialized")

    session = RetryAiohttpSession(max_retries=3, backoff_seconds=1.0)
    bot = Bot(token=BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

    await bot.delete_webhook(drop_pending_updates=True)

    if not BOT_USERNAME:
        me = await bot.get_me()
        config.BOT_USERNAME = me.username
        logger.info(f"Bot username: @{me.username}")
    else:
        logger.info(f"Bot username: @{BOT_USERNAME}")

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(start.router)
    dp.include_router(recognition.router)
    dp.include_router(search.router)
    dp.include_router(artist.router)
    dp.include_router(playlist.router)
    dp.include_router(settings.router)
    dp.include_router(help.router)
    dp.include_router(admin.router)

    logger.info("All handlers registered")

    async def scheduled_cleanup():
        while True:
            await asyncio.sleep(3600)
            await cleanup_temp_files(max_age_seconds=3600)

    cleanup_task = asyncio.create_task(scheduled_cleanup())

    try:
        logger.info("Bot starting...")
        await dp.start_polling(bot)
    finally:
        cleanup_task.cancel()
        await close_db()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
