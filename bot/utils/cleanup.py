import os
import glob
import time
import asyncio
from pathlib import Path
from bot.config import TEMP_DIR
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def cleanup_temp_files(max_age_seconds: int = 3600):
    temp_path = Path(TEMP_DIR)
    if not temp_path.exists():
        return

    now = time.time()
    cleaned = 0

    for file_path in temp_path.iterdir():
        if file_path.is_file():
            try:
                age = now - file_path.stat().st_mtime
                if age > max_age_seconds:
                    file_path.unlink()
                    cleaned += 1
            except Exception as e:
                logger.warning(f"Failed to clean up {file_path}: {e}")

    if cleaned:
        logger.info(f"Cleaned up {cleaned} temporary files")


async def cleanup_file(file_path: str):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Failed to clean up {file_path}: {e}")


async def cleanup_directory(directory: str):
    try:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    file_path.unlink()
            dir_path.rmdir()
    except Exception as e:
        logger.warning(f"Failed to clean up directory {directory}: {e}")
