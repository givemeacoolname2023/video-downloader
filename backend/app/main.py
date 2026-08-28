"""
Video Downloader API - FastAPI application.
"""
import os
import time
import uuid
import asyncio
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

from .downloader import (
    parse_video_info,
    download_video,
    get_task_status,
    get_download_filepath,
    DOWNLOAD_DIR,
)
from .subtitles import SubtitleError
from .context import get_transcript
from .summary import summary_stream, SummaryError
from .mindmap import generate_mindmap
from .qa import qa_stream
from .llm import LLMError

# Load environment variables from the project-root .env (parent of backend/).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

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


class SummaryRequest(BaseModel):
    url: str


class SummaryResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[dict] = None


class MindmapRequest(BaseModel):
    url: str


class MindmapResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[dict] = None


class SubtitleRequest(BaseModel):
    url: str


class QaRequest(BaseModel):
    url: str
    question: str
    history: list = []


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


@app.post("/api/summary")
async def create_summary(req: SummaryRequest):
    """
    Stream an AI summary of a video as SSE, token-by-token.

    Returns ``text/event-stream`` with ``data: {"text": "..."}`` chunks,
    ``data: {"done": true}`` at the end, and ``data: {"error": "..."}`` on
    failure (e.g. no usable subtitles).
    """
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="请提供视频链接")

    return StreamingResponse(
        summary_stream(req.url.strip()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/mindmap", response_model=MindmapResponse)
def create_mindmap(req: MindmapRequest):
    """
    Generate an interactive mind-map outline (hierarchical Markdown) for a
    video, reusing the same cached transcript as the summary/QA features.

    Plain ``def`` so the blocking extraction + LLM call runs in the thread pool.
    """
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="请提供视频链接")

    try:
        transcript = get_transcript(req.url.strip())
        result = generate_mindmap(transcript["text"], transcript["title"])
        return MindmapResponse(success=True, data=result)
    except (SubtitleError, LLMError, ValueError) as e:
        return MindmapResponse(success=False, message=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成思维导图失败：{str(e)[:200]}")


@app.post("/api/subtitles")
def get_video_subtitles(req: SubtitleRequest):
    """
    Return a video's subtitle segments with timestamps.

    Reuses the same cached transcript as summary / mind-map / QA, so no second
    platform request is made once those features have run. Returns
    ``{"success", "data": {"title", "lang", "segments": [{"start", "text"}]}}``.
    Plain ``def`` so the blocking extraction runs in the thread pool.
    """
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="请提供视频链接")

    try:
        transcript = get_transcript(req.url.strip())
        return {
            "success": True,
            "data": {
                "title": transcript["title"],
                "lang": transcript.get("lang", ""),
                "segments": transcript.get("lines", []),
            },
        }
    except (SubtitleError, ValueError) as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取字幕失败：{str(e)[:200]}")


@app.post("/api/qa")
async def create_qa(req: QaRequest):
    """
    Stream an answer to a question about a video using SSE.

    Returns ``text/event-stream`` with ``data: {"text": "..."}`` chunks,
    ``data: {"done": true}`` at the end, and ``data: {"error": "..."}`` on
    failure. Async (not a threadpool ``def``) because we stream LLM tokens.
    """
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="请提供视频链接")
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="请输入问题")

    return StreamingResponse(
        qa_stream(req.url.strip(), req.question.strip(), req.history or []),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Referer mapping for image proxy — maps domain patterns to the correct Referer header
_REFERER_MAP = {
    "hdslb.com": "https://www.bilibili.com/",
    "bilibili.com": "https://www.bilibili.com/",
    "bilivideo.com": "https://www.bilibili.com/",
    "douyin.com": "https://www.douyin.com/",
    "douyinpic.com": "https://www.douyin.com/",
    "ixigua.com": "https://www.ixigua.com/",
    "ixiguavideo.com": "https://www.ixigua.com/",
    "xhscdn.com": "https://www.xiaohongshu.com/",
    "xhslink.com": "https://www.xiaohongshu.com/",
}


def _infer_referer(image_url: str) -> Optional[str]:
    """Guess the Referer header value from the image URL's domain."""
    try:
        host = urlparse(image_url).hostname or ""
        for key, referer in _REFERER_MAP.items():
            if key in host:
                return referer
    except Exception:
        pass
    return None


@app.get("/api/proxy-image")
async def proxy_image(url: str):
    """
    Proxy image requests to bypass Referer-based hotlink protection.
    Sets a platform-appropriate Referer header based on the image URL domain.
    """
    if not url:
        raise HTTPException(status_code=400, detail="Missing image URL")

    target_url = unquote(url)

    # Validate scheme
    parsed = urlparse(target_url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid image URL scheme")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
    }
    referer = _infer_referer(target_url)
    if referer:
        headers["Referer"] = referer

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(target_url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Image fetch failed")
            content_type = resp.headers.get("content-type", "image/jpeg")
            return Response(content=resp.content, media_type=content_type)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Proxy request failed: {str(e)[:200]}")


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