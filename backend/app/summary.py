"""
AI video summarization using the DeepSeek API (OpenAI-compatible).

Sends extracted subtitles to DeepSeek and returns a structured Chinese summary.
The network/client concerns live in :mod:`app.llm`; this module only builds the
prompt and formats the result. :func:`summary_stream` exposes a streaming
(token-by-token) variant so the frontend can render the summary as it arrives.
"""
import asyncio
from typing import Any, AsyncIterator, Dict

from . import llm
from .context import get_transcript
from .llm import LLMError

_sse = llm.sse_event

# ``SummaryError`` is kept separate (subclassing ``LLMError``) so callers can
# catch it, and for backward-compatible imports in ``main.py``.
class SummaryError(LLMError):
    """Raised when a summary cannot be generated."""


_SYSTEM_PROMPT = (
    "你是一名专业的视频内容分析助手，擅长将长视频的语音/字幕内容提炼为结构化的中文总结。\n"
    "请严格按以下 Markdown 格式输出：\n\n"
    "## 一句话概括\n用一句话概括视频主旨。\n\n"
    "## 内容大纲\n- 按时间或主题列出核心部分（3-6 条）。\n\n"
    "## 关键知识点\n- 用要点列出视频中的核心信息、概念、数据或方法论。\n\n"
    "## 结论与价值\n给出视频的结论，以及对观众的帮助或启发。\n\n"
    "只输出总结本身，不要添加开场白、结束语或任何其它说明。"
)


def summarize_video(text: str, title: str) -> Dict[str, Any]:
    """Generate a structured Chinese summary of the given transcript."""
    body = llm.truncate(text, llm.DEEPSEEK_MAX_CHARS)

    user_prompt = (
        f"请对以下视频内容进行总结。\n\n"
        f"【视频标题】{title}\n\n"
        f"【字幕内容】\n{body}"
    )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    content = llm.chat(messages, max_tokens=4096, temperature=0.3)
    return {"summary": content, "model": llm.DEEPSEEK_MODEL}


async def summary_stream(url: str) -> AsyncIterator[str]:
    """Stream a video summary as SSE events (token-by-token).

    Mirrors ``/api/qa``'s event shape: ``data: {"text": "..."}`` per chunk,
    ``data: {"done": true}`` at the end, ``data: {"error": "..."}`` on failure.
    """
    try:
        transcript = await asyncio.to_thread(get_transcript, url)
    except Exception as e:  # noqa: BLE001
        yield _sse({"error": str(e)[:300]})
        return

    user_prompt = (
        f"请对以下视频内容进行总结。\n\n"
        f"【视频标题】{transcript['title']}\n\n"
        f"【字幕内容】\n{llm.truncate(transcript['text'], llm.DEEPSEEK_MAX_CHARS)}"
    )
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        async for chunk in llm.stream_chat(messages, max_tokens=4096, temperature=0.3):
            yield _sse({"text": chunk})
        yield _sse({"done": True})
    except LLMError as e:
        yield _sse({"error": str(e)[:300]})
