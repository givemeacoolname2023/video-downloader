"""
AI video summarization using the DeepSeek API (OpenAI-compatible).

Sends extracted subtitles to DeepSeek and returns a structured Chinese summary.
Uses ``httpx`` directly (already a project dependency) instead of the OpenAI SDK.
"""
import os
import logging
from pathlib import Path
from typing import Any, Dict

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


class SummaryError(Exception):
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
    if not DEEPSEEK_API_KEY:
        raise SummaryError("未配置 DEEPSEEK_API_KEY，请在 .env 中设置后重启后端。")

    # Truncate long transcripts to stay within the model context window.
    if len(text) > DEEPSEEK_MAX_CHARS:
        text = text[: DEEPSEEK_MAX_CHARS] + "\n……（字幕过长，超出部分已省略）"

    user_prompt = (
        f"请对以下视频内容进行总结。\n\n"
        f"【视频标题】{title}\n\n"
        f"【字幕内容】\n{text}"
    )

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=180.0) as client:
            resp = client.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
        resp.raise_for_status()
        data = resp.json()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        if not content:
            raise SummaryError("AI 返回内容为空，请稍后重试。")
        return {"summary": content, "model": DEEPSEEK_MODEL}
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.text[:300]
        except Exception:  # noqa: BLE001
            pass
        raise SummaryError(f"AI 接口调用失败（{e.response.status_code}）：{detail}")
    except httpx.HTTPError as e:
        raise SummaryError(f"AI 接口请求失败：{str(e)[:200]}")
