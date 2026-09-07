import asyncio
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from bot.config import BOT_TOKEN, BOT_USERNAME, WEBHOOK_URL
import bot.config as config
from bot.database.database import init_db, close_db
from bot.handlers import start, recognition, search, artist, playlist, settings, help, admin
from bot.utils.logger import get_logger
from bot.utils.cleanup import cleanup_temp_files
from bot.utils.network import RetryAiohttpSession

logger = get_logger(__name__)

WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "music_bot_webhook_secret_2026"

async def on_startup(bot: Bot, dp: Dispatcher, app: web.Application):
    await init_db()
    logger.info("Database initialized")

    if not BOT_USERNAME:
        me = await bot.get_me()
        config.BOT_USERNAME = me.username
        logger.info(f"Bot username: @{me.username}")
    else:
        logger.info(f"Bot username: @{BOT_USERNAME}")

    if WEBHOOK_URL:
        await bot.set_webhook(
            url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True,
        )
        logger.info(f"Webhook set to: {WEBHOOK_URL}{WEBHOOK_PATH}")
    else:
        logger.warning("WEBHOOK_URL not set, falling back to polling")
        dp["use_polling"] = True

async def on_shutdown(bot: Bot, app: web.Application):
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted")
    await close_db()
    await bot.session.close()
    logger.info("Bot stopped")

async def webhook_handler(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    dp: Dispatcher = request.app["dp"]

    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_token != WEBHOOK_SECRET:
        logger.warning("Invalid secret token")
        return web.Response(status=403)

    try:
        update = await request.json()
        logger.info(f"Webhook received update: {update.get('update_id', '?')}")
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)

    return web.Response()

async def health_handler(request: web.Request) -> web.Response:
    return web.Response(text="OK")

async def scheduled_cleanup():
    while True:
        await asyncio.sleep(3600)
        await cleanup_temp_files(max_age_seconds=3600)

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Please configure your .env file.")
        sys.exit(1)

    session = RetryAiohttpSession(max_retries=3, backoff_seconds=1.0)
    bot = Bot(token=BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

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

    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp
    app.on_startup.append(lambda app: on_startup(bot, dp, app))
    app.on_shutdown.append(lambda app: on_shutdown(bot, app))
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/", health_handler)

    cleanup_task = asyncio.create_task(scheduled_cleanup())

    import os
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Using port: {port}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Webhook server started on port {port}")
    logger.info(f"Webhook URL: {WEBHOOK_URL}{WEBHOOK_PATH}")

    try:
        await asyncio.Event().wait()
    finally:
        cleanup_task.cancel()
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
