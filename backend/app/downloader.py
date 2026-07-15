"""
Video download service using yt-dlp.
Provides video parsing, downloading and progress tracking capabilities.
"""
import os
import json
import asyncio
import uuid
import threading
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import yt_dlp

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


def parse_video_info(url: str) -> Dict[str, Any]:
    """
    Parse video information without downloading.
    
    Returns:
        dict with keys: title, thumbnail, duration, uploader, view_count, 
                       formats (list of available formats), etc.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        "no_color": True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract relevant info
            duration_seconds = info.get("duration", 0) or 0
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
            
            # Sort formats: prefer video+audio merged, higher quality first
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
            
            # Limit to top 8 formats
            processed_formats = processed_formats[:8]
            
            result = {
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
            
            return result
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
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


def download_video(url: str, format_id: Optional[str] = None, task_id: Optional[str] = None) -> str:
    """
    Download a video using yt-dlp.
    
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
    
    # Build yt-dlp options
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "outtmpl": output_template,
        "progress_hooks": [_progress_hook(task_id)],
        # Prefer formats that don't need merging (mp4 with audio)
        "format": format_id if format_id else "best[ext=mp4]/best",
        # Merge to mp4
        "merge_output_format": "mp4",
        # Retry
        "retries": 3,
        "fragment_retries": 3,
        # Throttling workarounds
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }
    
    # Run download in a separate thread
    def _download():
        try:
            task.status = "downloading"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
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