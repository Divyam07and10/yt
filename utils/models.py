from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    youtube_id = Column(String, nullable=False)
    title = Column(String)
    duration = Column(Integer)
    resolution = Column(String)
    s3_url = Column(String)
    created_at = Column(DateTime, default=func.current_timestamp())