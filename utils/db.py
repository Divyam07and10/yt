from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from sqlalchemy.sql import select
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from utils.models import Video, Base

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database by creating tables."""
    Base.metadata.create_all(bind=engine)

def check_video_exists(url: str) -> bool:
    """Check if a video URL exists in the videos table."""
    try:
        with SessionLocal() as session:
            stmt = exists().where(Video.url == url)
            return session.execute(select(stmt)).scalar()
    except Exception as e:
        raise Exception(f"Failed to check video existence: {str(e)}")

def insert_metadata(metadata: dict, s3_url: str):
    """Insert video metadata into the database."""
    try:
        with SessionLocal() as session:
            video = Video(
                url=metadata["url"],
                youtube_id=metadata["youtube_id"],
                title=metadata["title"],
                duration=metadata["duration"],
                views=metadata["views"],
                likes=metadata["likes"],
                channel=metadata["channel"],
                thumbnail_url=metadata["thumbnail_url"],
                resolution=metadata["resolution"],
                s3_url=s3_url,
                published_date=metadata["published_date"]
            )
            session.add(video)
            session.commit()
            return video.id
    except Exception as e:
        raise Exception(f"Failed to insert metadata: {str(e)}")