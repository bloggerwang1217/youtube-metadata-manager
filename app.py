"""
FastAPI Application with SQLAdmin Dashboard
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqladmin import Admin, ModelView, BaseView
from sqladmin import expose
from sqlalchemy import create_engine
from typing import List
import aiofiles
from pathlib import Path

from models import Video, Music, Style, Work, Streaming, Version, Creator, Role
from services.youtube_service import YouTubeService
from services.database_service import DatabaseService
from services.description_service import DescriptionService
from services.video_sync_service import VideoSyncService

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# YouTube configuration
CLIENT_SECRETS_FILE = os.getenv('CLIENT_SECRETS_FILE')
API_KEY = os.getenv('YOUTUBE_API_KEY')

# Create FastAPI app
app = FastAPI(title="YouTube Metadata Manager", version="2.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)

# Create admin interface with custom title
admin = Admin(
    app, 
    engine,
    title="YouTube Metadata Manager",
    base_url="/admin"
)

# Initialize services
youtube_service = YouTubeService(CLIENT_SECRETS_FILE)
db_service = DatabaseService(DATABASE_URL)


# Add navigation links at the top with category
class DashboardLink(BaseView):
    name = "Dashboard 首頁"
    icon = "fa-solid fa-home"
    category = "🚀 快速導航"
    
    @expose("/redirect-home", methods=["GET"])
    async def redirect_home(self, request: Request):
        return RedirectResponse(url="/")


class VideoSyncLink(BaseView):
    name = "Video Sync Manager"
    icon = "fa-solid fa-sync-alt"
    category = "🚀 快速導航"
    
    @expose("/redirect-video", methods=["GET"])
    async def redirect_video(self, request: Request):
        return RedirectResponse(url="/video")


# Add navigation links first
admin.add_view(DashboardLink)
admin.add_view(VideoSyncLink)

# Add all data management views with category
class WorkAdmin(ModelView, model=Work):
    name = "Work"
    name_plural = "Works"
    icon = "fa-solid fa-book"
    category = "📊 資料管理"
    
    column_list = [Work.WorkID, Work.Type, Work.JaName, Work.ZhHantName, Work.EnName]
    column_searchable_list = [Work.JaName, Work.ZhHantName, Work.EnName]
    column_sortable_list = [Work.WorkID, Work.Type]
    column_default_sort = (Work.WorkID, True)


class MusicAdmin(ModelView, model=Music):
    name = "Music"
    name_plural = "Music"
    icon = "fa-solid fa-music"
    category = "📊 資料管理"
    
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
    category = "📊 資料管理"
    
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
    category = "🔗 關聯資料"
    
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
    category = "📊 資料管理"
    
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
    category = "🔗 關聯資料"
    
    column_list = [Version.ID, Version.StreamingID, Version.MusicID, Version.Version]
    column_sortable_list = [Version.ID, Version.StreamingID, Version.MusicID]
    column_default_sort = (Version.ID, True)


class CreatorAdmin(ModelView, model=Creator):
    name = "Creator"
    name_plural = "Creators"
    icon = "fa-solid fa-user"
    category = "📊 資料管理"
    
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
    category = "🔗 關聯資料"
    
    column_list = [Role.RoleID, Role.CreatorID, Role.MusicID, Role.Role]
    column_sortable_list = [Role.RoleID, Role.CreatorID, Role.MusicID]
    column_default_sort = (Role.RoleID, True)


# Add all data management views
admin.add_view(WorkAdmin)
admin.add_view(MusicAdmin)
admin.add_view(VideoAdmin)
admin.add_view(StreamingAdmin)
admin.add_view(CreatorAdmin)
admin.add_view(StyleAdmin)
admin.add_view(VersionAdmin)
admin.add_view(RoleAdmin)


# Redirect /admin to /admin/video/list
@app.get("/admin", include_in_schema=False)
async def redirect_admin():
    """Redirect admin root to video list"""
    return RedirectResponse(url="/admin/video/list")



# ============ Video Sync Routes ============

@app.get("/video", response_class=HTMLResponse)
async def video_sync_page(request: Request):
    """Video sync management page"""
    session = db_service.get_session()
    try:
        videos = session.query(Video).order_by(Video.VideoID.desc()).all()
        return templates.TemplateResponse("video_sync.html", {
            "request": request,
            "videos": videos
        })
    finally:
        session.close()


@app.post("/api/upload-subtitles/{video_id}")
async def upload_subtitles(video_id: int, files: List[UploadFile] = File(...)):
    """Upload subtitle files for a video"""
    try:
        # Create temp directory for this video
        temp_dir = Path("temp") / str(video_id)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        for file in files:
            if file.filename.endswith('.srt'):
                file_path = temp_dir / file.filename
                async with aiofiles.open(file_path, 'wb') as f:
                    content = await file.read()
                    await f.write(content)
                uploaded_files.append(file.filename)
        
        return JSONResponse({
            "success": True,
            "uploaded_files": uploaded_files
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)


@app.post("/api/sync-video/{video_id}")
async def sync_video(video_id: int):
    """Sync video metadata and subtitles to YouTube"""
    try:
        # Get video data from database
        video_data = db_service.get_video_metadata(video_id)
        if not video_data:
            return JSONResponse({
                "success": False,
                "message": "Video not found in database"
            }, status_code=404)
        
        # Check YouTube link
        if not video_data.get('YouTubeLink'):
            return JSONResponse({
                "success": False,
                "message": "YouTube link not set"
            }, status_code=400)
        
        # Authenticate with YouTube
        youtube_service.authenticate()
        
        # Extract YouTube video ID
        yt_video_id = VideoSyncService.extract_video_id_from_link(video_data['YouTubeLink'])
        
        # Step 1: Upload subtitles (if available)
        subtitle_names = {
            'Lyrics': {'ja': "歌詞", "en": "English Lyrics Translation", "zh-Hant": "中文歌詞翻譯"},
            'BloggerTalk': {'ja': "僕の心の話", "en": "My heartfelt story", "zh-Hant": "我心裡的話"}
        }
        name = subtitle_names.get(video_data.get('SubtitleType', 'Lyrics'), subtitle_names['Lyrics'])
        
        temp_dir = Path("temp") / str(video_id)
        subtitle_uploaded = False
        if temp_dir.exists():
            for language_code in ['ja', 'en', 'zh-Hant']:
                subtitle_file = temp_dir / f"{language_code}_subtitle.srt"
                if subtitle_file.exists():
                    try:
                        youtube_service.upload_subtitle(
                            yt_video_id, 
                            language_code, 
                            str(subtitle_file), 
                            name[language_code]
                        )
                        subtitle_uploaded = True
                    except Exception as e:
                        print(f"Warning: Failed to upload {language_code} subtitle: {e}")
                        # Continue even if subtitle upload fails
        
        # Step 2: Generate and update descriptions/titles
        info_dict = DescriptionService.prepare_info_dict(video_data)
        inst_type = "instrumental" if video_data.get('InstrumentalType') == 'Inst' else "piano"
        
        languages = ['ja', 'en', 'zh-Hant']
        language_map = {'ja': 'JaTitle', 'en': 'EnTitle', 'zh-Hant': 'ZhHantTitle'}
        
        localized_metadata = {}
        for language_code in languages:
            title = video_data.get(language_map[language_code])
            description = DescriptionService.generate(info_dict, inst_type, language=language_code)
            localized_metadata[language_code] = {"title": title, "description": description}
        
        youtube_service.update_video_metadata(yt_video_id, localized_metadata, 10)
        
        # Step 3: Fetch video info from YouTube and update database
        video_info = VideoSyncService.get_video_info(youtube_service.youtube, yt_video_id)
        
        if video_info:
            # Update database with duration and upload time
            db_service.update_video(video_id, {
                'Length': video_info['duration'],
                'UploadTime': video_info['upload_time']
            })
        
        # Clean up temp files
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        return JSONResponse({
            "success": True,
            "message": "Sync completed successfully",
            "subtitle_uploaded": subtitle_uploaded,
            "video_info": {
                "duration": video_info['duration'] if video_info else None,
                "upload_time": video_info['upload_time'].isoformat() if video_info else None
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)


@app.post("/api/batch-sync")
async def batch_sync(request: Request):
    """Batch sync multiple videos"""
    try:
        body = await request.json()
        video_ids = body.get('video_ids', [])
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'details': []
        }
        
        for video_id in video_ids:
            try:
                # Note: In production, this should be done asynchronously
                # For now, we process sequentially
                result = await sync_video(video_id)
                if result.status_code == 200:
                    results['success_count'] += 1
                    results['details'].append({
                        'video_id': video_id,
                        'status': 'success'
                    })
                else:
                    results['failed_count'] += 1
                    results['details'].append({
                        'video_id': video_id,
                        'status': 'failed',
                        'error': result.body.decode()
                    })
            except Exception as e:
                results['failed_count'] += 1
                results['details'].append({
                    'video_id': video_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return JSONResponse(results)
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)


@app.get("/")
async def root(request: Request):
    """Dashboard home page with statistics"""
    session = db_service.get_session()
    try:
        # Get statistics
        video_count = session.query(Video).count()
        video_with_link = session.query(Video).filter(Video.YouTubeLink.isnot(None)).count()
        music_count = session.query(Music).count()
        work_count = session.query(Work).count()
        streaming_count = session.query(Streaming).count()
        style_count = session.query(Style).count()
        version_count = session.query(Version).count()
        creator_count = session.query(Creator).count()
        
        # Get recent videos (last 10)
        recent_videos = session.query(Video).order_by(Video.VideoID.desc()).limit(10).all()
        
        stats = {
            'video_count': video_count,
            'video_with_link': video_with_link,
            'music_count': music_count,
            'work_count': work_count,
            'streaming_count': streaming_count,
            'style_count': style_count,
            'version_count': version_count,
            'creator_count': creator_count
        }
        
        return templates.TemplateResponse("dashboard_home.html", {
            "request": request,
            "stats": stats,
            "recent_videos": recent_videos
        })
    finally:
        session.close()


@app.get("/health")
async def health():
    return {"status": "healthy", "database": DATABASE_URL.split("@")[1]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
