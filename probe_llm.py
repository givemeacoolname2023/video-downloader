import os, json
import httpx
os.environ.get  # noop
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"
print("API_KEY 存在:", bool(API_KEY), "len=", len(API_KEY))
print("MODEL =", MODEL)
payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "你是思维导图助手，输出 # 开头 + ## 分支 + - 叶子的层级 Markdown。"},
        {"role": "user", "content": "为《测试视频》生成思维导图。字幕：\n这是关于测试的短视频。"},
    ],
    "temperature": 0.3,
    "max_tokens": 1600,
    "stream": False,
}
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
with httpx.Client(timeout=60.0) as c:
    r = c.post(f"{BASE}/chat/completions", json=payload, headers=headers)
print("HTTP", r.status_code)
try:
    j = r.json()
    print("=== 顶层 keys:", list(j.keys()))
    ch = (j.get("choices") or [{}])
    if ch:
        msg = ch[0].get("message", {}) if isinstance(ch[0], dict) else {}
        print("=== message keys:", list(msg.keys()))
        print("content repr:", repr(msg.get("content")))
        print("reasoning_content repr:", repr(msg.get("reasoning_content"))[:200])
    else:
        print("无 choices, 完整:", json.dumps(j, ensure_ascii=False)[:500])
except Exception as e:
    print("解析失败:", e, r.text[:300])
