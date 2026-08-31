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

---

## 七、前端布局重构（v1.1）

> 目标：把「视频信息（下载）」与「AI 总结」放到同一屏，让用户解析视频后就能同屏看到信息与总结，无需多次点击。

### 7.1 设计决策（已人工确认）

| 决策点 | 结论 |
|--------|------|
| 右侧 AI 区组织方式 | **标签页切换**（紧凑、贴合 bibigpt 参考稿） |
| 字幕列表位置 | **右栏第 4 个标签**（与总结/导图/问答并列） |
| 解析后自动触发 | **仅自动生成「AI 总结」**（SSE 流式），导图/问答/字幕仍手动 |

### 7.2 布局结构

```
┌──────────────────────────────────────────────────────────┐
│ 搜索栏（居中）                                              │
├──────────────┬───────────────────────────────────────────┤
│ 左栏 380px   │ 右栏（弹性）                                 │
│ 视频信息卡片  │  [AI总结][思维导图][AI问答][字幕列表]        │
│ · 封面(16:9) │  ─────────────────────────────             │
│ · 标题/元信息│  当前标签内容（v-show 保活）                 │
│ · 清晰度选择 │                                             │
│ · 下载按钮   │                                             │
└──────────────┴───────────────────────────────────────────┘
```

- 桌面端（`lg` 及以上）两栏并排；手机/平板堆叠成单列（视频卡片在前，AI 标签在后）。
- 各 AI 面板用 `v-show` 切换保留状态（对话历史、已生成总结等不因切换丢失）。

### 7.3 关键代码点

| 文件 | 作用 |
|------|------|
| `frontend/src/components/AiFeatureTabs.vue` | 新增的标签容器，管理 4 个标签与页签切换 |
| `frontend/src/components/SummaryPanel.vue` | 新增 `auto` 属性：挂载且有 URL 时自动流式生成总结 |
| `frontend/src/components/MindMapPanel.vue` | 新增 `active` 属性：标签页变为可见时才渲染 markmap（避免 display:none 下读不到宽高导致导图塌缩） |
| `frontend/src/views/DownloadView.vue` | 改为双栏 grid：左视频卡 + 右 AiFeatureTabs |

### 7.4 后端

无改动。总结/导图/字幕/问答仍复用同一份字幕缓存（`context.get_transcript`），解析后自动调 `/api/summary` 即可。

---

## 八、SEO 搜索引擎优化（v1.2）

> 目标：让用户在各大搜索引擎能优先看到本站内容。核心是把「纯客户端渲染的 SPA」升级为「构建时预渲染 + 结构化数据」，让每个页面在 HTML 源码里就有完整内容与语义标签，搜索引擎无需执行 JS 也能读懂。

### 8.1 关键约束（决定了技术路线）

- 当前 sandbox 无法访问 `registry.npmjs.org`（HTTP 000），**无法安装任何新依赖**（Playwright / puppeteer / @prerenderer 等预渲染插件都不能用）。
- 本项目已自带 `@vue/server-renderer`（随 vue 一起）与 `vue-router`（含 `createMemoryHistory`）。
- 因此选 **零依赖的 Vite-SSR 预渲染**：构建后用一个 Node 脚本跑 `renderToString` 生成静态 HTML，无需任何额外包。

### 8.2 实现方式（构建时预渲染）

`npm run build` 现在为 `vite build && node prerender.mjs`，分两步：

1. `vite build`：照常产出 SPA 到 `dist/`（含 `index.html`、哈希后的 JS/CSS）。
2. `node prerender.mjs`：
   - 用 Vite 的 `createServer({ server: { middlewareMode: true } })` + `ssrLoadModule('/src/entry-server.js')` 加载 SSR 入口；
   - 对 `['/', '/download']` 各调用 `render(path)`，用 `renderToString` 得到该路由的静态 HTML；
   - 把结果注入到 `dist/*.html` 的 `<div id="app">`，并按路由重写 `<title>` / `meta description` / `canonical` / `og:*` / `twitter:*`；
   - 生成 `dist/robots.txt` 与 `dist/sitemap.xml`。
   - **容错**：任一路由渲染失败只打印错误并跳过，不会让 `npm run build` 失败，`dist/` 仍保留可用的 SPA 产出。

### 8.3 新增 / 修改文件

| 文件 | 类型 | 作用 |
|------|------|------|
| `frontend/src/seo.config.js` | 新增 | **统一配置中心**：`SITE_URL`（占位域名）、每页 `title/description`、站点级 JSON-LD `siteSchema()`。改域名只改这一处。 |
| `frontend/src/entry-server.js` | 新增 | SSR 入口：为每个路径新建 Vue + 内存路由实例，`renderToString` 输出 `{ html, title, description }`。 |
| `frontend/prerender.mjs` | 新增 | 构建后预渲染脚本（见 8.2），同时生成 robots.txt / sitemap.xml。 |
| `frontend/scripts/make-og.mjs` | 新增 | 零依赖生成 1200×630 的 OG 占位图 `public/og.png`（手写 PNG + zlib 压缩）。 |
| `frontend/public/favicon.svg` | 新增 | 修复原先 `<link rel="icon" href="/favicon.svg">` 指向的空文件 404。 |
| `frontend/index.html` | 修改 | 修 viewport（移除 `user-scalable=no`）、加 `robots`/`theme-color` meta、`SEO_BLOCK` 占位（含 OG/Twitter/canonical）。 |
| `frontend/src/router/index.js` | 修改 | `history` 条件化（浏览器 `createWebHistory`，Node 用 `createMemoryHistory`），`beforeEach` 加 `typeof document !== 'undefined'` 守卫；每页 `meta` 增加 `description`。 |
| `frontend/src/main.js` | 未改 | 保持 `createApp`，零改动，无运行时行为变更。 |
| `frontend/package.json` | 修改 | `build` → `vite build && node prerender.mjs`；新增 `build:spa`（仅 SPA）、`prerender`、`make:og` 脚本。 |

### 8.4 落地 SEO 要素

- **预渲染正文**：首页 Hero / 功能 / 三步流程 / 定价，下载页搜索栏与平台列表，全部写进 HTML 源码。
- **标题 & 描述**：每页独立，主关键词前置，首页与下载页文案不同，避免站内互相抢词。
- **Canonical**：每页自指；`/download` 页面 canonical 为 `/download`。站内各自独立。
- **Open Graph / Twitter Card**：`summary_large_image`，指向 `/og.png`。
- **JSON-LD 结构化数据**：`WebSite`（含 `SearchAction` 站内搜索）、`Organization`、`SoftwareApplication`。
- **robots.txt**：`Allow: /` + `Sitemap` 指引；**sitemap.xml**：`/` 与 `/download`，含 `lastmod / changefreq / priority`。
- **favicon**：写入真实 SVG，消除 404。

### 8.5 上线前只需做的一件事

改 `frontend/src/seo.config.js` 里的 `SITE_URL` 为真实域名，然后 `npm run build`。预渲染脚本会据此自动重写所有 canonical / OG / robots / sitemap 的绝对地址。

### 8.6 部署注意

- 预渲染在 `dist/` 里同时产出 `index.html` 与 `download.html`，静态托管需把 `/download` 映射到 `download.html`（否则 `/download` 会 404）。
  - Netlify：在 `public/` 放 `_redirects` 内容 `/*  /index.html  200` 交给 SPA；或配置 rewrite。
  - Vercel：默认 `/download` 走 SPA 回退到 `index.html`。若要让 /download 返回其独立 HTML，需在 `vercel.json` 加 rewrite。这会与「SPA 回退」二选一，请按托管平台实际选择。
- 目前 `SITE_URL` 为 `https://example.com` 占位，仅用于尚未部署/无域名阶段。所有绝对地址均由此单一来源生成。

---

## 九、GEO 生成式引擎优化（v1.3）

> 目标：让用户在与 AI 对话（ChatGPT、Claude、Perplexity、DeepSeek、Google AI Overviews 等）被问到「视频下载 / 视频总结」类问题时，优先看到并引用本站。GEO 的关键是「让 AI 更容易提取、更愿意引用、更信任」。

GEO 与 SEO 不同：SEO 优化的是 URL 收录与排名；GEO 优化的是**内容的结构化程度、可引用性、可信度与站点自述**，让 LLM 能从页面里直接抽取到权威、自洽的答案。

### 9.1 决策（已人工确认）

| 决策点 | 结论 |
|--------|------|
| FAQ 放置 | **首页新增「常见问题」区块**（不改路由），并同步注入 FAQPage JSON-LD |
| llms.txt | **生成**（AI 专用站点摘要，事实标准，纯静态文本） |
| 信任页面 | **新增「隐私政策 + 服务条款」两页**（含 About/联系方式），带路由 + 预渲染 + 页脚接入 |

### 9.2 落地内容

1. **FAQ 区块 + FAQPage JSON-LD**
   - 首页 `#faq` 区块（`<details>/<summary>` 原生展开），面向 AI 与用户列 8 条真实问答（平台支持、水印、版权、清晰度、付费、AI 功能、多端、链接留存）。
   - 首页 `<head>` 注入 `FAQPage` 结构化数据（8 组 `Question/Answer`），与区块正文**同源于 `faq.js`**——改一处两边同步，杜绝文案/结构漂移。
2. **llms.txt**
   - 预渲染阶段从 `SITE_URL` 与 FAQ 数据生成 `dist/llms.txt`，用纯文本自述站点：是什么/主要能力/典型问题/权威页面入口。
3. **信任与 E-E-A-T 页面**
   - `/privacy`（隐私政策）与 `/terms`（服务条款），含联系邮箱与关于说明。AI 系统与评估方看重透明、合规与可信，这两页同时提供可被引用的权威背景。
   - 页脚「法律」栏接入真实路由，底部补充联系邮箱。

### 9.3 关键文件

| 文件 | 类型 | 作用 |
|------|------|------|
| `frontend/src/faq.js` | 新增 | FAQ **唯一真源**：`faq` 数组（文案）+ `faqPageSchema()`（JSON-LD）。浏览器与 Node 共用。 |
| `frontend/src/views/HomeView.vue` | 修改 | 新增 `#faq` 区块，`v-for faq` 渲染（仅新增内容，不改既有区块）。 |
| `frontend/src/views/PrivacyView.vue` / `TermsView.vue` | 新增 | 两个静态 SSR 安全的信任页。 |
| `frontend/src/router/index.js` | 修改 | 新增 `/privacy`、`/terms` 路由与 meta.description。 |
| `frontend/src/components/Footer.vue` | 修改 | 「法律」栏接入真实路由；「联系客服」改 mailto；底部补联系邮箱。 |
| `frontend/src/seo.config.js` | 修改 | 新增 `/privacy`、`/terms` 的 title/description。 |
| `frontend/prerender.mjs` | 修改 | 新增两条路由入预渲染/sitemap；首页 `@graph` 追加 `FAQPage`；生成 `dist/llms.txt`。 |

### 9.4 数据同源约定

- 站点级（站点名、域名、logo、OG 图）→ `src/seo.config.js` 唯一来源。
- FAQ 文案与 FAQPage schema → `src/faq.js` 唯一来源。
- 预渲染脚本从这两个模块取数，保证页面正文、JSON-LD、llms.txt、robots/sitemap 的绝对地址永远一致。

### 9.5 后续可进一步加强（本期未做）

- 按平台/场景产出「教程类」长文（如「如何下载某平台高清视频」），形成内容深度与可引用密度（GEO 最吃这一项）。
- 若上线后启用 SEO 内容，可扩充 sitemap、增加 `BreadcrumbList` 与 `VideoObject` 结构化数据。
- 上线后把 `llms.txt` 与 `sitemap.xml` 一并纳入浏览器/搜索引擎管理后台观察收录。