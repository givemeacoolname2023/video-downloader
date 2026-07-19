"""
Video Downloader API - FastAPI application.
"""
import os
import time
import uuid
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .downloader import (
    parse_video_info,
    download_video,
    get_task_status,
    get_download_filepath,
    DOWNLOAD_DIR,
)

app = FastAPI(
    title="Video Downloader API",
    description="万能视频下载器 - 基于 yt-dlp 的视频下载服务",
    version="1.0.0",
)

# CORS - allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    url: str


class ParseResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[dict] = None


class DownloadRequest(BaseModel):
    url: str
    format_id: Optional[str] = None


class DownloadResponse(BaseModel):
    success: bool
    message: str = ""
    task_id: Optional[str] = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float = 0.0
    speed: str = ""
    filename: str = ""
    error: str = ""


@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "ok",
        "service": "Video Downloader API",
        "version": "1.0.0",
        "powered_by": "yt-dlp",
    }


@app.post("/api/parse", response_model=ParseResponse)
async def parse_video(req: ParseRequest):
    """
    Parse video information from URL.
    Returns video title, thumbnail, available formats, etc.
    """
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="请提供视频链接")

    try:
        info = parse_video_info(req.url.strip())
        return ParseResponse(success=True, data=info)
    except ValueError as e:
        return ParseResponse(success=False, message=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败：{str(e)[:200]}")


@app.post("/api/download", response_model=DownloadResponse)
async def start_download(req: DownloadRequest):
    """
    Start a video download task.
    Returns a task_id for tracking progress.
    """
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="请提供视频链接")

    try:
        task_id = download_video(
            url=req.url.strip(),
            format_id=req.format_id,
        )
        return DownloadResponse(
            success=True,
            message="下载任务已创建",
            task_id=task_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动下载失败：{str(e)[:200]}")


@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task(task_id: str):
    """Get download task status."""
    status = get_task_status(task_id)
    if "error" in status and status["error"] == "Task not found":
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskStatusResponse(**status)


@app.get("/api/download-file/{task_id}")
async def download_file(task_id: str):
    """Download the completed video file."""
    filepath = get_download_filepath(task_id)
    if not filepath:
        raise HTTPException(status_code=404, detail="文件不存在或下载尚未完成")
    
    filename = os.path.basename(filepath)
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )


@app.websocket("/ws/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time download progress updates."""
    await websocket.accept()
    
    try:
        # Poll task status every second and send updates
        while True:
            status = get_task_status(task_id)
            
            if "error" in status and status["error"] == "Task not found":
                await websocket.send_json({"type": "error", "message": "Task not found"})
                break
            
            if status["status"] == "completed":
                await websocket.send_json({
                    "type": "complete",
                    "filename": status["filename"],
                    "filepath": status["filepath"],
                })
                break
            elif status["status"] == "error":
                await websocket.send_json({
                    "type": "error",
                    "message": status["error"] or "下载失败",
                })
                break
            elif status["status"] in ("downloading", "extracting"):
                await websocket.send_json({
                    "type": "progress",
                    "progress": status["progress"],
                    "speed": status["speed"],
                    "status": status["status"],
                })
            
            await asyncio.sleep(1)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)[:200]})
        except Exception:
            pass