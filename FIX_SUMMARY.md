# Music Recognition Bot — Fix Summary
**Stack:** Python 3.12, aiogram 3.12, aiosqlite, AudD API (recognition), iTunes Search API (search), Deezer API (previews), lyrics.ovh (lyrics), yt-dlp (search + fallback), Cobalt API (YouTube proxy), mutagen (artwork embedding), ffmpeg.

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

### 18. Added Shazam recognition (removed due to conflicts)
**Files:** `bot/services/music_recognition.py`, `requirements.txt`
**Fix:** Added then removed `shazamio` — pydantic version conflict with aiogram made it unusable on Railway. Using AudD only.

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

### 26. YouTube bot detection on Railway
**File:** `bot/services/music_recognition.py`
**Fix:** Added Cobalt API proxy support. Bot searches YouTube for URL via yt-dlp, then sends URL to Cobalt for download. Falls back to direct yt-dlp if Cobalt unavailable.

### 27. Cobalt API wrong request format
**File:** `bot/services/music_recognition.py`
**Fix:** Cobalt requires direct video URL, not search URL. Added yt-dlp search step to get video URL first.

### 28. Bot menu showing old commands (/lang, /legal)
**Fix:** Cleared bot commands via Telegram API `deleteMyCommands` + `setMyCommands`. Users may need to clear Telegram cache.

### 29. Added debug logging for AudD API
**File:** `bot/services/music_recognition.py`
**Fix:** Added response status and body logging to diagnose recognition failures.

### 30. /help command treated as song inquiry
**File:** `bot/handlers/start.py`
**Fix:** Added explicit `/help` command handler with `Command("help")` filter.

### 31. Missing bot commands
**Files:** `bot/handlers/start.py`, Telegram API
**Fix:** Added `/lang`, `/results`, `/settings`, `/my`, `/top`, `/song`, `/artist` command handlers. Set commands via Telegram API `setMyCommands` for all scopes.

### 32. /start message had inline keyboard
**File:** `bot/handlers/start.py`
**Fix:** Removed `reply_markup=main_menu()` from `/start` handler.

### 33. /top missing caption and pagination
**File:** `bot/handlers/admin.py`
**Fix:** `/top` now shows numbered list with caption "🔥 Popular Songs" and uses `search_results_numbered` keyboard for pagination. Stores songs in `user_search_results` cache.

### 34. /top limited to 10 hardcoded results
**Files:** `bot/services/music_search.py`, `bot/services/metadata.py`
**Fix:** `get_trending()` now fetches from Deezer Charts + iTunes, deduplicates, sorts by popularity, returns top 30. Added `popularity` field to `SongData`.

### 35. Missing album art fallback
**File:** `bot/handlers/recognition.py`
**Fix:** Added `get_album_art_fallback()` with chain: AudD → iTunes → Spotify (embed) → Deezer → YouTube thumbnail. Added `has_embedded_art()` to skip embedding if artwork exists.

### 36. Telegram not showing album art
**File:** `bot/handlers/recognition.py`
**Fix:** Download thumbnail image and pass as `InputFile` to `thumbnail` parameter in `answer_audio()`. Telegram ignores embedded MP3 artwork but displays API thumbnails.

### 37. YouTube audio too large for Telegram
**File:** `bot/services/music_recognition.py`
**Fix:** Reduced YouTube audio quality from 128kbps to 96kbps to stay under Telegram's 50MB limit.

### 38. settings_keyboard() missing argument
**File:** `bot/handlers/start.py`
**Fix:** Fixed `/settings` command to pass user to `settings_keyboard()`.

### 39. Bot conflict with old instance
**File:** `main.py`
**Fix:** Switched from polling to webhook mode. Webhook replaces any existing polling connection. Set `WEBHOOK_URL` environment variable to your Railway app URL.

---

## New Files
- `bot/utils/network.py` — RetryAiohttpSession for network resilience

## Config Changes
- `bot/config.py`: Added `RECOGNITION_CLIP_SECONDS = 12`, `BOT_USERNAME`, `WEBHOOK_URL`; removed `SONGLINK_API_KEY`
- `.env.example`: Removed `SONGLINK_API_KEY`, added `BOT_USERNAME`, `COBALT_API_URL`, `WEBHOOK_URL`
- `requirements.txt`: Added `mutagen`, `requests`; removed `shazamio` (pydantic conflict)

---

## Architecture Notes
- **Webhook mode**: Bot runs as web server, Telegram sends updates to webhook URL
- Recognition: AudD API only (shazamio removed due to pydantic conflict)
- Audio: Cobalt API proxy → yt-dlp fallback → Deezer/iTunes 30s preview
- `download_full_song()`: searches YouTube via yt-dlp (extract_flat), sends URL to Cobalt
- `download_preview()` used only for quick 30s previews when needed
- Artwork embedded via mutagen (supports MP3 ID3 and M4A/M4A covr tags)
- Album art thumbnail downloaded as InputFile for Telegram display
- Recognition result shown immediately; audio downloads in background task
- Bot username auto-fetched from Telegram API on startup
- Lyrics fetched from lyrics.ovh API with Google fallback
- Inline queries return iTunes audio previews

---

## Known Gaps
- YouTube download requires Cobalt proxy (Railway datacenter IPs get blocked)
- Cobalt instance may also get blocked if on same datacenter IP
- pydantic version conflict prevented shazamio usage
- No live runtime testing
- Credentials exposed in conversation — recommend rotating
- Genius API branch needs `LYRICS_API_KEY`
- No automated tests
