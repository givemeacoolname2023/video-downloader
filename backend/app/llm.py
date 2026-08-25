"""
Shared DeepSeek (OpenAI-compatible) chat client.

Centralises the API key/base-url/model config, the httpx call, and error
handling so the summary / mind-map / QA features don't each re-implement it.
Provides both a blocking :func:`chat` for non-streaming use (summary, mind map)
and an async generator :func:`stream_chat` for token-by-token output (QA).
"""
import os
import json
import logging
from pathlib import Path
from typing import AsyncIterator, Dict, List

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# The root .env lives one level above the backend/ directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
# default to the current chat model (deepseek-chat was deprecated on 2026-07-24)
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_MAX_CHARS = int(os.getenv("DEEPSEEK_MAX_CHARS", "30000"))


class LLMError(Exception):
    """Raised when an LLM chat request fails."""


def truncate(text: str, max_chars: int = DEEPSEEK_MAX_CHARS) -> str:
    """Truncate a long transcript to stay within the model context window."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n……（字幕过长，超出部分已省略）"


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }


def sse_event(obj: dict) -> str:
    """Serialize one SSE event in our ``data: {json}`` format."""
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def _raise_http_error(resp: httpx.Response, context: str) -> None:
    """Turn a non-2xx DeepSeek response into an LLMError with a readable message."""
    detail = ""
    try:
        detail = resp.text[:300]
    except Exception:  # noqa: BLE001
        pass
    raise LLMError(f"AI 接口调用失败（{resp.status_code}，{context}）：{detail}")


def chat(
    messages: List[Dict[str, str]],
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> str:
    """Non-streaming chat completion. Returns the full assistant reply string.

    ``deepseek-v4-flash`` is a reasoning model: it spends many output tokens on
    ``reasoning_content`` before emitting ``content``. A too-small ``max_tokens``
    can therefore starve the real answer (empty ``content``). We retry once with
    a doubled budget when the reply comes back empty.
    """
    if not DEEPSEEK_API_KEY:
        raise LLMError("未配置 DEEPSEEK_API_KEY，请在 .env 中设置后重启后端。")

    for attempt in (0, 1):
        budget = max_tokens * (2 ** attempt)
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": budget,
            "stream": False,
        }
        try:
            with httpx.Client(timeout=180.0) as client:
                resp = client.post(
                    f"{DEEPSEEK_BASE_URL}/chat/completions",
                    json=payload,
                    headers=_headers(),
                )
            if resp.status_code != 200:
                _raise_http_error(resp, "非流式")
            data = resp.json()
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
            if content:
                return content
            logger.warning("AI 返回内容为空，将以更大 max_tokens 重试（max_tokens=%s）", budget)
        except httpx.HTTPStatusError as e:
            _raise_http_error(e.response, "非流式")
        except httpx.HTTPError as e:
            raise LLMError(f"AI 接口请求失败：{str(e)[:200]}")

    raise LLMError("AI 返回内容为空，请稍后重试。")


async def stream_chat(
    messages: List[Dict[str, str]],
    max_tokens: int = 4096,
    temperature: float = 0.5,
) -> AsyncIterator[str]:
    """Streaming chat completion. Yields text chunks (``delta.content``).

    DeepSeek returns OpenAI-style ``data: {json}`` SSE lines, ending with
    ``data: [DONE]``. We inherit the upstream format and only forward the
    human-facing ``content`` delta (ignoring any internal ``reasoning_content``).
    """
    if not DEEPSEEK_API_KEY:
        raise LLMError("未配置 DEEPSEEK_API_KEY，请在 .env 中设置后重启后端。")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream(
                "POST",
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                json=payload,
                headers=_headers(),
            ) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", "ignore")
                    raise LLMError(f"AI 接口调用失败（{resp.status_code}）：{body[:300]}")

                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        payload_json = json.loads(data)
                    except ValueError:
                        continue
                    choices = payload_json.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {}) or {}
                    content = delta.get("content")
                    if content:
                        yield content
    except LLMError:
        raise
    except httpx.HTTPError as e:
        raise LLMError(f"AI 接口请求失败：{str(e)[:200]}")
