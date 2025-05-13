import yt_dlp
import os
from urllib.parse import urlparse, parse_qs

def download_video(youtube_url: str, output_path: str = "/tmp"):
    try:
        ydl_opts = {
            "outtmpl": f"{output_path}/%(id)s_%(timestamp)s.%(ext)s",
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "quiet": False,  # Enable verbose output for debugging
            "noplaylist": True,  # Avoid downloading playlists
            "ffmpeg_location": "/usr/bin/ffmpeg",  # Adjust if ffmpeg is elsewhere
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            filename = ydl.prepare_filename(info)
            youtube_id = info.get("id")
            metadata = {
                "youtube_id": youtube_id,
                "title": info.get("title"),
                "duration": int(info.get("duration", 0)),
                "resolution": info.get("resolution") or f"{info.get('width')}x{info.get('height')}",
            }
            return filename, metadata
    except Exception as e:
        print(f"yt_dlp error: {str(e)}")  # Log detailed error
        raise Exception(f"Failed to download video: {str(e)}")

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