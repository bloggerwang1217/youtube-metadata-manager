"""
YouTube API Service
Handles authentication, video updates, subtitle uploads, and tag management
"""
import os
from typing import Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials


class YouTubeService:
    def __init__(self, client_secrets_file: str):
        self.client_secrets_file = client_secrets_file
        self.youtube = None
        
    def authenticate(self):
        """Authenticate with YouTube API using OAuth2"""
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file,
            scopes=['https://www.googleapis.com/auth/youtube.force-ssl']
        )

        credentials = None
        if os.path.exists('token.json'):
            credentials = Credentials.from_authorized_user_file('token.json')

        if not credentials or not credentials.valid:
            credentials = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(credentials.to_json())

        self.youtube = build('youtube', 'v3', credentials=credentials)
        return self.youtube
    
    def update_video_metadata(self, video_id: str, localized_metadata: Dict, category_id: int = 10):
        """Update video title and localized metadata"""
        try:
            video_response = self.youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if 'items' in video_response and video_response['items']:
                current_snippet = video_response['items'][0]['snippet']
                current_snippet['defaultLanguage'] = "ja"
                current_snippet['title'] = localized_metadata["ja"]["title"]
                current_snippet['description'] = localized_metadata["ja"]["description"]
                current_snippet['categoryId'] = category_id

            response = self.youtube.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': current_snippet
                }
            ).execute()

            print("✓ Main language metadata updated successfully")
            self._update_localization(video_id, localized_metadata)
            return response

        except HttpError as e:
            print(f"✗ Error updating metadata: {e}")
            return None
    
    def _update_localization(self, video_id: str, localized_metadata: Dict):
        """Update localized titles and descriptions"""
        try:
            request = self.youtube.videos().update(
                part='localizations',
                body={
                    'id': video_id,
                    'localizations': localized_metadata
                }
            )
            
            response = request.execute()
            print("✓ Localized metadata updated successfully")
            return response

        except HttpError as e:
            print(f"✗ Error updating localization: {e}")
            return None
    
    def upload_subtitle(self, video_id: str, language: str, subtitle_file: str, name: str):
        """Upload subtitle file to YouTube video"""
        try:
            request = self.youtube.captions().insert(
                part='snippet',
                body={
                    'snippet': {
                        'videoId': video_id,
                        'name': name,
                        'language': language,
                        'isDraft': False
                    }
                },
                media_body=MediaFileUpload(subtitle_file, mimetype='application/octet-stream')
            )

            response = request.execute()
            print(f'✓ Subtitle uploaded for {language}')
            return response

        except Exception as e:
            print(f'✗ Error uploading subtitle for {language}: {e}')
            return None
    
    def update_tags(self, video_id: str, tag_string: str):
        """Update video tags"""
        try:
            video_response = self.youtube.videos().list(
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

                    self.youtube.videos().update(
                        part='snippet',
                        body={
                            'id': video_id,
                            'snippet': current_snippet
                        }
                    ).execute()

                    print("✓ Tags updated successfully")
                    return True
                    
            print("✗ Failed to update tags")
            return False

        except HttpError as e:
            print(f"✗ Error updating tags: {e}")
            return False
    
    @staticmethod
    def extract_video_id(video_link: str) -> str:
        """Extract YouTube video ID from URL"""
        if "youtu.be" in video_link:
            return video_link.split("/")[-1].split("?")[0]
        else:
            return video_link.split("=")[-1].split("&")[0]
