"""
AI mind-map generation using DeepSeek.

Produces a hierarchical Markdown outline (``#`` central theme, ``##`` branches,
``-`` leaves) that the frontend renders with markmap into an interactive mind
map. Reuses the shared ``llm.chat`` client.
"""
from typing import Any, Dict

from . import llm

# Instruct the model to emit exactly the markmap-friendly structure: a single
# H1 as the central topic, H2 as main branches, and indented bullet lists as
# leaves. Markmap derives the tree from heading + list nesting.
_MINDMAP_SYSTEM_PROMPT = (
    "你是一名专业的思维导图生成助手，擅长将视频内容提炼为层级清晰的中文思维导图。\n"
    "请严格按以下 Markdown 层级格式输出，只输出导图本身，不要任何说明文字：\n"
    "- 第一行用 `# ` 开头，写视频的核心主题（作为中心节点）。\n"
    "- 用 `## ` 开头表示一级分支（3-6 个主要模块）。\n"
    "- 用 `- ` 缩进表示二级要点，可再缩进用 `- ` 表示三级细节。\n"
    "- 每个分支不超过 4 层，用语精炼，节点用短语而不是长句。\n\n"
    "示例结构：\n"
    "# 视频中心主题\n"
    "## 模块一\n"
    "- 要点1\n"
    "- 要点2\n"
    "## 模块二\n"
    "- 要点1\n"
    "- 子要点\n"
)

def generate_mindmap(text: str, title: str) -> Dict[str, Any]:
    """Generate a mind-map Markdown outline for the given transcript."""
    body = llm.truncate(text, llm.DEEPSEEK_MAX_CHARS)

    user_prompt = (
        f"请为以下视频生成思维导图。\n\n"
        f"【视频标题】{title}\n\n"
        f"【字幕内容】\n{body}"
    )

    messages = [
        {"role": "system", "content": _MINDMAP_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    markdown = llm.chat(messages, max_tokens=4096, temperature=0.3)
    return {"mindmap": markdown, "model": llm.DEEPSEEK_MODEL}
