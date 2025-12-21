# YouTube Metadata Manager

Modern FastAPI-based tool to manage YouTube video metadata with multi-language support and admin dashboard.

## ✨ Features

- 🎛️ **Web Dashboard** (SQLAdmin) - Modern admin interface for managing videos, music, and metadata
- 📝 Update video titles and descriptions in multiple languages (中文, 日本語, English)
- 📄 Upload subtitles (.srt files) automatically
- 🏷️ Copy and transform tags from reference videos
- 🗄️ Database management with SQLAlchemy ORM
- 🔐 Secure credential management with environment variables
- 🚀 FastAPI with auto-generated API documentation

## 🏗️ Architecture

```
youtube-metadata-manager/
├── app.py                      # FastAPI + SQLAdmin dashboard
├── cli.py                      # Command-line interface
├── models.py                   # SQLAlchemy ORM models
├── services/
│   ├── youtube_service.py      # YouTube API operations
│   ├── database_service.py     # Database CRUD operations
│   ├── description_service.py  # Description generation
│   └── tag_service.py          # Tag management
├── requirements.txt
└── .env                        # Configuration (not in git)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:
- YouTube API key
- Google OAuth client secrets file path
- MariaDB connection details
- File paths for subtitles and tag replacement CSV

### 3. Start Dashboard (Recommended)

```bash
./start_dashboard.sh
# Or manually:
# uvicorn app:app --reload
```

Then open: http://localhost:8000/admin

### 4. Or Use CLI

```bash
./run.sh
# Or manually:
# python cli.py
```

## 📊 Dashboard Features

- **Videos Management**: Create, read, update, delete video metadata
- **Music Database**: Manage song information
- **Style Linking**: Connect videos with music entries
- **Search & Filter**: Find videos quickly
- **Bulk Operations**: Edit multiple entries

## 🔧 Usage Examples

### Add New Video via Dashboard

1. Go to http://localhost:8000/admin
2. Click "Videos" → "Create"
3. Fill in all language versions (titles, descriptions)
4. Save

### Update Existing Video via CLI

```bash
python cli.py
# Follow prompts:
# 1. Enter YouTube video link
# 2. Enter database VideoID
# 3. Authenticate (first time only)
# 4. Subtitles will be uploaded
# 5. Metadata will be updated
# 6. Tags will be copied from reference video
```

## 📡 API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /admin` - Admin dashboard
- `GET /docs` - Interactive API documentation (Swagger UI)

## 🗄️ Database Schema

### Video Table
- VideoID, YouTubeLink, UploadTime
- ZhHantTitle, JaTitle, EnTitle
- Descriptions (3 languages)
- Subtitle sources, Sheet music links
- InstrumentalType, SubtitleType

### Music Table
- MusicID, WorkID
- Names (3 languages)
- ThemeType, SpotifyID, MV, OfficialArtist

### Style Table
- Links Video ↔ Music
- Style type (Cover, Arrangement, etc.)

## 🔐 Security

⚠️ **Never commit**:
- `.env` (contains secrets)
- `client_secret_*.json` (OAuth credentials)
- `token.json` (OAuth token)

All are in `.gitignore`.

## 🛠️ Development

### Install dev dependencies
```bash
pip install -r requirements.txt
```

### Run with auto-reload
```bash
uvicorn app:app --reload
```

### Access API docs
http://localhost:8000/docs

## 📋 TODO / Future Enhancements

- [ ] Direct video upload support
- [ ] Batch processing for multiple videos
- [ ] Thumbnail upload
- [ ] Analytics dashboard
- [ ] Export/Import metadata (JSON/CSV)
- [ ] User authentication for dashboard
- [ ] Webhook notifications

## 📄 License

Private use only.
