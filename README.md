# Teacher Bot YT - NCERT Video Creator 🤖📚

Automated YouTube channel that teaches **Class 1 to 10 NCERT Mathematics** with a unique pencil animation style.

## Features

- 📖 **Downloads actual NCERT books** (Class 1-10, English + Hindi medium)
- 📝 **Sequential topic coverage** — one topic daily, never repeats
- ✏️ **Pencil animation style** — white page with animated pencil drawing content
- 🔊 **Female Hindi voice** — using free Edge-TTS (no costs!)
- 🎬 **Auto-upload to YouTube** — daily automation via GitHub Actions

## Video Style

Each video features:
- Pure white background
- Animated pencil that "writes" content line-by-line
- Class and chapter labels
- Hindi female voice narration

## How It Works

```
1. Download NCERT PDF books (Class 1-10)
2. Extract topics from PDFs
3. Track progress (daily sequential coverage)
4. Render animated frames (pencil drawing)
5. Generate Hindi audio narration
6. Compose video
7. Upload to YouTube
```

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/shairo009/teacher-bot-yt.git
cd teacher-bot-yt
```

### 2. Get YouTube API credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable **YouTube Data API v3**
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `client_secrets.json`
5. Run once locally to get `token.json`

### 3. Add GitHub Secrets
In your repo, go to Settings → Secrets and add:
- `TOKEN_JSON` — content of token.json
- `CLIENT_SECRETS_JSON` — content of client_secrets.json

### 4. Run locally (optional)
```bash
pip install -r requirements.txt
playwright install chromium
python main.py
```

## Running Modes

| Mode | Command | Description |
|------|---------|-------------|
| Full | `python main.py` | Download PDFs, create video, upload |
| Dry run | `python main.py --dry-run` | Create video without uploading |
| Force download | `python main.py --force` | Re-download all PDFs |

## File Structure

```
teacher-bot-yt/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── src/
│   ├── pdf_downloader.py    # Download NCERT PDFs
│   ├── pdf_extractor.py     # Extract text from PDFs
│   ├── topic_manager.py     # Track daily progress
│   ├── render_engine.py     # Pencil animation renderer
│   ├── audio_engine.py      # Hindi TTS
│   ├── video_engine.py      # Video composition
│   └── uploader.py          # YouTube upload
├── templates/
│   └── lesson_template.html # HTML template for animation
└── data/
    ├── books/           # Downloaded PDFs
    ├── topics_index.json    # All topics index
    └── topics_progress.json # Progress tracking
```

## Curriculum Coverage

| Class | Medium | Status |
|-------|--------|--------|
| 1-5 | English + Hindi | ✅ |
| 6-10 | English + Hindi | ✅ |

Each class has ~15 chapters with multiple topics.

## Cost

- **Zero cost!** Uses only free tools:
  - Edge-TTS (no API key needed)
  - Playwright + Chromium (free browser)
  - GitHub Actions (free tier)
  - Google OAuth (free)

## License

MIT License