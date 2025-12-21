"""
Database Service
Handles all database operations using SQLAlchemy
"""
from typing import Optional, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Video, Style, Music


class DatabaseService:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def get_video_metadata(self, video_id: int) -> Optional[Dict]:
        """Fetch video metadata with related Music info"""
        session = self.get_session()
        try:
            # Query with joins
            result = session.query(Video, Style, Music)\
                .join(Style, Video.VideoID == Style.VideoID)\
                .join(Music, Style.MusicID == Music.MusicID)\
                .filter(Video.VideoID == video_id)\
                .first()
            
            if not result:
                return None
            
            video, style, music = result
            
            # Convert to dictionary
            video_dict = {
                'VideoID': video.VideoID,
                'YouTubeLink': video.YouTubeLink,
                'UploadTime': video.UploadTime,
                'ZhHantTitle': video.ZhHantTitle,
                'JaTitle': video.JaTitle,
                'EnTitle': video.EnTitle,
                'ZhHantDescription': video.ZhHantDescription,
                'JaDescription': video.JaDescription,
                'EnDescription': video.EnDescription,
                'ZhHantSubSource': video.ZhHantSubSource,
                'JaSubSource': video.JaSubSource,
                'EnSubSource': video.EnSubSource,
                'Instrumental': video.Instrumental,
                'Sheet': video.Sheet,
                'InstrumentalType': video.InstrumentalType,
                'SubtitleType': video.SubtitleType,
                'GumroadSheet': video.GumroadSheet,
                'Length': video.Length,
                # Style fields
                'ID': style.ID,
                'MusicID': style.MusicID,
                'Style': style.Style,
                # Music fields
                'WorkID': music.WorkID,
                'ZhHantName': music.ZhHantName,
                'JaName': music.JaName,
                'EnName': music.EnName,
                'ThemeType': music.ThemeType,
                'SpotifyID': music.SpotifyID,
                'MV': music.MV,
                'OfficialArtist': music.OfficialArtist
            }
            
            return video_dict
            
        finally:
            session.close()
    
    def create_video(self, video_data: Dict) -> Video:
        """Create a new video entry"""
        session = self.get_session()
        try:
            video = Video(**video_data)
            session.add(video)
            session.commit()
            session.refresh(video)
            return video
        finally:
            session.close()
    
    def update_video(self, video_id: int, video_data: Dict) -> Optional[Video]:
        """Update an existing video"""
        session = self.get_session()
        try:
            video = session.query(Video).filter(Video.VideoID == video_id).first()
            if video:
                for key, value in video_data.items():
                    setattr(video, key, value)
                session.commit()
                session.refresh(video)
            return video
        finally:
            session.close()
    
    def create_music(self, music_data: Dict) -> Music:
        """Create a new music entry"""
        session = self.get_session()
        try:
            music = Music(**music_data)
            session.add(music)
            session.commit()
            session.refresh(music)
            return music
        finally:
            session.close()
    
    def create_style(self, style_data: Dict) -> Style:
        """Create a new style entry linking Video and Music"""
        session = self.get_session()
        try:
            style = Style(**style_data)
            session.add(style)
            session.commit()
            session.refresh(style)
            return style
        finally:
            session.close()
