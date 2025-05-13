from fastapi import FastAPI
from pydantic import BaseModel
from handler import download_video_handler
from utils.db import init_db

app = FastAPI(title="YouTube Video Downloader")

# Initialize database
init_db()

class DownloadRequest(BaseModel):
    video_id: str

@app.post("/download")
async def download_video_endpoint(request: DownloadRequest):
    return await download_video_handler(request.video_id)