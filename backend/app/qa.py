"""
Multi-turn Q&A over a video's transcript, streamed token-by-token.

The transcript (and title) is loaded via the shared ``context.get_transcript``
cache, injected as system context, and the model answers a user question.
Conversation history is passed through for multi-turn continuity. The public
:func:`qa_stream` is an async generator that yields SSE ``data:`` events:
``{"text": "..."}`` per chunk, ``{"done": true}`` at the end, ``{"error": "..."}``
on failure.
"""
import asyncio
from typing import AsyncIterator, Dict, List

from . import llm
from .context import get_transcript

_sse = llm.sse_event

_QA_SYSTEM_PROMPT = (
    "你是一名精通视频内容的问答助手。我会给你一段视频的字幕内容和标题，"
    "你根据这些内容回答用户的提问。\n"
    "要求：\n"
    "- 回答要准确、简洁，用中文。\n"
    "- 只依据字幕内容作答；若字幕中确实没有相关信息，请明确说明“基于字幕内容无法得知”。\n"
    "- 不要编造字幕中没有的事实。\n"
)


def build_messages(
    title: str,
    transcript: str,
    history: List[Dict[str, str]],
    question: str,
) -> List[Dict[str, str]]:
    """Build the OpenAI message list: system context + history + new question."""
    context = (
        f"以下是视频【{title}】的字幕内容，仅作问答依据：\n\n"
        f"{llm.truncate(transcript, llm.DEEPSEEK_MAX_CHARS)}"
    )
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": _QA_SYSTEM_PROMPT + "\n\n" + context},
    ]
    # Pass through prior turns (if any) for multi-turn continuity.
    for turn in (history or [])[-10:]:
        role = turn.get("role")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": _clean(content)})
    messages.append({"role": "user", "content": _clean(question)})
    return messages


def _clean(text: str, limit: int = 4000) -> str:
    """Trim a history/query message to a sane length to bound the prompt."""
    text = (text or "").strip()
    if len(text) > limit:
        return text[:limit] + "…"
    return text


async def qa_stream(url: str, question: str, history: List[Dict[str, str]]) -> AsyncIterator[str]:
    """Stream an answer to *question* about the video at *url* as SSE events."""
    # Extract/load subtitles in a thread so the event loop stays free; report
    # failures as an SSE error event instead of a mid-stream exception.
    try:
        transcript = await asyncio.to_thread(get_transcript, url)
    except Exception as e:  # noqa: BLE001
        yield _sse({"error": str(e)[:300]})
        return

    messages = build_messages(transcript["title"], transcript["text"], history, question)

    try:
        async for chunk in llm.stream_chat(messages):
            yield _sse({"text": chunk})
        yield _sse({"done": True})
    except llm.LLMError as e:
        yield _sse({"error": str(e)[:300]})
