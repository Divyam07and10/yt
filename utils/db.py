from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from utils.models import Video, Base

# Create database engine
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database by creating tables."""
    Base.metadata.create_all(bind=engine)

def insert_metadata(metadata: dict, s3_url: str):
    try:
        with SessionLocal() as session:
            video = Video(
                youtube_id=metadata["youtube_id"],
                title=metadata["title"],
                duration=metadata["duration"],
                resolution=metadata["resolution"],
                s3_url=s3_url
            )
            session.add(video)
            session.commit()
            return str(video.id)
    except Exception as e:
        raise Exception(f"Failed to insert metadata: {str(e)}")