from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from utils.models import Video, Base

# Async setup for FastAPI startup
ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, pool_size=5, max_overflow=10)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

# Sync setup for Celery tasks
SYNC_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)

async def init_db():
    """Initialize the database by creating tables (async for FastAPI startup)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def insert_metadata(metadata: dict, s3_url: str, format: str) -> int:
    """Insert video metadata into the database synchronously."""
    with SessionLocal() as session:
        try:
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
                published_date=metadata["published_date"],
                format=format
            )
            session.add(video)
            session.commit()
            return video.id
        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to insert metadata: {str(e)}")