import os
import glob
import shutil
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from handler import download_video_handler
from utils.db import init_db

app = FastAPI(title="YouTube Video Downloader")

@app.on_event("startup")
async def startup():
    """Initialize database and clear /tmp/videos directory on server startup."""
    await init_db()  # Initialize database asynchronously
    tmp_videos_path = '/tmp/videos'
    try:
        if os.path.exists(tmp_videos_path):
            for item in glob.glob(os.path.join(tmp_videos_path, '*')):
                try:
                    if os.path.isfile(item):
                        await asyncio.to_thread(os.remove, item)
                    elif os.path.isdir(item):
                        await asyncio.to_thread(shutil.rmtree, item)
                except:
                    pass
            if not os.listdir(tmp_videos_path):
                await asyncio.to_thread(os.rmdir, tmp_videos_path)
    except:
        pass

ALLOWED_FORMATS = ['mp4', 'webm', 'mkv', 'mp3']
ALLOWED_QUALITIES = ['360p', '480p', '720p', '1080p', '4k']

class DownloadRequest(BaseModel):
    video_id: str
    format: str = Field(default='mp4', enum=ALLOWED_FORMATS)
    quality: str = Field(default='720p', enum=ALLOWED_QUALITIES)

@app.post("/download")
async def download_video_endpoint(request: DownloadRequest):
    # Explicitly validate format and quality
    if request.format not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "reason": f"Invalid format: {request.format}. Allowed formats: {', '.join(ALLOWED_FORMATS)}"
            }
        )
    if request.quality not in ALLOWED_QUALITIES:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "reason": f"Invalid quality: {request.quality}. Allowed qualities: {', '.join(ALLOWED_QUALITIES)}"
            }
        )
    return await download_video_handler(request.video_id, request.format, request.quality)