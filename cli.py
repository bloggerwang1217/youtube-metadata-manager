"""
CLI Interface - Command Line Tool
Uses the refactored services for YouTube metadata management
"""
import os
from dotenv import load_dotenv

from services.youtube_service import YouTubeService
from services.database_service import DatabaseService
from services.description_service import DescriptionService
from services.tag_service import TagService

# Load environment variables
load_dotenv()

# Configuration
CLIENT_SECRETS_FILE = os.getenv('CLIENT_SECRETS_FILE')
SUBTITLES_FOLDER_PATH = os.getenv('SUBTITLES_FOLDER_PATH')
TAG_REPLACEMENT_CSV = os.getenv('TAG_REPLACEMENT_CSV')
API_KEY = os.getenv('YOUTUBE_API_KEY')

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def main():
    """Main CLI execution"""
    print("=" * 60)
    print("YouTube Metadata Manager - CLI")
    print("=" * 60)
    
    # Initialize services
    youtube_service = YouTubeService(CLIENT_SECRETS_FILE)
    db_service = DatabaseService(DATABASE_URL)
    tag_service = TagService(API_KEY, TAG_REPLACEMENT_CSV)
    
    # Get inputs
    video_link = input("\n📹 Input uploaded video link: ")
    db_video_id = int(input("🔢 Input VideoID from database: "))
    
    # Authenticate
    print("\n[1/6] 🔐 Authenticating with YouTube...")
    youtube_service.authenticate()
    print("✓ Authentication successful")
    
    # Extract YouTube video ID
    yt_video_id = YouTubeService.extract_video_id(video_link)
    print(f"✓ YouTube Video ID: {yt_video_id}")
    
    # Get metadata from database
    print("\n[2/6] 📦 Fetching metadata from database...")
    video_data = db_service.get_video_metadata(db_video_id)
    if not video_data:
        print("✗ Failed to fetch video metadata")
        return
    print(f"✓ Metadata fetched: {video_data.get('ZhHantTitle', 'N/A')}")
    
    # Upload subtitles
    print("\n[3/6] 📄 Uploading subtitles...")
    subtitle_names = {
        'Lyrics': {'ja': "歌詞", "en": "English Lyrics Translation", "zh-Hant": "中文歌詞翻譯"},
        'BloggerTalk': {'ja': "僕の心の話", "en": "My heartfelt story", "zh-Hant": "我心裡的話"}
    }
    
    name = subtitle_names.get(video_data['SubtitleType'], subtitle_names['Lyrics'])
    
    for language_code in ['ja', 'en', 'zh-Hant']:
        subtitle_file = f"{language_code}_subtitle.srt"
        subtitle_path = os.path.join(SUBTITLES_FOLDER_PATH, subtitle_file)
        if os.path.exists(subtitle_path):
            youtube_service.upload_subtitle(yt_video_id, language_code, subtitle_path, name[language_code])
        else:
            print(f"⚠ Subtitle file not found: {subtitle_path}")
    
    # Generate descriptions
    print("\n[4/6] 📝 Generating descriptions...")
    info_dict = DescriptionService.prepare_info_dict(video_data)
    inst_type = "instrumental" if video_data['InstrumentalType'] == 'Inst' else "piano"
    
    # Update titles and descriptions
    print("\n[5/6] 🔄 Updating titles and descriptions...")
    languages = ['ja', 'en', 'zh-Hant']
    language_map = {'ja': 'JaTitle', 'en': 'EnTitle', 'zh-Hant': 'ZhHantTitle'}
    
    localized_metadata = {}
    for language_code in languages:
        title = video_data[language_map[language_code]]
        description = DescriptionService.generate(info_dict, inst_type, language=language_code)
        localized_metadata[language_code] = {"title": title, "description": description}
        
        print(f"\n{language_code} Description Preview:")
        print("-" * 40)
        print(description[:200] + "...")
    
    youtube_service.update_video_metadata(yt_video_id, localized_metadata, 10)
    
    # Update tags
    print("\n[6/6] 🏷️ Updating tags...")
    reference_video = input("📌 Input reference video link for tags (or press Enter to skip): ")
    
    if reference_video:
        tag_string = tag_service.grab_tags(reference_video)
        if tag_string:
            youtube_service.update_tags(yt_video_id, tag_string)
            print(f"✓ Tags: {tag_string[:100]}...")
        else:
            print("⚠ No tags found")
    else:
        print("⊘ Skipped tag update")
    
    print("\n" + "=" * 60)
    print("✅ All tasks completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
