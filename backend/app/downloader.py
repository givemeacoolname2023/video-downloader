"""
Video download service using yt-dlp.
Provides video parsing, downloading and progress tracking capabilities.
"""
import os
import json
import asyncio
import logging
import uuid
import threading
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import yt_dlp

logger = logging.getLogger(__name__)

# Configuration
DOWNLOAD_DIR = Path(__file__).parent.parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)


@dataclass
class DownloadTask:
    """Represents a download task with progress tracking."""
    task_id: str
    url: str
    status: str = "pending"  # pending, extracting, downloading, completed, error
    progress: float = 0.0
    speed: str = ""
    filename: str = ""
    filepath: str = ""
    error: str = ""
    info: Dict[str, Any] = field(default_factory=dict)


# In-memory task store (for lightweight implementation without DB)
_tasks: Dict[str, DownloadTask] = {}


def _progress_hook(task_id: str):
    """Create a progress hook for yt-dlp that updates task status."""
    def hook(d):
        task = _tasks.get(task_id)
        if not task:
            return
        
        status = d.get("status", "")
        
        if status == "downloading":
            task.status = "downloading"
            # Calculate progress
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total and total > 0:
                task.progress = min((downloaded / total) * 100, 99.9)
            elif d.get("_percent_str"):
                try:
                    task.progress = float(d["_percent_str"].replace("%", "").strip())
                except (ValueError, AttributeError):
                    pass
            
            # Speed
            speed = d.get("_speed_str", "")
            if speed:
                task.speed = speed.strip()
            
            # Filename estimate
            filename = d.get("filename", "")
            if filename:
                task.filename = os.path.basename(filename)
        
        elif status == "finished":
            task.status = "completed"
            task.progress = 100.0
            # Get final filename
            filename = d.get("filename", "")
            if filename:
                task.filename = os.path.basename(filename)
                task.filepath = filename
    
    return hook


# Common HTTP headers to avoid 412 / anti-bot detection
_COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
}

# Browsers to try for automatic cookie extraction (in priority order)
_COOKIE_BROWSERS: tuple = ("edge",)


def _is_cookie_error(error_msg: str) -> bool:
    """Check if an error is related to browser cookie extraction."""
    msg_lower = error_msg.lower()
    return "cookie" in msg_lower or "browser" in msg_lower


def _build_ydl_opts(extract_only: bool = False, use_cookies: bool = False) -> Dict[str, Any]:
    """
    Build base yt-dlp options.

    Args:
        extract_only: If True, skip downloading (parse info only).
        use_cookies: If True, attempt to extract cookies from local browsers for HD access.
                     Cookie errors should be caught and retried without this flag.
    """
    opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        # Anti-anti-bot: spoof HTTP headers
        "http_headers": _COMMON_HEADERS,
        # Geo bypass for region-restricted content
        "geo_bypass": True,
        "geo_bypass_country": "CN",
        # Retry
        "retries": 5,
        "fragment_retries": 5,
        # Socket timeout
        "socket_timeout": 30,
    }

    if extract_only:
        opts["skip_download"] = True

    if use_cookies:
        opts["cookiesfrombrowser"] = _COOKIE_BROWSERS

    return opts


def _parse_extracted_info(info: Dict[str, Any], url: str) -> Dict[str, Any]:
    """Process raw yt-dlp info dict into a cleaned result."""
    duration_seconds = int(info.get("duration", 0) or 0)
    hours = duration_seconds // 3600
    minutes = (duration_seconds % 3600) // 60
    seconds = duration_seconds % 60
    if hours > 0:
        duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        duration_str = f"{minutes}:{seconds:02d}"

    # Process formats - only keep relevant ones
    raw_formats = info.get("formats", [])
    processed_formats = []
    seen_resolutions = set()

    for f in raw_formats:
        height = f.get("height") or 0
        if not height or height < 360:
            continue

        resolution = f"{height}p"
        format_id = f.get("format_id", "")
        ext = f.get("ext", "mp4")
        filesize = f.get("filesize") or f.get("filesize_approx") or 0

        if resolution not in seen_resolutions:
            seen_resolutions.add(resolution)
            processed_formats.append({
                "format_id": format_id,
                "resolution": resolution,
                "ext": ext,
                "filesize": filesize if filesize > 0 else None,
                "filesize_approx": f.get("filesize_approx") if not filesize else None,
                "format_note": f.get("format_note", ""),
                "vcodec": f.get("vcodec", "unknown")[:20],
                "acodec": f.get("acodec", "unknown")[:20],
            })

    processed_formats = processed_formats[:8]

    return {
        "title": info.get("title", "Unknown Title"),
        "thumbnail": info.get("thumbnail", ""),
        "duration": duration_str,
        "uploader": info.get("uploader", ""),
        "view_count": info.get("view_count", 0),
        "description": (info.get("description", "") or "")[:500],
        "webpage_url": info.get("webpage_url", url),
        "extractor": info.get("extractor", ""),
        "formats": processed_formats,
    }


def _handle_download_error(error_msg: str) -> None:
    """Map yt-dlp error messages to user-friendly Chinese messages."""
    if "Unsupported URL" in error_msg:
        raise ValueError("不支持的视频链接，请检查链接格式。")
    elif "Video unavailable" in error_msg:
        raise ValueError("视频不可用，可能已被删除或设为私密。")
    elif "Private video" in error_msg:
        raise ValueError("这是私密视频，无法访问。")
    elif "This video is not available" in error_msg:
        raise ValueError("该视频在您的地区不可用。")
    elif "Login" in error_msg or "sign in" in error_msg:
        raise ValueError("该平台需要登录才能访问此视频。")
    else:
        raise ValueError(f"解析视频失败：{error_msg[:200]}")


def parse_video_info(url: str) -> Dict[str, Any]:
    """
    Parse video information without downloading.
    
    Tries with browser cookies first for HD quality access; falls back to
    cookieless mode on cookie-related errors (e.g. browser database locked).
    
    Returns:
        dict with keys: title, thumbnail, duration, uploader, view_count, 
                       formats (list of available formats), etc.
    """
    extractor_args = {
        "bilibili": {
            "player_client": ["web", "android", "ios"],
            "prefer_multi_flv": True,
        },
    }

    def _do_parse(use_cookies: bool) -> Dict[str, Any]:
        ydl_opts = _build_ydl_opts(extract_only=True, use_cookies=use_cookies)
        ydl_opts["extract_flat"] = False
        ydl_opts["extractor_args"] = extractor_args
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    try:
        try:
            info = _do_parse(use_cookies=True)
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if _is_cookie_error(error_msg):
                logger.warning("Cookie extraction failed, retrying without cookies: %s", error_msg[:100])
                info = _do_parse(use_cookies=False)
            else:
                raise

        return _parse_extracted_info(info, url)

    except yt_dlp.utils.DownloadError as e:
        _handle_download_error(str(e))


def download_video(url: str, format_id: Optional[str] = None, task_id: Optional[str] = None) -> str:
    """
    Download a video using yt-dlp.
    
    Tries with browser cookies first; falls back to cookieless mode on cookie errors.
    
    Args:
        url: The video URL to download
        format_id: Specific format ID to download, or None for best quality
        task_id: Task ID for progress tracking. Auto-generated if not provided.
    
    Returns:
        task_id: The task ID for tracking download progress
    """
    if task_id is None:
        task_id = str(uuid.uuid4())[:8]
    
    # Create task
    task = DownloadTask(task_id=task_id, url=url, status="extracting")
    _tasks[task_id] = task
    
    # Output template
    output_template = str(DOWNLOAD_DIR / f"%(title)s_{task_id}.%(ext)s")
    
    # Shared options that don't change between attempts
    shared_opts: Dict[str, Any] = {
        "outtmpl": output_template,
        "progress_hooks": [_progress_hook(task_id)],
        "format": format_id + "+bestaudio/best" if format_id else "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            },
            "bilibili": {
                "player_client": ["web", "android", "ios"],
                "prefer_multi_flv": True,
            },
        },
    }

    def _download_attempt(use_cookies: bool):
        task.status = "downloading"
        ydl_opts = _build_ydl_opts(extract_only=False, use_cookies=use_cookies)
        ydl_opts.update(shared_opts)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def _download():
        try:
            try:
                _download_attempt(use_cookies=True)
            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                if _is_cookie_error(error_msg):
                    logger.warning("Cookie extraction failed during download, retrying without cookies: %s", error_msg[:100])
                    _download_attempt(use_cookies=False)
                else:
                    raise

            # Check if completed successfully
            if task.status != "completed":
                task.status = "completed"
                task.progress = 100.0

        except Exception as e:
            task.status = "error"
            task.error = str(e)[:500]
            raise
    
    # Start download thread
    thread = threading.Thread(target=_download, daemon=True)
    thread.start()
    
    return task_id


def get_task(task_id: str) -> Optional[DownloadTask]:
    """Get download task by ID."""
    return _tasks.get(task_id)


def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get download task status."""
    task = _tasks.get(task_id)
    if not task:
        return {"error": "Task not found"}
    
    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "speed": task.speed,
        "filename": task.filename,
        "filepath": task.filepath,
        "error": task.error,
    }


def get_download_filepath(task_id: str) -> Optional[str]:
    """Get the downloaded file path for a completed task."""
    task = _tasks.get(task_id)
    if not task or task.status != "completed":
        return None

    # First try the recorded filepath
    if task.filepath and os.path.exists(task.filepath):
        return task.filepath

    # Otherwise search the downloads directory for files matching the task ID
    for f in DOWNLOAD_DIR.glob(f"*{task_id}*"):
        if f.is_file():
            return str(f)

    return None