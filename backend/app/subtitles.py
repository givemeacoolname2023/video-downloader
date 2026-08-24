"""
Subtitle extraction service using yt-dlp.

Extracts subtitles from platform APIs (focused on Bilibili) so they can be
passed to the AI summarizer. Reuses the cookie / header handling from
downloader.py to obtain login-protected subtitles (e.g. Bilibili ``ai-zh`` AI
subtitles which require the user to be logged in).

The extraction runs in two passes:
  1. A metadata-only pass (``extract_info(download=False)``) to discover which
     subtitle languages are available and pick the best Chinese one.
  2. A write pass (``skip_download=True`` + ``writesubtitles``) that writes
     only the chosen language to a temp dir, then reads + parses it back.

Cookie-related errors are retried without cookies, matching the existing
parse/download flow in ``downloader.py``.
"""
import re
import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import yt_dlp

from .downloader import _build_ydl_opts, _is_cookie_error

logger = logging.getLogger(__name__)


class SubtitleError(Exception):
    """Raised when subtitles cannot be extracted."""


# Preferred subtitle languages, in priority order.
# Bilibili uses 'ai-zh' for AI-generated Chinese subs (requires login);
# manual subs use 'zh-Hans' / 'zh-CN' / 'zh-Hant'.
_SUBTITLE_LANGS = ["zh-Hans", "zh-CN", "ai-zh", "zh", "zh-Hant", "zh-Hans-CN"]


def _build_subtitle_opts(use_cookies: bool, out_dir: str) -> Dict[str, Any]:
    """Build yt-dlp options that write only subtitles (no video)."""
    opts = _build_ydl_opts(extract_only=False, use_cookies=use_cookies)
    opts.update(
        {
            "skip_download": True,  # only write subtitles, never the video
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": list(_SUBTITLE_LANGS),
            "subtitlesformat": "json3/srv3/best",
            "outtmpl": str(Path(out_dir) / "%(title)s.%(ext)s"),
        }
    )
    return opts


def _choose_language(info: Dict[str, Any]) -> str:
    """Pick the best available Chinese subtitle language code."""
    available = set(info.get("subtitles", {})) | set(info.get("automatic_captions", {}))
    for lang in _SUBTITLE_LANGS:
        if lang in available:
            return lang
    zh_langs = [lang for lang in available if lang.startswith("zh")]
    if zh_langs:
        return zh_langs[0]
    return next(iter(available), "")


def _read_subtitle_file(path: Path) -> List[Dict[str, Any]]:
    """Parse one subtitle file into a list of ``{start, text}`` segments."""
    ext = path.suffix.lower()
    try:
        if ext == ".json3":
            return _parse_json3(path)
        if ext in (".json", ".srv3"):
            return _parse_srv3(path)
        if ext == ".vtt":
            return _parse_timed_text(path)
        if ext == ".srt":
            return _parse_timed_text(path)
        # Unknown extension: treat each non-empty line as a segment.
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            return []
        return [{"start": None, "text": line} for line in text.splitlines() if line.strip()]
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to parse subtitle file %s: %s", path, e)
        return []


def _parse_json3(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    segments: List[Dict[str, Any]] = []
    for event in data.get("events", []):
        start_ms = event.get("tStartMs", 0) or 0
        segs = event.get("segs", [])
        text = "".join(seg.get("utf8", "") for seg in segs).strip()
        if text:
            segments.append({"start": round(start_ms / 1000, 2), "text": text})
    return segments


def _parse_srv3(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    segments: List[Dict[str, Any]] = []
    for item in data.get("body", []):
        content = item.get("content", "").strip()
        if content:
            start = item.get("from", 0) or 0
            try:
                start = round(float(start), 2)
            except (TypeError, ValueError):
                start = None
            segments.append({"start": start, "text": content})
    return segments


def _parse_timed_text(path: Path) -> List[Dict[str, Any]]:
    """Parse an SRT/VTT cue file into ``{start, text}`` segments."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    segments: List[Dict[str, Any]] = []
    for block in re.split(r"\r?\n\r?\n", text.strip()):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        timing_idx = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_idx is None:
            continue
        start = _parse_timestamp(lines[timing_idx])
        content = " ".join(lines[timing_idx + 1 :]).strip()
        if content:
            segments.append({"start": start, "text": content})
    return segments


def _parse_timestamp(cue_line: str) -> Optional[float]:
    """Parse the start timestamp (before '-->') of a cue timing line."""
    try:
        head = cue_line.split("-->")[0].replace(",", ".").strip()
        parts = [float(p) for p in head.split(":")]
        if len(parts) == 3:
            h, m, s = parts
        elif len(parts) == 2:
            h, m, s = 0, parts[0], parts[1]
        else:
            return None
        return round(h * 3600 + m * 60 + s, 2)
    except (ValueError, IndexError):
        return None


def _dedup(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Drop consecutive identical caption texts."""
    out: List[Dict[str, Any]] = []
    last = None
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        if last and text == last:
            continue
        out.append({"start": seg.get("start"), "text": text})
        last = text
    return out


def extract_subtitles(url: str) -> Dict[str, Any]:
    """
    Extract subtitles for a video URL (Bilibili-focused).

    Returns:
        dict with keys: ``title``, ``lang``, ``lines`` (list of ``{start, text}``),
        and ``text`` (plain transcript text).

    Raises:
        SubtitleError: if no usable Chinese subtitle is available.
    """
    def _discover_lang(use_cookies: bool) -> Dict[str, Any]:
        opts = _build_ydl_opts(extract_only=True, use_cookies=use_cookies)
        # yt-dlp only attaches ``subtitles`` / ``automatic_captions`` to the
        # info dict when a subtitle write is requested during extraction. Do it
        # here so we can discover which languages are available. ``download``
        # stays False, so requesting the write still writes no files.
        opts.update(
            {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": list(_SUBTITLE_LANGS),
                "subtitlesformat": "json3/srv3/best",
            }
        )
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _write_subtitle(lang: str, use_cookies: bool) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as tmpdir:
            opts = _build_subtitle_opts(use_cookies, tmpdir)
            opts["subtitleslangs"] = [lang]
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            title = info.get("title", "未知标题")
            segments: List[Dict[str, Any]] = []
            for f in Path(tmpdir).iterdir():
                if f.is_file():
                    segments.extend(_read_subtitle_file(f))
            return {"title": title, "segments": segments}

    def _meta_with_fallback() -> Dict[str, Any]:
        try:
            return _discover_lang(use_cookies=True)
        except (yt_dlp.utils.DownloadError, ValueError) as e:
            if _is_cookie_error(str(e)):
                state["cookie_failed"] = True
                logger.warning(
                    "Subtitle meta cookie extraction failed, retrying without cookies: %s",
                    str(e)[:100],
                )
                return _discover_lang(use_cookies=False)
            raise

    state = {"cookie_failed": False}

    meta = _meta_with_fallback()
    lang = _choose_language(meta)
    if not lang:
        if state["cookie_failed"]:
            raise SubtitleError(
                "读取 Cookie 失败。请用 Cookie-Editor 等扩展导出已登录 B 站的 "
                "cookies.txt，并在 .env 中配置 COOKIE_FILE 后重试（无需关闭 Edge）。"
            )
        raise SubtitleError(
            "该视频暂无可用的中文字幕（已探测其全部字幕语言）。若确认该视频有 "
            "AI 字幕，请检查 .env 中的 COOKIE_FILE 是否指向已登录 B 站的 cookies.txt 后重试。"
        )

    try:
        result = _write_subtitle(lang, use_cookies=True)
    except (yt_dlp.utils.DownloadError, ValueError) as e:
        if _is_cookie_error(str(e)):
            state["cookie_failed"] = True
            logger.warning(
                "Subtitle write cookie extraction failed, retrying without cookies: %s",
                str(e)[:100],
            )
            result = _write_subtitle(lang, use_cookies=False)
        else:
            raise

    lines = _dedup(result["segments"])
    text = " ".join(seg["text"] for seg in lines).strip()
    if not text and state["cookie_failed"]:
        raise SubtitleError(
            "读取 Cookie 失败。请用 Cookie-Editor 等扩展导出已登录 B 站的 "
            "cookies.txt，并在 .env 中配置 COOKIE_FILE 后重试（无需关闭 Edge）。"
        )
    return {
        "title": result["title"],
        "lang": lang,
        "lines": lines,
        "text": text,
    }
