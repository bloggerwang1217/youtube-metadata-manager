"""
Video Sync Service
Handles fetching video metadata from YouTube and syncing to database
"""
import isodate
from datetime import datetime, timedelta
from typing import Dict, Optional
from googleapiclient.discovery import Resource


class VideoSyncService:
    @staticmethod
    def get_video_info(youtube: Resource, video_id: str) -> Optional[Dict]:
        """
        Fetch video information from YouTube API
        Returns: dict with duration (seconds) and publishedAt (datetime in UTC+8)
        """
        try:
            response = youtube.videos().list(
                part="contentDetails,snippet",
                id=video_id
            ).execute()
            
            if "items" not in response or not response["items"]:
                return None
            
            video = response["items"][0]
            
            # Parse duration (ISO 8601 format like PT3M45S)
            duration_iso = video["contentDetails"]["duration"]
            duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
            
            # Parse publishedAt and convert to UTC+8 (Taipei Time)
            published_at_str = video["snippet"]["publishedAt"]
            published_at_utc = datetime.strptime(published_at_str, '%Y-%m-%dT%H:%M:%SZ')
            published_at_taipei = published_at_utc + timedelta(hours=8)
            
            return {
                "duration": duration_seconds,
                "upload_time": published_at_taipei,
                "title": video["snippet"]["title"],
                "description": video["snippet"]["description"]
            }
            
        except Exception as e:
            print(f"Error fetching video info: {e}")
            return None
    
    @staticmethod
    def extract_video_id_from_link(youtube_link: str) -> str:
        """Extract YouTube video ID from various URL formats"""
        if not youtube_link:
            return ""
        
        # Handle youtu.be/VIDEO_ID
        if "youtu.be" in youtube_link:
            return youtube_link.split("/")[-1].split("?")[0]
        
        # Handle youtube.com/watch?v=VIDEO_ID
        if "youtube.com" in youtube_link:
            if "v=" in youtube_link:
                return youtube_link.split("v=")[-1].split("&")[0]
        
        # Assume it's already a video ID
        return youtube_link
