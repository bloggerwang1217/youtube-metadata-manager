# YouTube Metadata Manager

A tool to manage YouTube video metadata (titles, descriptions, subtitles, tags) with multi-language support.

## Features

- 📝 Update video titles and descriptions in multiple languages (Chinese, English, Japanese)
- 📄 Upload subtitles (.srt files) automatically
- 🏷️ Copy and transform tags from reference videos
- 🗄️ Fetch video metadata from MariaDB database
- 🔐 Secure credential management with environment variables

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd youtube-metadata-manager
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your credentials:
     - YouTube API key
     - Google OAuth client secrets file path
     - MariaDB connection details
     - File paths for subtitles and tag replacement CSV

4. Place your Google OAuth client secret JSON file in the project directory

5. Prepare your subtitle files in the configured folder with names:
   - `ja_subtitle.srt`
   - `en_subtitle.srt`
   - `zh-Hant_subtitle.srt`

## Usage

### CLI Mode

Run the main script:
```bash
python metadata_manager.py
```

Follow the prompts to:
1. Enter the YouTube video link
2. Enter the database Video ID
3. Authenticate with YouTube (first time only)
4. Upload subtitles
5. Update titles and descriptions
6. Update tags from a reference video

### Original Jupyter Notebook

The original workflow is preserved in `metadata_saver.ipynb` for reference.

## Configuration

### Database Schema

The tool expects the following tables:
- `Video`: Video metadata (VideoID, YouTubeLink, titles, descriptions, etc.)
- `Style`: Style information (Style, InstrumentalType, SubtitleType, etc.)
- `Music`: Music information (MusicID, names, SpotifyID, MV, etc.)

### Tag Replacement CSV

Format: `original_word,replacement_word` (one per line)

Example:
```csv
Old Artist,New Artist
Original Title,Cover Title
```

## Security Notes

⚠️ **IMPORTANT**: Never commit these files to Git:
- `.env` (contains secrets)
- `client_secret_*.json` (OAuth credentials)
- `token.json` (OAuth token)

These are already in `.gitignore`.

## Future Enhancements

- [ ] Web dashboard UI (Flask)
- [ ] Direct video upload support
- [ ] Batch processing for multiple videos
- [ ] Preview before publishing changes
- [ ] Thumbnail upload support

## License

Private use only.
