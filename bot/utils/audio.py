import os
import subprocess
import asyncio
from pathlib import Path
from bot.utils.logger import get_logger
from bot.config import TEMP_DIR, RECOGNITION_CLIP_SECONDS

logger = get_logger(__name__)


async def prepare_recognition_clip(input_path: str, duration: int = RECOGNITION_CLIP_SECONDS) -> str:
    """
    Produce a short, compressed mp3 clip suitable for AudD's standard
    recognition endpoint, which rejects uploads longer than ~12 seconds
    with a 400 "audio is too large" error. Works for any input type
    (audio file, video, voice note) since -vn drops any video stream
    and -t caps duration regardless of the source's original length.
    """
    output_path = str(TEMP_DIR / f"{Path(input_path).stem}_clip.mp3")
    cmd = [
        "ffmpeg", "-i", input_path,
        "-t", str(duration),
        "-vn", "-acodec", "libmp3lame", "-q:a", "2",
        "-y", output_path
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(process.communicate(), timeout=60)
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("ffmpeg produced no output")
        return output_path
    except asyncio.TimeoutError:
        logger.error("FFmpeg recognition-clip extraction timed out")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise
    except Exception as e:
        logger.error(f"FFmpeg recognition-clip extraction failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


async def extract_audio(input_path: str, output_format: str = "mp3") -> str:
    output_path = str(TEMP_DIR / f"{Path(input_path).stem}_audio.{output_path_ext(output_format)}")
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vn", "-acodec", "libmp3lame", "-q:a", "2",
        "-y", output_path
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(process.communicate(), timeout=60)
        return output_path
    except asyncio.TimeoutError:
        logger.error("FFmpeg extraction timed out")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise
    except Exception as e:
        logger.error(f"FFmpeg extraction failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


def output_path_ext(fmt: str) -> str:
    mapping = {"mp3": "mp3", "wav": "wav", "ogg": "ogg"}
    return mapping.get(fmt, "mp3")


async def convert_to_wav(input_path: str) -> str:
    output_path = str(TEMP_DIR / f"{Path(input_path).stem}.wav")
    cmd = [
        "ffmpeg", "-i", input_path,
        "-ar", "44100", "-ac", "1",
        "-y", output_path
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(process.communicate(), timeout=60)
        return output_path
    except Exception as e:
        logger.error(f"WAV conversion failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


async def trim_audio(input_path: str, start: int = 0, duration: int = 30) -> str:
    output_path = str(TEMP_DIR / f"{Path(input_path).stem}_trimmed.wav")
    cmd = [
        "ffmpeg", "-i", input_path,
        "-ss", str(start), "-t", str(duration),
        "-y", output_path
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(process.communicate(), timeout=60)
        return output_path
    except Exception as e:
        logger.error(f"Audio trimming failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


def get_audio_duration(file_path: str) -> int:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of", "csv=p=0", file_path],
            capture_output=True, text=True, timeout=10
        )
        return int(float(result.stdout.strip())) if result.stdout.strip() else 0
    except Exception:
        return 0
