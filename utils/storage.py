import os
import glob
from fastapi import HTTPException
from config.settings import MAX_VIDEO_SIZE

def get_tmp_size() -> int:
    """Calculate total size of files in /tmp synchronously."""
    total_size = 0
    tmp_path = '/tmp'
    try:
        for item in glob.glob(os.path.join(tmp_path, '**/*'), recursive=True):
            if os.path.isfile(item):
                total_size += os.path.getsize(item)
    except:
        raise HTTPException(status_code=500, detail="Failed to calculate /tmp size")
    return total_size

def check_storage_limit():
    """Check if /tmp storage exceeds 512MB limit."""
    max_tmp_storage = 512 * 1024 * 1024
    current_size = get_tmp_size()
    
    if current_size >= max_tmp_storage:
        raise HTTPException(
            status_code=503,
            detail=f"/tmp storage full (512 MB limit reached). Current usage: {current_size / 1024 / 1024:.2f} MB"
        )
    return True

def check_file_size(filename: str):
    """Check if file size exceeds 100MB limit."""
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        if file_size > MAX_VIDEO_SIZE:
            raise HTTPException(status_code=400, detail=f"Video file size ({file_size / 1024 / 1024:.2f} MB) exceeds 100 MB limit")
    return True