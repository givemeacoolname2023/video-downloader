# 万能视频下载网站 - 技术方案文档

> 创建时间：2026-07-15
> 版本：v1.0（MVP）

---

## 一、技术选型

### 1.1 后端
| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|---------|
| Python | 3.10+ | 运行环境 | 与 yt-dlp 语言一致 |
| FastAPI | latest | Web 框架 | 异步支持好，适合 IO 密集型下载任务 |
| uvicorn | latest | ASGI 服务器 | FastAPI 官方推荐 |
| yt-dlp | latest | 视频下载核心 | GitHub 14 万+ star，支持 1000+ 平台 |
| python-multipart | latest | 文件上传 | FastAPI 依赖 |

### 1.2 前端
| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|---------|
| Vue 3 | latest | 前端框架 | 上手快，中文社区好 |
| Vite | latest | 构建工具 | 开发体验极佳，HMR 快 |
| TailwindCSS | 3.x | CSS 框架 | 快速开发响应式界面 |
| Axios | latest | HTTP 客户端 | 请求后端 API |
| Heroicons | latest | 图标库 | 简约 SVG 图标 |

### 1.3 开发工具
| 工具 | 用途 |
|------|------|
| npm | 前端包管理 |
| pip | Python 包管理 |

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────┐
│         前端 (Vue 3 + Vite)              │
│  ┌──────────┐ ┌──────────────────────┐  │
│  │ 首页      │ │ 下载页（核心功能）    │  │
│  │ 营销展示  │ │ URL 输入 → 解析      │  │
│  │ 功能介绍  │ │ 清晰度选择 → 下载    │  │
│  │ 付费引导  │ │ WebSocket 进度推送   │  │
│  └──────────┘ └──────────────────────┘  │
│  port: 5173 (Vite dev server)            │
└──────────────────┬──────────────────────┘
                   │ HTTP REST + WebSocket
┌──────────────────▼──────────────────────┐
│         后端 (FastAPI)                   │
│  ┌────────────────────────────────────┐  │
│  │  API 路由                           │  │
│  │  POST /api/parse    → 解析视频信息   │  │
│  │  POST /api/download → 开始下载任务    │  │
│  │  WS   /ws/download/{task_id} → 进度 │  │
│  │  GET  /api/download/{task_id} → 文件 │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  yt-dlp 封装层 (downloader.py)     │  │
│  │  - subprocess 调用 yt-dlp          │  │
│  │  - 解析进度输出                     │  │
│  │  - 文件管理                         │  │
│  └────────────────────────────────────┘  │
│  port: 8000                              │
└─────────────────────────────────────────┘
```

### 2.2 数据流

```
用户输入 URL
    │
    ▼
POST /api/parse ──► yt-dlp --dump-json ──► 返回视频信息（标题、封面、清晰度列表）
    │
用户选择清晰度
    │
    ▼
POST /api/download ──► 创建下载任务 ──► 返回 task_id
    │
    ▼
WebSocket /ws/download/{task_id} ──► 实时推送下载进度
    │
    ▼
GET /api/download/{task_id} ──► 返回视频文件（StreamingResponse）
```

### 2.3 安全设计

- URL 校验：使用 Python `validators` 库验证 URL 格式
- 命令注入防护：使用 `shlex.join()` 构建 yt-dlp 命令参数
- 文件清理：下载完成后定时清理（1 小时后自动删除）
- CORS：仅允许前端域名访问

---

## 三、目录结构

```
video-downloader/
├── docs/
│   ├── requirements.md          # 需求分析文档
│   └── architecture.md          # 技术方案文档（本文件）
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── App.vue              # 根组件
│   │   ├── main.js              # 入口文件
│   │   ├── style.css            # 全局样式 + Tailwind
│   │   ├── views/
│   │   │   ├── HomeView.vue     # 首页（营销）
│   │   │   └── DownloadView.vue # 下载页（核心）
│   │   ├── components/
│   │   │   ├── NavBar.vue       # 导航栏
│   │   │   ├── Footer.vue       # 页脚
│   │   │   ├── SearchBar.vue    # URL 输入搜索栏
│   │   │   ├── VideoInfo.vue    # 视频信息展示卡片
│   │   │   ├── QualitySelect.vue# 清晰度选择器
│   │   │   ├── DownloadProgress.vue # 下载进度条
│   │   │   └── FeatureCard.vue  # 功能特性卡片
│   │   └── utils/
│   │       └── api.js           # API 请求封装
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── package.json
├── backend/                     # FastAPI 后端
│   ├── main.py                  # 入口文件
│   ├── downloader.py            # yt-dlp 封装
│   ├── models.py                # Pydantic 数据模型
│   ├── requirements.txt         # Python 依赖
│   └── downloads/               # 下载文件存放目录（gitignore）
├── .env                         # 环境变量
├── .gitignore
└── 提示词.md
```

---

## 四、API 设计

### 4.1 POST /api/parse
**描述**：解析视频 URL，返回视频信息

**请求体**：
```json
{
  "url": "https://www.youtube.com/watch?v=xxxxx"
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "title": "视频标题",
    "duration": 3600,
    "thumbnail": "https://...",
    "uploader": "作者名",
    "formats": [
      { "format_id": "18", "resolution": "640x360", "ext": "mp4", "filesize": 52428800 },
      { "format_id": "22", "resolution": "1280x720", "ext": "mp4", "filesize": 104857600 }
    ]
  }
}
```

### 4.2 POST /api/download
**描述**：开始下载视频

**请求体**：
```json
{
  "url": "https://www.youtube.com/watch?v=xxxxx",
  "format_id": "22"
}
```

**响应**：
```json
{
  "success": true,
  "task_id": "uuid-string"
}
```

### 4.3 WebSocket /ws/download/{task_id}
**描述**：实时推送下载进度

**消息格式**：
```json
{
  "type": "progress",
  "percentage": 45.5,
  "speed": "2.3MiB/s",
  "eta": "00:30",
  "downloaded": "15.2MiB",
  "total": "50.0MiB"
}
```

完成消息：
```json
{
  "type": "completed",
  "filename": "video.mp4"
}
```

错误消息：
```json
{
  "type": "error",
  "message": "下载失败原因"
}
```

### 4.4 GET /api/download/{task_id}/file
**描述**：下载完成后获取视频文件（流式传输）

**响应**：`application/octet-stream` 文件流

---

## 五、UI 设计参考

参考网站：https://ai.codefather.cn/painting（鱼皮 AI）

### 设计特点提取：
| 元素 | 参考样式 |
|------|---------|
| 布局 | 卡片网格布局，最大宽度 1200px 居中 |
| 配色 | 主色：渐变色（蓝紫/橙红），卡片白底圆角阴影 |
| 搜索栏 | 顶部居中大搜索框，placeholder 引导文案 |
| 卡片 | 封面图 + 标题 + 标签，hover 效果 |
| 字体 | 现代无衬线字体，标题加粗 |
| 动效 | 卡片 hover 上浮，过渡动画 |
| CTA | 渐变按钮，大字号，醒目文案 |

### 本项目配色方案：
| 颜色 | 色值 | 用途 |
|------|------|------|
| 主色 | `#667eea` → `#764ba2`（蓝紫渐变） | 按钮、标题、重点元素 |
| 辅色 | `#f093fb` → `#f5576c`（粉红渐变） | CTA 按钮、强调文字 |
| 背景 | `#f8fafc`（浅灰） | 页面背景 |
| 卡片 | `#ffffff` | 卡片背景 |
| 文字 | `#1e293b` | 主要文字 |
| 次要文字 | `#64748b` | 描述文字 |

---

## 六、开发计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| 1 | 搭建前端项目骨架（Vue 3 + Vite + TailwindCSS） | 待开发 |
| 2 | 搭建后端项目骨架（FastAPI + yt-dlp） | 待开发 |
| 3 | 实现核心下载 API | 待开发 |
| 4 | 实现前端下载页面（参考鱼皮 AI 风格） | 待开发 |
| 5 | 本地测试验证 | 待开发 |
| 6 | Stripe 支付集成 | 后续 |
| 7 | AI 增值功能 | 后续 |