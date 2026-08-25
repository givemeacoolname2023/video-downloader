"""
In-memory transcript cache.

Subtitle extraction (via yt-dlp) is the slowest shared step for the AI
features (summary / mind-map / QA). This module caches the extracted transcript
per URL so the first feature pays the extraction cost and the rest reuse it
instantly. It is process-local and bounded; a restart clears it.
"""
import logging
from typing import Dict, Optional

from .subtitles import extract_subtitles, SubtitleError

logger = logging.getLogger(__name__)

# url -> {"title": str, "text": str}
_TRANSCRIPTS: Dict[str, dict] = {}
# Simple FIFO bound: drop the oldest entry once we exceed this many URLs.
_MAX_ENTRIES = 50


def cache_transcript(url: str, title: str, text: str) -> None:
    """Store a transcript under its URL, evicting the oldest entry if needed."""
    if not text.strip():
        return
    if url not in _TRANSCRIPTS and len(_TRANSCRIPTS) >= _MAX_ENTRIES:
        oldest = next(iter(_TRANSCRIPTS))
        _TRANSCRIPTS.pop(oldest, None)
    _TRANSCRIPTS[url] = {"title": title, "text": text}


def get_cached_transcript(url: str) -> Optional[dict]:
    """Return the cached transcript for *url*, or None if not cached yet."""
    hit = _TRANSCRIPTS.get(url)
    return {"title": hit["title"], "text": hit["text"]} if hit else None


def get_transcript(url: str) -> dict:
    """
    Return ``{"title", "text"}`` for *url*, extracting + caching on first use.

    Raises:
        SubtitleError: if no usable subtitle text can be extracted.
    """
    cached = get_cached_transcript(url)
    if cached:
        return cached

    sub = extract_subtitles(url)
    if not sub.get("text", "").strip():
        raise SubtitleError("该视频暂无可用的中文字幕，无法生成总结。")

    cache_transcript(url, sub.get("title", "未知标题"), sub["text"])
    return {"title": sub.get("title", "未知标题"), "text": sub["text"]}
