import re
import os
import glob
import asyncio
from fastapi import HTTPException
from datetime import datetime
from utils.youtube import download_video
from utils.s3 import upload_to_mock_s3
from utils.db import insert_metadata, check_video_exists

def sanitize_video_id(video_id: str) -> str:
    """Sanitize and validate YouTube video ID."""
    if not re.match(r'^[A-Za-z0-9_-]{11}$', video_id):
        raise HTTPException(status_code=400, detail="Invalid YouTube video ID")
    sanitized_id = re.sub(r'[^A-Za-z0-9_-]', '', video_id)
    if len(sanitized_id) != 11:
        raise HTTPException(status_code=400, detail="Invalid YouTube video ID length")
    return sanitized_id

async def get_tmp_size() -> int:
    """Calculate total size of files in /tmp asynchronously."""
    total_size = 0
    tmp_path = '/tmp'
    try:
        for item in glob.glob(os.path.join(tmp_path, '**/*'), recursive=True):
            if os.path.isfile(item):
                total_size += await asyncio.to_thread(os.path.getsize, item)
    except:
        raise HTTPException(status_code=500, detail="Failed to calculate /tmp size")
    return total_size

async def check_storage_limit():
    """Check if /tmp storage exceeds 512MB limit."""
    max_tmp_storage = 512 * 1024 * 1024
    current_size = await get_tmp_size()
    
    if current_size >= max_tmp_storage:
        raise HTTPException(
            status_code=400,
            detail=f"/tmp storage full (512 MB limit reached). Current usage: {current_size / 1024 / 1024:.2f} MB"
        )
    return True

async def download_video_handler(video_id: str, format: str, quality: str):
    """Handle video download, upload to S3, and store metadata."""
    await check_storage_limit()
    
    try:
        sanitized_id = sanitize_video_id(video_id)
        youtube_url = f"https://www.youtube.com/watch?v={sanitized_id}"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"/tmp/videos/{sanitized_id}_{timestamp}.{format}"
        
        # Check if video exists in database
        if await asyncio.to_thread(check_video_exists, youtube_url):
            print(f"[download] {filename} has already been downloaded")
            raise HTTPException(status_code=400, detail=f"Download failed: {filename} has already been downloaded")
        
        filename, metadata = await asyncio.to_thread(download_video, youtube_url, format=format, quality=quality)
        
        if not os.path.exists(filename):
            raise HTTPException(status_code=400, detail=f"Downloaded file not found: {filename}")
        
        s3_url, presigned_url = await asyncio.to_thread(upload_to_mock_s3, filename, sanitized_id, timestamp, format)
        
        video_id = await asyncio.to_thread(insert_metadata, metadata, s3_url)
        
        if os.path.exists(filename):
            await asyncio.to_thread(os.remove, filename)
        
        print(f"Download link: {presigned_url}")
        
        return {
            "status": "success",
            "video_id": video_id,
            "s3_url": s3_url,
            "download_link": presigned_url
        }
    except HTTPException as e:
        if "has already been downloaded" in str(e.detail):
            print(f"[download] {e.detail.split(': ')[1]}")
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")