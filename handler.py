from utils.youtube import download_video
from utils.s3 import upload_to_mock_s3
from utils.db import insert_metadata
from datetime import datetime
from fastapi import HTTPException
import re

def sanitize_video_id(video_id: str) -> str:
    """Sanitize and validate YouTube video ID."""
    # YouTube video IDs are 11 characters, alphanumeric with _ and -
    if not re.match(r'^[A-Za-z0-9_-]{11}$', video_id):
        raise HTTPException(status_code=400, detail="Invalid YouTube video ID")
    # Additional sanitization (though regex is sufficient)
    sanitized_id = re.sub(r'[^A-Za-z0-9_-]', '', video_id)
    if len(sanitized_id) != 11:
        raise HTTPException(status_code=400, detail="Invalid YouTube video ID length")
    return sanitized_id

async def download_video_handler(video_id: str):
    try:
        # Sanitize video ID
        sanitized_id = sanitize_video_id(video_id)
        
        # Construct YouTube URL
        youtube_url = f"https://www.youtube.com/watch?v={sanitized_id}"

        # Download video
        filename, metadata = download_video(youtube_url)

        # Upload to mock S3
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        s3_url = upload_to_mock_s3(filename, sanitized_id, timestamp)

        # Store metadata in PostgreSQL
        video_id = insert_metadata(metadata, s3_url)

        return {
            "status": "success",
            "video_id": video_id,
            "s3_url": s3_url,
            "metadata": metadata,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))