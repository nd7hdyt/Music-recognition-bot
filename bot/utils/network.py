import asyncio
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class RetryAiohttpSession(AiohttpSession):
    """
    AiohttpSession that retries a request a few times, with short backoff,
    when it fails with a transient network error (dropped connection,
    connection reset, DNS blip, etc).

    This is the layer that catches things like Windows' intermittent
    "WinError 64 - The specified network name is no longer available",
    which happens when the TCP connection to Telegram's API gets reset
    mid-request. It's usually caused by an unstable network, VPN
    reconnects, or antivirus doing TLS inspection — not by the bot code —
    so a short retry is the correct fix rather than treating it as fatal.
    """

    def __init__(self, *args, max_retries: int = 3, backoff_seconds: float = 1.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    async def make_request(self, bot, method, timeout=None):
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await super().make_request(bot, method, timeout=timeout)
            except TelegramNetworkError as e:
                last_error = e
                if attempt == self.max_retries:
                    logger.error(
                        f"Network request failed after {attempt} attempts "
                        f"({method.__class__.__name__}): {e}"
                    )
                    raise
                wait = self.backoff_seconds * attempt
                logger.warning(
                    f"Transient network error on {method.__class__.__name__} "
                    f"(attempt {attempt}/{self.max_retries}), retrying in {wait:.1f}s: {e}"
                )
                await asyncio.sleep(wait)
        raise last_error
