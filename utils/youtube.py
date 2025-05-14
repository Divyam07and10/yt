import yt_dlp
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from fastapi import HTTPException

def check_ffmpeg(ffmpeg_path: str) -> bool:
    """Check if ffmpeg is available at the specified path."""
    return os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK)

def check_storage_and_size(filename: str = None, estimated_size: int = 0):
    """Check if file size or estimated size exceeds Lambda limits."""
    max_file_size = 100 * 1024 * 1024
    
    if estimated_size > max_file_size:
        raise HTTPException(status_code=400, detail=f"Estimated video size ({estimated_size / 1024 / 1024:.2f} MB) exceeds 100 MB limit")
    
    if filename and os.path.exists(filename):
        file_size = os.path.getsize(filename)
        
        if file_size > max_file_size:
            os.remove(filename)
            raise HTTPException(status_code=400, detail=f"Video file size ({file_size / 1024 / 1024:.2f} MB) exceeds 100 MB limit")
    return True

def get_estimated_size(youtube_url: str, format: str, quality: str, ffmpeg_available: bool) -> int:
    """Estimate video file size using yt-dlp."""
    try:
        format_str = f"best[ext={format}]" if not ffmpeg_available else (
            f"bestvideo[height<={quality[:-1]}][ext={format}]+bestaudio/best[ext={format}]/best" if format != "mp3" else "bestaudio/best"
        )
        ydl_opts = {
            "format": format_str,
            "simulate": True,
            "socket_timeout": 30,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            video_size = info.get("filesize_approx", 0) or info.get("filesize", 0)
            return video_size if video_size else 0
    except:
        return 0

def download_video(youtube_url: str, output_path: str = "/tmp/videos", format: str = "mp4", quality: str = "720p"):
    """Download video using yt-dlp."""
    filename = None
    ffmpeg_path = "/opt/bin/ffmpeg"
    ffmpeg_available = check_ffmpeg(ffmpeg_path)
    
    if format == "mp3" and not ffmpeg_available:
        raise HTTPException(status_code=400, detail="MP3 format requires ffmpeg, which is not available")
    
    try:
        estimated_size = get_estimated_size(youtube_url, format, quality, ffmpeg_available)
        check_storage_and_size(estimated_size=estimated_size)

        os.makedirs(output_path, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        youtube_id = extract_youtube_id(youtube_url)
        filename = f"{output_path}/{youtube_id}_{timestamp}.{format}"
        
        if os.path.exists(filename):
            raise HTTPException(status_code=400, detail=f"/tmp/{youtube_id}_{timestamp}.{format} has already been downloaded")
        
        format_str = f"best[ext={format}]" if not ffmpeg_available else (
            f"bestvideo[height<={quality[:-1]}][ext={format}]+bestaudio/best[ext={format}]/best" if format != "mp3" else "bestaudio/best"
        )
        
        ydl_opts = {
            "outtmpl": f"{output_path}/%(id)s_{timestamp}.%(ext)s",
            "format": format_str,
            "merge_output_format": format,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 30,
        }
        
        if ffmpeg_available:
            ydl_opts["ffmpeg_location"] = ffmpeg_path
            ydl_opts["outtmpl"] = f"{output_path}/%(id)s_{timestamp}.{format}"
            if format == "mp3":
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
        
        if not os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            ydl_opts["verbose"] = True
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            youtube_id = info.get("id")
            filename = f"{output_path}/{youtube_id}_{timestamp}.{format}"
            if not os.path.exists(filename):
                raise HTTPException(status_code=400, detail=f"Output file not created: {filename}")
            metadata = {
                "url": youtube_url,
                "youtube_id": youtube_id,
                "title": info.get("title"),
                "duration": str(info.get("duration", 0)),
                "views": info.get("view_count"),
                "likes": info.get("like_count"),
                "channel": info.get("uploader"),
                "thumbnail_url": info.get("thumbnail"),
                "resolution": "audio" if format == "mp3" else (info.get("resolution") or f"{info.get('width')}x{info.get('height')}"),
                "published_date": info.get("upload_date")
            }
            check_storage_and_size(filename)
            return filename, metadata
    except Exception as e:
        if filename and os.path.exists(filename):
            os.remove(filename)
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e).replace('\u001b[0;31mERROR:\u001b[0m ', '')}")
    
def extract_youtube_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc in ("www.youtube.com", "youtube.com"):
        if parsed.path.startswith("/watch"):
            query = parse_qs(parsed.query)
            return query.get("v", [None])[0]
        elif parsed.path.startswith("/shorts/"):
            return parsed.path.lstrip("/shorts/")
    elif parsed.netloc == "youtu.be":
        return parsed.path.lstrip("/")
    return None