import os
def check_ffmpeg(ffmpeg_path: str) -> bool:
    """Check if ffmpeg is available at the specified path."""
    print(f"[debug] Checking ffmpeg at: {ffmpeg_path}")
    return os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK)