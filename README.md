# Music Recognition Bot

A production-ready Telegram bot that identifies songs from audio, voice messages, videos, lyrics, and links.

## Features

- Music recognition from voice/audio/video
- Song and artist search
- Lyrics-based identification
- URL recognition (YouTube, Instagram, TikTok)
- Personal playlist management
- Popular songs
- User settings
- Admin panel with stats and broadcast

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

Required variables:
- `BOT_TOKEN` - Telegram bot token from @BotFather
- `MUSIC_API_KEY` - AudD API key
- `ADMIN_IDS` - Comma-separated Telegram user IDs for admins

### 3. Get Music Recognition API Key

1. Go to https://audd.io/
2. Sign up for a free account
3. Get your API token from the dashboard
4. Add it to `.env` as `MUSIC_API_KEY`

Free tier: 100 requests/month

### 4. Install FFmpeg

**Windows:**
```bash
winget install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**Docker:** Included in the Dockerfile

### 5. Run Locally

```bash
python main.py
```

### 6. Deploy to Railway

1. Push to GitHub
2. Go to https://railway.app
3. Create new project
4. Connect your GitHub repo
5. Add environment variables in Railway dashboard
6. Deploy

### 7. Persistent Storage (Railway)

1. Add a Volume in Railway
2. Mount at `/data`
3. Database will be stored at `/data/musicbot.db`

### 8. Testing

1. Start the bot: `python main.py`
2. Open Telegram and find your bot
3. Send `/start`
4. Try these tests:
   - Send a voice message with music
   - Type a song name: `Blinding Lights`
   - Send lyrics: `I've been tryna call`
   - Send a YouTube link
   - Use `/artist The Weeknd`
   - Use `/top`

## Project Structure

```
bot/
├── main.py              # Entry point
├── config.py            # Configuration
├── handlers/            # Telegram handlers
├── services/            # Business logic
├── database/            # Database layer
├── keyboards/           # Inline keyboards
└── utils/               # Utilities
```

## Architecture

- **Handlers**: Process Telegram messages and callbacks
- **Services**: Business logic (recognition, search, etc.)
- **Database**: SQLite with async support, easily swappable to PostgreSQL
- **Utils**: Audio processing, cleanup, logging

## Adding New Recognition Provider

1. Create a new service in `bot/services/`
2. Implement the same interface as `MusicRecognitionService`
3. Update `recognition.py` handler to use your new service

## License

MIT
