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
from sqlalchemy import create_engine, or_
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
    base_url="/admin",
    templates_dir="templates"
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
        Music.ThemeType
    ]
    
    column_searchable_list = [Music.JaName, Music.ZhHantName, Music.EnName]
    column_sortable_list = [Music.MusicID, Music.WorkID]
    column_default_sort = (Music.MusicID, True)
    
    # Show relationships
    column_details_exclude_list = []
    can_view_details = True


from sqladmin import ModelView
from wtforms import SelectField


class VideoAdmin(ModelView, model=Video):
    name = "Video"
    name_plural = "Videos"
    icon = "fa-solid fa-video"
    category = "📊 資料管理"
    
    column_list = [
        Video.VideoID, 
        Video.JaTitle,
        Video.YouTubeLink,
        Video.UploadTime,
        Video.Length
    ]
    
    # 格式化欄位顯示
    column_formatters = {
        Video.JaTitle: lambda m, a: (m.JaTitle or m.ZhHantTitle or m.EnTitle or '(未設定)')[:35] + ('...' if (m.JaTitle or m.ZhHantTitle or m.EnTitle or '') and len(m.JaTitle or m.ZhHantTitle or m.EnTitle or '') > 35 else '')
    }
    
    column_searchable_list = [Video.ZhHantTitle, Video.JaTitle, Video.EnTitle, Video.YouTubeLink]
    column_sortable_list = [Video.VideoID, Video.UploadTime, Video.Length]
    column_default_sort = [(Video.VideoID, True)]
    
    # Enable details view
    can_view_details = True
    can_create = True
    can_edit = True
    can_delete = True
    
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
    
    column_list = [Style.ID, 'video', 'music', Style.Style]
    column_sortable_list = [Style.ID]
    column_default_sort = [(Style.ID, True)]
    column_searchable_list = ["Style"]
    
    # 表單使用 AJAX 搜尋（Video 和 Music）
    form_ajax_refs = {
        'video': {
            'fields': ('VideoID', 'JaTitle', 'ZhHantTitle'),
            'order_by': Video.VideoID,
        },
        'music': {
            'fields': ('MusicID', 'JaName', 'ZhHantName'),
            'order_by': Music.MusicID,
        }
    }
    
    # Style 欄位配置
    form_args = {
        'Style': {
            'default': 'Cover',
            'description': '常用選項：Cover, ShortCover, Collection, ShortMeme, ShortLife'
        }
    }

    def search_query(self, stmt, term):
        if not term:
            return stmt
        like_term = f"%{term}%"
        return (
            stmt.join(Style.video)
                .join(Style.music)
                .where(
                    or_(
                        Style.Style.ilike(like_term),
                        Video.JaTitle.ilike(like_term),
                        Video.ZhHantTitle.ilike(like_term),
                        Video.EnTitle.ilike(like_term),
                        Music.JaName.ilike(like_term),
                        Music.ZhHantName.ilike(like_term),
                        Music.EnName.ilike(like_term),
                    )
                )
        )


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
    
    column_list = [Version.ID, 'streaming', 'music', Version.Version]
    column_sortable_list = [Version.ID]
    column_default_sort = [(Version.ID, True)]
    column_searchable_list = ["Version"]
    
    # 表單使用 AJAX 搜尋
    form_ajax_refs = {
        'streaming': {
            'fields': ('JaTitle', 'EnTitle', 'ZhHantTitle', 'ZhHansTitle'),
            'order_by': Streaming.StreamingID,
        },
        'music': {
            'fields': ('JaName', 'EnName', 'ZhHantName'),
            'order_by': Music.MusicID,
        }
    }
    
    # Version 欄位配置
    form_args = {
        'Version': {
            'description': '常用選項：Inst, Piano'
        }
    }

    def search_query(self, stmt, term):
        if not term:
            return stmt
        like_term = f"%{term}%"
        return (
            stmt.join(Version.streaming)
                .join(Version.music)
                .where(
                    or_(
                        Version.Version.ilike(like_term),
                        Streaming.JaTitle.ilike(like_term),
                        Streaming.EnTitle.ilike(like_term),
                        Streaming.ZhHantTitle.ilike(like_term),
                        Music.JaName.ilike(like_term),
                        Music.ZhHantName.ilike(like_term),
                        Music.EnName.ilike(like_term),
                    )
                )
        )


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
    
    column_list = [Role.RoleID, 'creator', 'music', Role.Role]
    column_sortable_list = [Role.RoleID]
    column_default_sort = [(Role.RoleID, True)]
    column_searchable_list = ["Role"]
    
    # 表單使用 AJAX 搜尋
    form_ajax_refs = {
        'creator': {
            'fields': ('CreatorID', 'CreatorName', 'ChannelName'),
            'order_by': Creator.CreatorID,
        },
        'music': {
            'fields': ('MusicID', 'JaName', 'ZhHantName'),
            'order_by': Music.MusicID,
        }
    }
    
    # Role 欄位配置
    form_args = {
        'Role': {
            'description': '常用選項：Artist, Composer, Singer'
        }
    }

    def search_query(self, stmt, term):
        if not term:
            return stmt
        like_term = f"%{term}%"
        return (
            stmt.join(Role.creator)
                .join(Role.music)
                .where(
                    or_(
                        Role.Role.ilike(like_term),
                        Creator.CreatorName.ilike(like_term),
                        Creator.ChannelName.ilike(like_term),
                        Music.JaName.ilike(like_term),
                        Music.ZhHantName.ilike(like_term),
                        Music.EnName.ilike(like_term),
                    )
                )
        )


def _clone_video(session, video_id: int):
    original = session.query(Video).filter(Video.VideoID == video_id).first()
    if not original:
        return None

    new_video = Video(
        YouTubeLink=None,
        UploadTime=None,
        ZhHantTitle=original.ZhHantTitle,
        JaTitle=original.JaTitle,
        EnTitle=original.EnTitle,
        ZhHantDescription=original.ZhHantDescription,
        JaDescription=original.JaDescription,
        EnDescription=original.EnDescription,
        ZhHantSubSource=original.ZhHantSubSource,
        JaSubSource=original.JaSubSource,
        EnSubSource=original.EnSubSource,
        Instrumental=original.Instrumental,
        Sheet=original.Sheet,
        InstrumentalType=original.InstrumentalType,
        SubtitleType=original.SubtitleType,
        GumroadSheet=original.GumroadSheet,
        Length=None
    )

    session.add(new_video)
    session.commit()
    session.refresh(new_video)

    original_styles = session.query(Style).filter(Style.VideoID == video_id).all()
    for style in original_styles:
        session.add(Style(VideoID=new_video.VideoID, MusicID=style.MusicID, Style=style.Style))
    session.commit()
    return new_video.VideoID


def _clone_work(session, work_id: int):
    original = session.query(Work).filter(Work.WorkID == work_id).first()
    if not original:
        return None
    new_work = Work(Type=original.Type, JaName=original.JaName, ZhHantName=original.ZhHantName, EnName=original.EnName)
    session.add(new_work)
    session.commit()
    session.refresh(new_work)
    return new_work.WorkID


def _clone_music(session, music_id: int):
    original = session.query(Music).filter(Music.MusicID == music_id).first()
    if not original:
        return None
    new_music = Music(
        WorkID=original.WorkID,
        JaName=original.JaName,
        ZhHantName=original.ZhHantName,
        EnName=original.EnName,
        ThemeType=original.ThemeType,
        SpotifyID=original.SpotifyID,
        MV=original.MV,
        OfficialArtist=original.OfficialArtist
    )
    session.add(new_music)
    session.commit()
    session.refresh(new_music)

    original_roles = session.query(Role).filter(Role.MusicID == music_id).all()
    for role in original_roles:
        session.add(Role(CreatorID=role.CreatorID, MusicID=new_music.MusicID, Role=role.Role))
    session.commit()
    return new_music.MusicID


def _clone_streaming(session, streaming_id: int):
    original = session.query(Streaming).filter(Streaming.StreamingID == streaming_id).first()
    if not original:
        return None
    new_streaming = Streaming(
        EnTitle=original.EnTitle,
        JaTitle=original.JaTitle,
        ZhHantTitle=original.ZhHantTitle,
        ZhHansTitle=original.ZhHansTitle,
        Instrumental=original.Instrumental,
        InstrumentalType=original.InstrumentalType,
        SmartLink=None
    )
    session.add(new_streaming)
    session.commit()
    session.refresh(new_streaming)

    original_versions = session.query(Version).filter(Version.StreamingID == streaming_id).all()
    for version in original_versions:
        session.add(Version(StreamingID=new_streaming.StreamingID, MusicID=version.MusicID, Version=version.Version))
    session.commit()
    return new_streaming.StreamingID


def _clone_creator(session, creator_id: int):
    original = session.query(Creator).filter(Creator.CreatorID == creator_id).first()
    if not original:
        return None
    new_creator = Creator(
        CreatorName=f"{original.CreatorName} (Copy)",
        ChannelName=original.ChannelName,
        ChannelLink=None
    )
    session.add(new_creator)
    session.commit()
    session.refresh(new_creator)
    return new_creator.CreatorID


@app.api_route("/api/clone/{entity}/{pk}", methods=["GET", "POST"])
async def api_clone(entity: str, pk: int):
    session = db_service.get_session()
    try:
        new_id = None
        if entity == "video":
            new_id = _clone_video(session, pk)
        elif entity == "work":
            new_id = _clone_work(session, pk)
        elif entity == "music":
            new_id = _clone_music(session, pk)
        elif entity == "streaming":
            new_id = _clone_streaming(session, pk)
        elif entity == "creator":
            new_id = _clone_creator(session, pk)

        if not new_id:
            return JSONResponse({"success": False, "message": "Record not found"}, status_code=404)
        return JSONResponse({"success": True, "new_id": new_id, "message": "複製成功"})
    except Exception as e:
        session.rollback()
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        session.close()


@app.get("/admin/video/clone/{video_id}")
async def clone_video(video_id: int, request: Request):
    """Clone a video record"""
    session = db_service.get_session()
    try:
        new_id = _clone_video(session, video_id)
        if not new_id:
            return RedirectResponse(url="/admin/video/list", status_code=303)
        return RedirectResponse(url=f"/admin/video/edit/{new_id}", status_code=303)
    finally:
        session.close()


@app.get("/admin/work/clone/{work_id}")
async def clone_work(work_id: int):
    """Clone a work record"""
    session = db_service.get_session()
    try:
        new_id = _clone_work(session, work_id)
        if not new_id:
            return RedirectResponse(url="/admin/work/list", status_code=303)
        return RedirectResponse(url=f"/admin/work/edit/{new_id}", status_code=303)
    finally:
        session.close()


@app.get("/admin/music/clone/{music_id}")
async def clone_music(music_id: int):
    """Clone a music record"""
    session = db_service.get_session()
    try:
        new_id = _clone_music(session, music_id)
        if not new_id:
            return RedirectResponse(url="/admin/music/list", status_code=303)
        return RedirectResponse(url=f"/admin/music/edit/{new_id}", status_code=303)
    finally:
        session.close()


@app.get("/admin/streaming/clone/{streaming_id}")
async def clone_streaming(streaming_id: int):
    """Clone a streaming record"""
    session = db_service.get_session()
    try:
        new_id = _clone_streaming(session, streaming_id)
        if not new_id:
            return RedirectResponse(url="/admin/streaming/list", status_code=303)
        return RedirectResponse(url=f"/admin/streaming/edit/{new_id}", status_code=303)
    finally:
        session.close()


@app.get("/admin/creator/clone/{creator_id}")
async def clone_creator(creator_id: int):
    """Clone a creator record"""
    session = db_service.get_session()
    try:
        new_id = _clone_creator(session, creator_id)
        if not new_id:
            return RedirectResponse(url="/admin/creator/list", status_code=303)
        return RedirectResponse(url=f"/admin/creator/edit/{new_id}", status_code=303)
    finally:
        session.close()


# Add all data management views (ordered for sidebar)
admin.add_view(VideoAdmin)
admin.add_view(WorkAdmin)
admin.add_view(MusicAdmin)
admin.add_view(CreatorAdmin)
admin.add_view(StreamingAdmin)
admin.add_view(StyleAdmin)
admin.add_view(RoleAdmin)
admin.add_view(VersionAdmin)


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
async def sync_video(video_id: int, subtitle_type: str = None):
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
        # Use provided subtitle_type or fall back to database value or default
        selected_type = subtitle_type if subtitle_type else video_data.get('SubtitleType', 'Lyrics')
        name = subtitle_names.get(selected_type, subtitle_names['Lyrics'])
        
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


# ============ Clone Routes ============

@app.get("/api/clone/video/{video_id}")
async def clone_video(video_id: int):
    """Clone a video record"""
    session = db_service.get_session()
    try:
        new_id = _clone_video(session, video_id)
        if not new_id:
            return JSONResponse({"success": False, "message": "Video not found"}, status_code=404)
        return JSONResponse({
            "success": True,
            "new_id": new_id,
            "message": f"Video cloned successfully! New ID: {new_id}"
        })
        
    except Exception as e:
        session.rollback()
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        session.close()


@app.get("/api/clone/music/{music_id}")
async def clone_music(music_id: int):
    """Clone a music record"""
    session = db_service.get_session()
    try:
        new_id = _clone_music(session, music_id)
        if not new_id:
            return JSONResponse({"success": False, "message": "Music not found"}, status_code=404)
        return JSONResponse({
            "success": True,
            "new_id": new_id,
            "message": f"Music cloned successfully! New ID: {new_id}"
        })
        
    except Exception as e:
        session.rollback()
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        session.close()


@app.get("/api/clone/streaming/{streaming_id}")
async def clone_streaming(streaming_id: int):
    """Clone a streaming record"""
    session = db_service.get_session()
    try:
        new_id = _clone_streaming(session, streaming_id)
        if not new_id:
            return JSONResponse({"success": False, "message": "Streaming not found"}, status_code=404)
        return JSONResponse({
            "success": True,
            "new_id": new_id,
            "message": f"Streaming cloned successfully! New ID: {new_id}"
        })
        
    except Exception as e:
        session.rollback()
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        session.close()


@app.get("/api/clone/creator/{creator_id}")
async def clone_creator(creator_id: int):
    """Clone a creator record"""
    session = db_service.get_session()
    try:
        new_id = _clone_creator(session, creator_id)
        if not new_id:
            return JSONResponse({"success": False, "message": "Creator not found"}, status_code=404)
        return JSONResponse({
            "success": True,
            "new_id": new_id,
            "message": f"Creator cloned successfully! New ID: {new_id}"
        })
        
    except Exception as e:
        session.rollback()
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        session.close()


@app.get("/health")
async def health():
    return {"status": "healthy", "database": DATABASE_URL.split("@")[1]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
