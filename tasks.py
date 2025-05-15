import yt_dlp
import os
import shutil
from datetime import datetime
from fastapi import HTTPException
from celery import shared_task
from utils.helpers import build_format_selector
from utils.s3 import upload_to_mock_s3
from utils.db import insert_metadata
from utils.storage import check_file_size
from utils.youtube import check_ffmpeg

@shared_task(bind=True, max_retries=3)
def download_video_task(self, youtube_url: str, format: str = "mp4", quality: str = "720p"):
    """Celery task to download video, upload to S3, and store metadata."""
    try:
        filename = None
        ffmpeg_path = shutil.which("ffmpeg") or "/opt/bin/ffmpeg"
        ffmpeg_available = check_ffmpeg(ffmpeg_path)

        # Prepare output path
        output_path = "/tmp/videos"
        os.makedirs(output_path, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        youtube_id = youtube_url.split('v=')[-1]
        filename = f"{output_path}/{youtube_id}_{timestamp}.{format}"

        if os.path.exists(filename):
            raise HTTPException(status_code=400, detail=f"File {filename} has already been downloaded")

        # Build yt-dlp format selector
        target_height = 2160 if quality.lower() == "4k" else int(quality.lower().replace("p", ""))
        format_str = build_format_selector(format, target_height)

        # Configure yt-dlp options
        ydl_opts = {
            "outtmpl": filename.replace(f".{format}", ".%(ext)s"),
            "format": format_str,
            "merge_output_format": format,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 30,
            "no_clean": True,
            "keepvideo": False,
            "quiet": True,
        }

        if ffmpeg_available:
            ydl_opts["ffmpeg_location"] = ffmpeg_path
            if format == "mp3":
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
                ydl_opts["outtmpl"] = filename.replace(".mp3", ".%(ext)s")

        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            final_file = ydl.prepare_filename(info).replace(".webm", f".{format}").replace(".m4a", f".{format}")

            if not os.path.exists(final_file):
                raise HTTPException(status_code=400, detail=f"Output file not created: {final_file}")

            print(f"[debug] Final file exists: {os.path.exists(final_file)}")

            # Check file size
            check_file_size(final_file)

            # Upload to S3
            s3_url, presigned_url = upload_to_mock_s3(final_file, youtube_id, timestamp, format)

            # Format metadata
            upload_date = info.get("upload_date")
            if upload_date:
                formatted_date = f"{upload_date[:4]}/{upload_date[4:6]}/{upload_date[6:]}"
            else:
                formatted_date = datetime.now().strftime("%Y/%m/%d")
            metadata = {
                "url": youtube_url,
                "youtube_id": youtube_id,
                "title": info.get("title", "Unknown title"),
                "duration": str(info.get("duration", 0)),
                "views": info.get("view_count", 0),
                "likes": info.get("like_count", 0),
                "channel": info.get("uploader", "Unknown channel"),
                "thumbnail_url": info.get("thumbnail", ""),
                "resolution": "audio" if format == "mp3" else (info.get("resolution") or f"{info.get('width', 0)}x{info.get('height', 0)}"),
                "published_date": formatted_date
            }

            # Insert metadata into database
            video_id = insert_metadata(metadata, s3_url, format)

            return {
                "status": "success",
                "video_id": video_id,
                "s3_url": s3_url,
                "download_url": presigned_url
            }
    except HTTPException as e:
        print(f"[debug] HTTPException: {str(e)}")
        return {
            "status": "failed",
            "reason": str(e.detail),
            "status_code": e.status_code
        }
    except Exception as e:
        print(f"[debug] General Exception: {str(e)}")
        return {
            "status": "failed",
            "reason": f"Download failed: {str(e)}",
            "status_code": 400
        }