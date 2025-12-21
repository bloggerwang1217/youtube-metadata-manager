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
        Returns: dict with duration (seconds) and scheduled publish time (datetime in UTC+8)
        """
        try:
            response = youtube.videos().list(
                part="contentDetails,snippet,status",
                id=video_id
            ).execute()
            
            if "items" not in response or not response["items"]:
                return None
            
            video = response["items"][0]
            
            # Parse duration (ISO 8601 format like PT3M45S)
            duration_iso = video["contentDetails"]["duration"]
            duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
            
            # Get publish time - prefer publishAt (scheduled) over publishedAt (first upload)
            publish_time_str = None
            if "status" in video and "publishAt" in video["status"]:
                # This is the scheduled publish time
                publish_time_str = video["status"]["publishAt"]
            else:
                # Fall back to publishedAt if no scheduled time
                publish_time_str = video["snippet"]["publishedAt"]
            
            # Parse and convert to UTC+8 (Taipei Time)
            publish_time_utc = datetime.strptime(publish_time_str, '%Y-%m-%dT%H:%M:%SZ')
            publish_time_taipei = publish_time_utc + timedelta(hours=8)
            
            return {
                "duration": duration_seconds,
                "upload_time": publish_time_taipei,
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
