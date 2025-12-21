"""
YouTube Metadata Manager - Main Script
Converts the Jupyter notebook workflow into a production-ready script with environment variables
"""

import os
from dotenv import load_dotenv
import mariadb
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import requests
import csv

# Load environment variables
load_dotenv()

# Configuration from environment
API_KEY = os.getenv('YOUTUBE_API_KEY')
CLIENT_SECRETS_FILE = os.getenv('CLIENT_SECRETS_FILE')
SUBTITLES_FOLDER_PATH = os.getenv('SUBTITLES_FOLDER_PATH')
TAG_REPLACEMENT_CSV = os.getenv('TAG_REPLACEMENT_CSV')

DB_CONFIG = {
    "host": os.getenv('DB_HOST'),
    "user": os.getenv('DB_USER'),
    "password": os.getenv('DB_PASSWORD'),
    "database": os.getenv('DB_NAME'),
    "port": int(os.getenv('DB_PORT', 3306)),
}


def authenticate(client_secrets_file):
    """Authenticate with YouTube API using OAuth2"""
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file,
        scopes=['https://www.googleapis.com/auth/youtube.force-ssl']
    )

    credentials = None
    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_file('token.json')

    if not credentials or not credentials.valid:
        credentials = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())

    return build('youtube', 'v3', credentials=credentials)


def get_video_metadata_from_db(video_id):
    """Fetch video metadata from MariaDB database"""
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = f"""
        SELECT Video.*, Style.*, Music.*
        FROM Video
        INNER JOIN Style ON Video.VideoID = Style.VideoID
        INNER JOIN Music ON Style.MusicID = Music.MusicID
        WHERE 
            Video.VideoID = {video_id};
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        results = [dict(zip(column_names, row)) for row in rows]
        
        return results[0] if results else None

    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return None
    finally:
        if conn:
            conn.close()


def update_video_title(youtube, video_id, localized_metadata, category_id):
    """Update video title and localized metadata"""
    try:
        video_response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()
        
        if 'items' in video_response and video_response['items']:
            current_snippet = video_response['items'][0]['snippet']
            current_snippet['defaultLanguage'] = "ja"
            current_snippet['title'] = localized_metadata["ja"]["title"]
            current_snippet['description'] = localized_metadata["ja"]["description"]
            current_snippet['categoryId'] = category_id

        response = youtube.videos().update(
            part='snippet',
            body={
                'id': video_id,
                'snippet': current_snippet
            }
        ).execute()

        print("Titles and metadata for main language updated successfully.")
        update_localization(youtube, video_id, localized_metadata)

    except HttpError as e:
        print(f"An error occurred while updating titles and metadata: {e}")


def update_localization(youtube, video_id, localized_metadata):
    """Update localized titles and descriptions"""
    try:
        request = youtube.videos().update(
            part='localizations',
            body={
                'id': video_id,
                'localizations': localized_metadata
            }
        )
        
        response = request.execute()
        print("Titles and metadata for multiple languages updated successfully.")

    except HttpError as e:
        print(f"An error occurred while updating localization: {e}")


def description_generator(information_dict, inst_type, language='en'):
    """Generate video description based on template"""
    instrumental_template_dict = {
        'zh-Hant': '''
{chinese_introduciton}
–{chinese_name}–
🎵免費樂譜（Gumroad）：https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️訂閱Patreon：https://patreon.com/BloggerMandolin
🌟我的串流/社群平台們：https://ffm.bio/bloggermandolin

–更多資料–
曼陀林演奏：Blogger Wang
原曲：{original_song}
伴奏：{instrumental}
樂譜：{musescore_sheetmusic}
中文歌詞翻譯：{chinese_translation}
英文歌詞翻譯：{english_translation}

–聯絡我–
bloggermandolin@proton.me
''',
        'en': '''
{english_introduciton}
–{english_name}–
🎵Free Sheet Music(Gumroad): https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️Patreon: https://patreon.com/BloggerMandolin
🌟My Platforms: https://ffm.bio/bloggermandolin

–Info–
Mandolin: Blogger Wang
Original: {original_song}
Instrumental: {instrumental}
Sheet music: {musescore_sheetmusic}
Traditional Chinese translation: {chinese_translation}
English Translation: {english_translation}

–Contact me–
bloggermandolin@proton.me
''',
        'ja': '''
{japanese_introduciton}
–{japanese_name}–
🎵無料楽譜（Gumroad）：https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️Patreon：https://patreon.com/BloggerMandolin
🌟プラットフォーム：https://ffm.bio/bloggermandolin

–インフォ–
マンドリン：Blogger Wang
本家様：{original_song}
インスト：{instrumental}
楽譜：{musescore_sheetmusic}
中国語翻訳：{chinese_translation}
英語翻訳：{english_translation}

–Eメール–
bloggermandolin@proton.me
'''
    }

    piano_template_dict = {
        'zh-Hant': '''
{chinese_introduciton}
–{chinese_name}–
🎵免費樂譜（Gumroad）：https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️訂閱Patreon：https://patreon.com/BloggerMandolin
🌟我的串流/社群平台們：https://ffm.bio/bloggermandolin

–更多資料–
曼陀林演奏：Blogger Wang
原曲：{original_song}
樂譜：{musescore_sheetmusic}
鋼琴樂譜參考：{instrumental}
中文歌詞翻譯：{chinese_translation}
英文歌詞翻譯：{english_translation}

–聯絡我–
bloggermandolin@proton.me
''',
        'en': '''
{english_introduciton}
–{english_name}–
🎵Free Sheet Music(Gumroad): https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️Patreon: https://patreon.com/BloggerMandolin
🌟My Platforms: https://ffm.bio/bloggermandolin

–Info–
Mandolin: Blogger Wang
Original: {original_song}
Sheet music: {musescore_sheetmusic}
Piano sheet music: {instrumental}
Traditional Chinese translation: {chinese_translation}
English Translation: {english_translation}

–Contact me–
bloggermandolin@proton.me
''',
        'ja': '''
{japanese_introduciton}
–{japanese_name}–
🎵無料楽譜（Gumroad）：https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️Patreon：https://patreon.com/BloggerMandolin
🌟プラットフォーム：https://ffm.bio/bloggermandolin

–インフォ–
マンドリン：Blogger Wang
本家様：{original_song}
楽譜：{musescore_sheetmusic}
ピアノ楽譜参考：{instrumental}
中国語翻訳：{chinese_translation}
英語翻訳：{english_translation}

–Eメール–
bloggermandolin@proton.me
'''
    }

    if inst_type == "instrumental":
        template = instrumental_template_dict.get(language, instrumental_template_dict[language])
    elif inst_type == "piano":
        template = piano_template_dict.get(language, piano_template_dict[language])

    description = template.format(
        original_song=information_dict["original_song"],
        chinese_translation=information_dict["chinese_translation"],
        english_translation=information_dict["english_translation"],
        instrumental=information_dict["instrumental"],
        japanese_name=information_dict["japanese_name"],
        chinese_name=information_dict["chinese_name"],
        english_name=information_dict["english_name"],
        musescore_sheetmusic=information_dict["musescore_sheetmusic"],
        gumroad_sheetmusic_name=information_dict["gumroad_sheetmusic_name"],
        japanese_introduciton=information_dict["japanese_introduction"],
        chinese_introduciton=information_dict["chinese_introduction"],
        english_introduciton=information_dict["english_introduction"]
    )
    
    return description


def prepare_description_dict(video_data_dict):
    """Prepare information dictionary from database data"""
    return {
        "japanese_introduction": video_data_dict["JaDescription"] + '\n',
        "chinese_introduction": video_data_dict["ZhHantDescription"] + '\n',
        "english_introduction": video_data_dict["EnDescription"] + '\n',
        "musescore_sheetmusic": video_data_dict["Sheet"],
        "gumroad_sheetmusic_name": video_data_dict["GumroadSheet"],
        "original_song": video_data_dict["MV"],
        "chinese_translation": video_data_dict["ZhHantSubSource"],
        "english_translation": video_data_dict["EnSubSource"],
        "instrumental": video_data_dict["Instrumental"],
        "japanese_name": video_data_dict["JaName"],
        "chinese_name": video_data_dict["ZhHantName"],
        "english_name": video_data_dict["EnName"]
    }


def get_video_tags(video_id, api_key):
    """Get tags from an existing YouTube video"""
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if "items" in data and len(data["items"]) > 0:
        tags = data["items"][0]["snippet"].get("tags", [])
        return tags
    
    return None


def replace_tags(tags, replacement_dict):
    """Replace tag words based on replacement dictionary"""
    replaced_tags = []
    for tag in tags:
        replaced_tag = tag
        for word, replacement in replacement_dict.items():
            if word in replaced_tag:
                replaced_tag = replaced_tag.replace(word, replacement)
        replaced_tags.append(replaced_tag)
    return replaced_tags


def read_replacement_dict_from_csv(file_path):
    """Read tag replacement dictionary from CSV"""
    replacement_dict = {}
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) >= 2:
                key, value = row[0], row[1]
                replacement_dict[key] = value
    return replacement_dict


def tag_grabber(reference_video_link):
    """Grab and replace tags from a reference video"""
    video_id = ""
    replacement_dict = read_replacement_dict_from_csv(TAG_REPLACEMENT_CSV)

    if "youtu.be" in reference_video_link:
        video_id = reference_video_link.split("/")[-1]
    else:
        video_id = reference_video_link.split("=")[-1]

    tags = get_video_tags(video_id, API_KEY)

    if tags:
        replaced_tags = replace_tags(tags, replacement_dict)
        tag_string = ",".join(replaced_tags)
        return tag_string
    
    return None


def update_tags(youtube, video_id, tag_string):
    """Update video tags"""
    try:
        video_response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()

        if 'items' in video_response and video_response['items']:
            if 'snippet' in video_response['items'][0]:
                current_snippet = video_response['items'][0]['snippet']
                
                # Split and add new tags
                new_tags = [tag.strip() for tag in tag_string.split(',')]
                existing_tags = current_snippet.get('tags', [])
                updated_tags = existing_tags + new_tags
                
                current_snippet['tags'] = updated_tags

                youtube.videos().update(
                    part='snippet',
                    body={
                        'id': video_id,
                        'snippet': current_snippet
                    }
                ).execute()

                print("Tags updated successfully.")
            else:
                print("Error: 'snippet' key not found in video metadata.")
        else:
            print("Error: 'items' list is empty.")

    except HttpError as e:
        print(f"An error occurred while updating the tags: {e}")


def upload_subtitle(youtube, video_id, language, subtitle_file, name):
    """Upload subtitle file to YouTube video"""
    try:
        request = youtube.captions().insert(
            part='snippet',
            body={
                'snippet': {
                    'videoId': video_id,
                    'name': name[language],
                    'language': language,
                    'isDraft': False
                }
            },
            media_body=MediaFileUpload(subtitle_file, mimetype='application/octet-stream')
        )

        response = request.execute()
        print(f'Subtitles uploaded successfully for {language}')

    except Exception as e:
        print(f'An error occurred uploading subtitle for {language}: {e}')


def extract_video_id(video_link):
    """Extract YouTube video ID from URL"""
    if "youtu.be" in video_link:
        return video_link.split("/")[-1]
    else:
        return video_link.split("=")[-1]


def main():
    """Main execution function"""
    print("YouTube Metadata Manager")
    print("=" * 50)
    
    # Get inputs
    video_link = input("Input uploaded video link: ")
    db_video_id = int(input("Please input the VideoID from database: "))
    
    # Authenticate
    print("\n[1/6] Authenticating with YouTube...")
    youtube = authenticate(CLIENT_SECRETS_FILE)
    print("✓ Authentication successful")
    
    # Extract YouTube video ID
    yt_video_id = extract_video_id(video_link)
    
    # Get metadata from database
    print("\n[2/6] Fetching metadata from database...")
    video_data = get_video_metadata_from_db(db_video_id)
    if not video_data:
        print("✗ Failed to fetch video metadata")
        return
    print("✓ Metadata fetched successfully")
    
    # Upload subtitles
    print("\n[3/6] Uploading subtitles...")
    subtitle_names = {
        'Lyrics': {'ja': "歌詞", "en": "English Lyrics Translation", "zh-Hant": "中文歌詞翻譯"},
        'BloggerTalk': {'ja': "僕の心の話", "en": "My heartfelt story", "zh-Hant": "我心裡的話"}
    }
    
    name = subtitle_names.get(video_data['SubtitleType'], subtitle_names['Lyrics'])
    
    for language_code in ['ja', 'en', 'zh-Hant']:
        subtitle_file = f"{language_code}_subtitle.srt"
        subtitle_path = os.path.join(SUBTITLES_FOLDER_PATH, subtitle_file)
        upload_subtitle(youtube, yt_video_id, language_code, subtitle_path, name)
    
    # Generate descriptions
    print("\n[4/6] Generating descriptions...")
    info_dict = prepare_description_dict(video_data)
    inst_type = "instrumental" if video_data['InstrumentalType'] == 'Inst' else "piano"
    
    # Update titles and descriptions
    print("\n[5/6] Updating titles and descriptions...")
    languages = ['ja', 'en', 'zh-Hant']
    language_map = {'ja': 'JaTitle', 'en': 'EnTitle', 'zh-Hant': 'ZhHantTitle'}
    
    localized_metadata = {}
    for language_code in languages:
        title = video_data[language_map[language_code]]
        description = description_generator(info_dict, inst_type, language=language_code)
        localized_metadata[language_code] = {"title": title, "description": description}
    
    update_video_title(youtube, yt_video_id, localized_metadata, 10)
    
    # Update tags
    print("\n[6/6] Updating tags...")
    reference_video = input("Please input reference video link for tags: ")
    tag_string = tag_grabber(reference_video)
    if tag_string:
        update_tags(youtube, yt_video_id, tag_string)
        print(f"Tags: {tag_string}")
    
    print("\n" + "=" * 50)
    print("✓ All tasks completed successfully!")


if __name__ == "__main__":
    main()
