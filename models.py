"""
Database models using SQLAlchemy ORM
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Work(Base):
    __tablename__ = 'Work'
    
    WorkID = Column(Integer, primary_key=True, autoincrement=True)
    Type = Column(String(20), nullable=False)
    ZhHantName = Column(String(100))
    JaName = Column(String(100))
    EnName = Column(String(100))
    
    # Relationships
    music = relationship("Music", back_populates="work")
    
    def __repr__(self):
        return f"<Work {self.WorkID}: {self.JaName}>"


class Music(Base):
    __tablename__ = 'Music'
    
    MusicID = Column(Integer, primary_key=True, autoincrement=True)
    WorkID = Column(Integer, ForeignKey('Work.WorkID'), nullable=False)
    ZhHantName = Column(String(100))
    JaName = Column(String(100))
    EnName = Column(String(100))
    ThemeType = Column(String(20))
    SpotifyID = Column(String(30))
    MV = Column(String(60))
    OfficialArtist = Column(String(20))
    
    # Relationships
    work = relationship("Work", back_populates="music")
    styles = relationship("Style", back_populates="music")
    roles = relationship("Role", back_populates="music")
    versions = relationship("Version", back_populates="music")
    
    def __repr__(self):
        title = self.JaName or self.EnName or self.ZhHantName or ""
        return f"<Music {self.MusicID}: {title}>"


class Video(Base):
    __tablename__ = 'Video'
    
    VideoID = Column(Integer, primary_key=True, autoincrement=True)
    YouTubeLink = Column(String(60))
    UploadTime = Column(DateTime)
    ZhHantTitle = Column(String(100))
    JaTitle = Column(String(100))
    EnTitle = Column(String(100))
    ZhHantDescription = Column(String(300))
    JaDescription = Column(String(300))
    EnDescription = Column(String(300))
    ZhHantSubSource = Column(String(200))
    JaSubSource = Column(String(200))
    EnSubSource = Column(String(200))
    Instrumental = Column(String(200))
    Sheet = Column(String(100))
    InstrumentalType = Column(String(20))
    SubtitleType = Column(String(20))
    GumroadSheet = Column(String(100))
    Length = Column(Integer)
    
    # Relationships
    styles = relationship("Style", back_populates="video")
    
    def __repr__(self):
        return f"<Video {self.VideoID}: {self.ZhHantTitle}>"


class Style(Base):
    __tablename__ = 'Style'
    
    ID = Column(Integer, primary_key=True, autoincrement=True)
    VideoID = Column(Integer, ForeignKey('Video.VideoID'), nullable=False)
    MusicID = Column(Integer, ForeignKey('Music.MusicID'), nullable=False)
    Style = Column(String(20), nullable=False)
    
    # Relationships
    video = relationship("Video", back_populates="styles")
    music = relationship("Music", back_populates="styles")
    
    def __repr__(self):
        return f"<Style {self.ID}: VideoID={self.VideoID}, MusicID={self.MusicID}>"


class Streaming(Base):
    __tablename__ = 'Streaming'
    
    StreamingID = Column(Integer, primary_key=True, autoincrement=True)
    EnTitle = Column(String(300))
    JaTitle = Column(String(300))
    ZhHantTitle = Column(String(300))
    ZhHansTitle = Column(String(300))
    Instrumental = Column(String(100))
    InstrumentalType = Column(String(20))
    SmartLink = Column(String(300))
    
    # Relationships
    versions = relationship("Version", back_populates="streaming")
    
    def __repr__(self):
        title = self.JaTitle or self.EnTitle or self.ZhHantTitle or self.ZhHansTitle or ""
        return f"<Streaming {self.StreamingID}: {title}>"


class Version(Base):
    __tablename__ = 'Version'
    
    ID = Column(Integer, primary_key=True, autoincrement=True)
    StreamingID = Column(Integer, ForeignKey('Streaming.StreamingID'), nullable=False)
    MusicID = Column(Integer, ForeignKey('Music.MusicID'), nullable=False)
    Version = Column(String(20), nullable=False)
    
    # Relationships
    streaming = relationship("Streaming", back_populates="versions")
    music = relationship("Music", back_populates="versions")
    
    def __repr__(self):
        return f"<Version {self.ID}: StreamingID={self.StreamingID}, MusicID={self.MusicID}>"


class Creator(Base):
    __tablename__ = 'Creator'
    
    CreatorID = Column(Integer, primary_key=True, autoincrement=True)
    CreatorName = Column(String(100))
    ChannelName = Column(String(100))
    ChannelLink = Column(String(60))
    
    # Relationships
    roles = relationship("Role", back_populates="creator")
    
    def __repr__(self):
        return f"<Creator {self.CreatorID}: {self.CreatorName}>"


class Role(Base):
    __tablename__ = 'Role'
    
    RoleID = Column(Integer, primary_key=True, autoincrement=True)
    CreatorID = Column(Integer, ForeignKey('Creator.CreatorID'), nullable=False)
    MusicID = Column(Integer, ForeignKey('Music.MusicID'), nullable=False)
    Role = Column(String(20), nullable=False)
    
    # Relationships
    creator = relationship("Creator", back_populates="roles")
    music = relationship("Music", back_populates="roles")
    
    def __repr__(self):
        return f"<Role {self.RoleID}: Creator={self.CreatorID}, Music={self.MusicID}>"
