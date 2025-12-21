"""
FastAPI Application with SQLAdmin Dashboard
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqlalchemy import create_engine

from models import Video, Music, Style, Work, Streaming, Version, Creator, Role

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create FastAPI app
app = FastAPI(title="YouTube Metadata Manager", version="2.0")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)

# Create admin interface
admin = Admin(app, engine)


# Define admin views for each model
class WorkAdmin(ModelView, model=Work):
    name = "Work"
    name_plural = "Works"
    icon = "fa-solid fa-book"
    
    column_list = [Work.WorkID, Work.Type, Work.JaName, Work.ZhHantName, Work.EnName]
    column_searchable_list = [Work.JaName, Work.ZhHantName, Work.EnName]
    column_sortable_list = [Work.WorkID, Work.Type]
    column_default_sort = (Work.WorkID, True)


class MusicAdmin(ModelView, model=Music):
    name = "Music"
    name_plural = "Music"
    icon = "fa-solid fa-music"
    
    column_list = [
        Music.MusicID,
        Music.WorkID,
        Music.JaName,
        Music.ZhHantName,
        Music.EnName,
        Music.ThemeType,
    ]
    
    column_searchable_list = [Music.JaName, Music.ZhHantName, Music.EnName]
    column_sortable_list = [Music.MusicID, Music.WorkID]
    column_default_sort = (Music.MusicID, True)
    
    # Show relationships
    column_details_exclude_list = []
    can_view_details = True


class VideoAdmin(ModelView, model=Video):
    name = "Video"
    name_plural = "Videos"
    icon = "fa-solid fa-video"
    
    column_list = [
        Video.VideoID, 
        Video.ZhHantTitle, 
        Video.JaTitle,
        Video.EnTitle,
        Video.YouTubeLink,
        Video.UploadTime,
        Video.InstrumentalType,
        Video.SubtitleType
    ]
    
    column_searchable_list = [Video.ZhHantTitle, Video.JaTitle, Video.EnTitle, Video.YouTubeLink]
    column_sortable_list = [Video.VideoID, Video.UploadTime]
    column_default_sort = (Video.VideoID, True)
    
    # Enable details view
    can_view_details = True
    
    # Group form fields
    form_columns = [
        Video.YouTubeLink,
        Video.UploadTime,
        Video.ZhHantTitle,
        Video.JaTitle,
        Video.EnTitle,
        Video.ZhHantDescription,
        Video.JaDescription,
        Video.EnDescription,
        Video.ZhHantSubSource,
        Video.JaSubSource,
        Video.EnSubSource,
        Video.Instrumental,
        Video.Sheet,
        Video.InstrumentalType,
        Video.SubtitleType,
        Video.GumroadSheet,
        Video.Length
    ]


class StyleAdmin(ModelView, model=Style):
    name = "Style"
    name_plural = "Styles (Video-Music Link)"
    icon = "fa-solid fa-link"
    
    column_list = [Style.ID, Style.VideoID, Style.MusicID, Style.Style]
    column_sortable_list = [Style.ID, Style.VideoID, Style.MusicID]
    column_default_sort = (Style.ID, True)
    
    # Show related objects in form
    form_ajax_refs = {
        'video': {
            'fields': ('ZhHantTitle', 'JaTitle'),
            'order_by': 'VideoID',
        },
        'music': {
            'fields': ('JaName', 'ZhHantName'),
            'order_by': 'MusicID',
        }
    }


class StreamingAdmin(ModelView, model=Streaming):
    name = "Streaming"
    name_plural = "Streaming Releases"
    icon = "fa-solid fa-compact-disc"
    
    column_list = [
        Streaming.StreamingID,
        Streaming.JaTitle,
        Streaming.ZhHantTitle,
        Streaming.EnTitle,
        Streaming.InstrumentalType,
        Streaming.SmartLink
    ]
    
    column_searchable_list = [Streaming.JaTitle, Streaming.ZhHantTitle, Streaming.EnTitle]
    column_sortable_list = [Streaming.StreamingID]
    column_default_sort = (Streaming.StreamingID, True)
    can_view_details = True


class VersionAdmin(ModelView, model=Version):
    name = "Version"
    name_plural = "Versions (Streaming-Music Link)"
    icon = "fa-solid fa-code-branch"
    
    column_list = [Version.ID, Version.StreamingID, Version.MusicID, Version.Version]
    column_sortable_list = [Version.ID, Version.StreamingID, Version.MusicID]
    column_default_sort = (Version.ID, True)


class CreatorAdmin(ModelView, model=Creator):
    name = "Creator"
    name_plural = "Creators"
    icon = "fa-solid fa-user"
    
    column_list = [
        Creator.CreatorID,
        Creator.CreatorName,
        Creator.ChannelName,
        Creator.ChannelLink
    ]
    
    column_searchable_list = [Creator.CreatorName, Creator.ChannelName]
    column_sortable_list = [Creator.CreatorID]
    column_default_sort = (Creator.CreatorID, True)
    can_view_details = True


class RoleAdmin(ModelView, model=Role):
    name = "Role"
    name_plural = "Roles (Creator-Music Link)"
    icon = "fa-solid fa-user-tag"
    
    column_list = [Role.RoleID, Role.CreatorID, Role.MusicID, Role.Role]
    column_sortable_list = [Role.RoleID, Role.CreatorID, Role.MusicID]
    column_default_sort = (Role.RoleID, True)


# Add all views to admin in logical order
admin.add_view(WorkAdmin)
admin.add_view(MusicAdmin)
admin.add_view(VideoAdmin)
admin.add_view(StyleAdmin)
admin.add_view(StreamingAdmin)
admin.add_view(VersionAdmin)
admin.add_view(CreatorAdmin)
admin.add_view(RoleAdmin)


@app.get("/")
async def root():
    return {
        "message": "YouTube Metadata Manager API v2.0",
        "admin_dashboard": "/admin",
        "api_docs": "/docs",
        "tables": ["Work", "Music", "Video", "Style", "Streaming", "Version", "Creator", "Role"]
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "database": DATABASE_URL.split("@")[1]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
