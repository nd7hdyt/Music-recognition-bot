# Music Recognition Bot — Fix Summary
**Stack:** Python 3.12, aiogram 3.12, aiosqlite, Shazamio (primary recognition), AudD API (fallback), iTunes Search API (search), Deezer API (previews), lyrics.ovh (lyrics), yt-dlp (full songs), mutagen (artwork embedding), ffmpeg.

---

## Bugs Fixed

### 1. Pasted URLs silently dropped
**File:** `bot/handlers/search.py`
**Fix:** Text handler now calls `_process_url` from `admin.py` when URL detected.

### 2. Temp-file cleanup never worked
**File:** `bot/utils/cleanup.py`
**Fix:** Replaced `asyncio.get_event_loop().time()` with `time.time()`.

### 3. Crash risk in media recognition
**File:** `bot/handlers/recognition.py`
**Fix:** Initialize `input_path = None` and `audio_path = None` before try block.

### 4. Same crash-risk in URL recognition
**File:** `bot/handlers/admin.py`
**Fix:** Same pattern as #3.

### 5. Duplicate function definition
**File:** `bot/handlers/recognition.py`
**Fix:** Removed duplicate `format_song_result()`.

### 6. lyrics.ovh API wrong request shape
**File:** `bot/services/lyrics.py`
**Fix:** Changed to `GET https://api.lyrics.ovh/suggest/{encoded_term}`.

### 7. Dead duplicate keyboard function
**File:** `bot/keyboards/main.py`
**Fix:** Removed unused `settings_keyboard()`.

### 8. AudD "audio too large" (HTTP 400)
**Files:** `bot/utils/audio.py`, `bot/handlers/recognition.py`, `bot/handlers/admin.py`, `bot/config.py`
**Fix:** Added `RECOGNITION_CLIP_SECONDS = 12` and `prepare_recognition_clip()` utility.

### 9. Songlink/Odesli API dead
**Files:** `bot/services/songlink.py` (deleted), `bot/config.py`, `.env.example`
**Fix:** Deleted dead code, removed config.

### 10. Missing dependencies in requirements.txt
**File:** `requirements.txt`
**Fix:** Added `mutagen==1.47.0` and `requests==2.32.3` for artwork embedding.

### 11. "Top Songs" button had no handler
**File:** `bot/handlers/admin.py`
**Fix:** Added `callback_top_songs` handler for `top_songs` callback data.

### 12. Database connection never closed
**Files:** `bot/database/database.py`, `main.py`
**Fix:** Added `close_db()` function, called in shutdown `finally` block.

### 13. Memory leak in user_search_results
**File:** `bot/handlers/search.py`
**Fix:** Added TTL cache (1 hour) with auto-cleanup using `time.time()` timestamps.

### 14. Double callback.answer in playlist
**File:** `bot/handlers/playlist.py`
**Fix:** Moved `callback.answer()` inside if block, removed unconditional duplicate.

### 15. Artwork embedding failed on M4A files
**File:** `bot/handlers/recognition.py`
**Fix:** Rewrote `embed_artwork()` to handle both MP3 (ID3) and M4A (MP4) formats using mutagen.

### 16. Full songs always 30 seconds
**File:** `bot/services/music_recognition.py`
**Fix:** `download_full_song()` now skips Deezer/iTunes previews and goes straight to YouTube for full tracks.

### 17. Audio sent sequentially (slow)
**File:** `bot/handlers/recognition.py`
**Fix:** Audio download/send now runs as background task (`asyncio.create_task`) — result shows instantly, audio follows.

### 18. Added Shazam recognition (free, fast)
**Files:** `bot/services/music_recognition.py`, `requirements.txt`
**Fix:** Added `shazamio` as primary recognition (free, no API key, async). AudD used as fallback.

### 19. Bot username not auto-detected
**Files:** `bot/config.py`, `main.py`
**Fix:** Added `BOT_USERNAME` config; auto-fetches from Telegram API on startup if not set in `.env`.

### 20. Lyrics button only showed search link
**File:** `bot/handlers/recognition.py`
**Fix:** Lyrics button now fetches lyrics from lyrics.ovh API and displays full lyrics in chat. Falls back to Google search if unavailable.

### 21. Inline query handler missing
**File:** `bot/handlers/search.py`
**Fix:** Added `inline_query_handler` for `switch_inline_query` buttons. Returns audio previews from iTunes.

### 22. Audio caption format
**Files:** `bot/handlers/recognition.py`, `bot/handlers/search.py`
**Fix:** Audio caption shows `@bot_username | info` with Spotify search link.

### 23. Recognition UI updated
**Files:** `bot/handlers/recognition.py`, `bot/keyboards/main.py`
**Fix:** Recognition shows monospace title—artist with bot link. Buttons: Google, YouTube Music, Spotify, Search by artist, Wrong song, Lyrics, Search.

### 24. Wrong song callback missing
**File:** `bot/handlers/recognition.py`
**Fix:** Added `callback_wrong_song` handler for "Wrong song" button.

### 25. Webhook conflict on startup
**File:** `main.py`
**Fix:** Moved `delete_webhook()` before `get_me()` to avoid conflict errors.

---

## New Files
- `bot/utils/network.py` — RetryAiohttpSession for network resilience

## Config Changes
- `bot/config.py`: Added `RECOGNITION_CLIP_SECONDS = 12`, `BOT_USERNAME`; removed `SONGLINK_API_KEY`
- `.env.example`: Removed `SONGLINK_API_KEY`, added `BOT_USERNAME`
- `requirements.txt`: Added `mutagen`, `requests`, `shazamio`

---

## Architecture Notes
- Recognition: Shazam (free, fast) → AudD (fallback, requires API key)
- Audio: YouTube (full song, only source for complete tracks)
- `download_full_song()` skips previews, goes straight to YouTube
- `download_preview()` used only for quick 30s previews when needed
- Artwork embedded via mutagen (supports MP3 ID3 and MP4/M4A covr tags)
- Recognition result shown immediately; audio downloads in background task
- Bot username auto-fetched from Telegram API on startup
- Lyrics fetched from lyrics.ovh API with Google fallback
- Inline queries return iTunes audio previews

---

## Known Gaps
- YouTube download ~15-20s (only source for full songs)
- shazamio is unofficial (could break if Shazam changes API)
- pydantic version conflict (shazamio needs 2.13+, aiogram needs <2.9)
- No live runtime testing
- Credentials exposed in conversation — recommend rotating
- Genius API branch needs `LYRICS_API_KEY`
- No automated tests
