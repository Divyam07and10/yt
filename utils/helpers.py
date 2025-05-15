def build_format_selector(format: str, target_height: int) -> str:
    """Build yt-dlp format selector based on format and quality."""
    if format == "mp4":
        return f"bestvideo[height<={target_height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={target_height}][ext=mp4]"
    elif format == "webm":
        return f"bestvideo[height<={target_height}][ext=webm]+bestaudio[ext=webm]/best[height<={target_height}][ext=webm]"
    elif format == "mkv":
        return f"bestvideo[height<={target_height}]+bestaudio/best[height<={target_height}]"
    elif format == "mp3":
        return "bestaudio[ext=m4a]/bestaudio"
    else:
        return "best"