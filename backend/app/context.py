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

# url -> {"title": str, "text": str, "lang": str, "lines": list}
# ``lines`` holds the timed subtitle segments (``[{"start": sec, "text": str}]``)
# extracted by ``extract_subtitles``, kept here so the subtitle viewer can show
# timestamps without a second platform request.
_TRANSCRIPTS: Dict[str, dict] = {}
# Simple FIFO bound: drop the oldest entry once we exceed this many URLs.
_MAX_ENTRIES = 50


def cache_transcript(
    url: str, title: str, text: str, lang: str = "", lines: Optional[list] = None
) -> None:
    """Store a transcript under its URL, evicting the oldest entry if needed."""
    if not text.strip():
        return
    if url not in _TRANSCRIPTS and len(_TRANSCRIPTS) >= _MAX_ENTRIES:
        oldest = next(iter(_TRANSCRIPTS))
        _TRANSCRIPTS.pop(oldest, None)
    _TRANSCRIPTS[url] = {
        "title": title,
        "text": text,
        "lang": lang,
        "lines": lines or [],
    }


def get_cached_transcript(url: str) -> Optional[dict]:
    """Return the cached transcript for *url*, or None if not cached yet."""
    hit = _TRANSCRIPTS.get(url)
    if not hit:
        return None
    return {
        "title": hit["title"],
        "text": hit["text"],
        "lang": hit.get("lang", ""),
        "lines": hit.get("lines", []),
    }


def get_transcript(url: str) -> dict:
    """
    Return ``{"title", "text", "lang", "lines"}`` for *url*, extracting +
    caching on first use. The summary / mind-map / QA features read only
    ``title`` & ``text``; the subtitle viewer also uses ``lines``.

    Raises:
        SubtitleError: if no usable subtitle text can be extracted.
    """
    cached = get_cached_transcript(url)
    if cached:
        return cached

    sub = extract_subtitles(url)
    if not sub.get("text", "").strip():
        raise SubtitleError("该视频暂无可用的中文字幕，无法生成总结。")

    cache_transcript(
        url,
        sub.get("title", "未知标题"),
        sub["text"],
        sub.get("lang", ""),
        sub.get("lines", []),
    )
    return {
        "title": sub.get("title", "未知标题"),
        "text": sub["text"],
        "lang": sub.get("lang", ""),
        "lines": sub.get("lines", []),
    }
