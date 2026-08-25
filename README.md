# 万能视频下载网站

基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的视频下载工具，支持 1000+ 平台（YouTube、Bilibili、Twitter 等），提供美观的 Web 界面和实时下载进度。

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 0.115.x |
| 服务器 | uvicorn | 0.34.x |
| 下载引擎 | yt-dlp | 2024.12.x |
| 前端框架 | Vue 3 | 3.4.x |
| 构建工具 | Vite | 5.x |
| CSS 框架 | TailwindCSS | 3.x |
| HTTP 客户端 | Axios | 1.7.x |

## 目录结构

```
video-downloader/
├── docs/                        # 文档
│   ├── requirements.md          # 需求分析文档
│   └── architecture.md          # 技术方案文档
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── App.vue              # 根组件
│   │   ├── main.js              # 入口文件
│   │   ├── style.css            # 全局样式
│   │   ├── views/               # 页面视图
│   │   ├── components/          # 组件
│   │   └── utils/               # 工具函数（API 封装）
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── tailwind.config.js
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # 入口文件
│   │   ├── downloader.py        # yt-dlp 封装
│   │   └── downloads/           # 下载文件存放目录
│   ├── run.py                   # 启动脚本
│   └── requirements.txt         # Python 依赖
├── start-backend.bat            # Windows 一键启动后端
├── start-frontend.bat           # Windows 一键启动前端
└── README.md
```

## 环境要求

- **Python** 3.10+
- **Node.js** 16+（推荐 18+）
- **npm** 8+

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/givemeacoolname2023/video-downloader.git
cd video-downloader
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
cd ..
```

> 建议使用虚拟环境：
> ```bash
> python -m venv venv
> source venv/bin/activate  # Linux/Mac
> venv\Scripts\activate     # Windows
> pip install -r backend/requirements.txt
> ```

### 3. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

## 运行项目

### 方式一：双击 bat 脚本（Windows）

1. 双击 `start-backend.bat` 启动后端
2. 双击 `start-frontend.bat` 启动前端

### 方式二：命令行启动

**启动后端**（端口 8000）：

```bash
cd backend
python run.py
```

**启动前端**（端口 5173）：

```bash
cd frontend
npm run dev
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:5173 |
| 后端 API 文档（Swagger） | http://127.0.0.1:8000/docs |

## API 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/parse` | 解析视频 URL，返回视频信息（标题、清晰度等） |
| POST | `/api/download` | 创建下载任务，返回 task_id |
| POST | `/api/summary` | 提取平台字幕并用 DeepSeek 生成 AI 视频总结 |
| POST | `/api/mindmap` | 基于同一份字幕生成层级思维导图（Markdown） |
| POST | `/api/qa` | 基于字幕进行多轮 AI 问答（SSE 流式） |
| WS | `/ws/download/{task_id}` | WebSocket 实时推送下载进度 |
| GET | `/api/download/{task_id}/file` | 下载完成后获取视频文件 |

详细请求/响应格式请参考 [技术方案文档](./docs/architecture.md) 或访问 Swagger 文档页面。

## 注意事项

- 下载的视频文件存放在 `backend/app/downloads/` 目录，1 小时后自动清理
- 请遵守各平台的用户协议和版权法规，仅下载有权限的内容
- 首次使用 yt-dlp 可能较慢，因为它会下载最新的提取器信息

## 开发计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| 1 | 搭建前端项目骨架 | ✅ |
| 2 | 搭建后端项目骨架 | ✅ |
| 3 | 实现核心下载 API | ✅ |
| 4 | 实现前端下载页面 | ✅ |
| 5 | 本地测试验证 | 进行中 |
| 6 | Stripe 支付集成 | 后续 |
| 7 | AI 增值功能 | 后续 |

## 自定义配置

以下是项目中可根据实际需求调整的参数，修改前建议先了解各参数的作用。

### 后端核心参数（`backend/app/downloader.py`）

| 参数 | 默认值 | 说明 | 修改方式 |
|------|--------|------|----------|
| `COOKIE_FILE` | （空） | 导出的 `cookies.txt` 绝对路径（Netscape 格式，含 B 站登录 cookie），用于获取需要登录的 AI 字幕。优先于浏览器读 Cookie | 在根目录 `.env` 设置，如 `COOKIE_FILE=D:/bilibili_cookies.txt` |
| `DOWNLOAD_DIR` | `backend/app/downloads/` | 下载文件存放目录 | 改为 `Path("D:/Downloads")` 等绝对路径 |
| `_CLEANUP_INTERVAL` | `3600` 秒（1小时） | 已下载文件的自动清理间隔 | 在 `_cleanup_old_files` 函数中修改 |
| `ytdl_format` | `'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'` | 下载格式优先级 | 按 yt-dlp format string 语法修改 |
| `merge_output_format` | `"mp4"` | 合并后的视频容器格式 | 可改为 `"mkv"` 等 |
| `concurrent_fragment_downloads` | `8` | 并发分片下载数 | 网络较慢时可适当减小 |
| `quiet` / `no_warnings` | `True` / `True` | 是否隐藏 yt-dlp 日志 | 调试时改为 `False` 可查看详细日志 |

### 后端服务参数（`backend/run.py`）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `host` | `"127.0.0.1"` | 后端绑定地址，改为 `"0.0.0.0"` 可局域网访问 |
| `port` | `8000` | 后端端口 |
| `reload` | `True` | 代码修改后自动重启，生产环境应改为 `False` |
| `log_level` | `"info"` | 日志级别：`debug` / `info` / `warning` / `error` |

### FastAPI 应用参数（`backend/app/main.py`）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `title` | `"Video Downloader API"` | Swagger 文档标题 |
| `version` | `"1.0.0"` | API 版本号 |
| `allow_origins` | `["*"]` | CORS 允许的来源域名，生产环境应限制为具体域名 |

### 视频总结参数（`backend/app/summary.py` + `.env`）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `DEEPSEEK_API_KEY` | （必填） | DeepSeek API Key，用于生成 AI 总结，在根目录 `.env` 配置 |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | DeepSeek 模型名（`deepseek-chat` 已于 2026-07-24 弃用） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek API 地址 |
| `DEEPSEEK_MAX_CHARS` | `30000` | 送入模型前截断的字幕最大字符数 |

### 配置 Cookie（获取 B 站 AI 字幕）

视频总结依赖字幕，而 B 站的 **AI 字幕（`ai-zh`）需要登录**才能通过平台接口拿到。因此需要把浏览器里已登录 B 站的 cookie 导出给 yt-dlp。

#### 为什么要用 cookies.txt 而不是 `--cookies-from-browser`

本项目**不使用 `--cookies-from-browser`**（原方案），原因：

1. Edge 运行时，其 cookie 数据库会被锁定，yt-dlp 无法复制，报 `Could not copy Chrome cookie database`。
2. Chrome/Edge **v127+** 引入了 app-bound 加密，解密密钥绑定到浏览器自身二进制，外部程序（即使是管理员）也无法解密，yt-dlp 官方已声明不会修复 Windows 上的该问题。**就算关掉 Edge 也可能失败**。

改用 `cookies.txt` 后则完全绕开这两个问题：扩展导出的是**明文**，既不依赖浏览器进程，也不受加密影响，而且**全程无需关闭 Edge**。B 站 `SESSDATA` 的**到期时间**通常数月至更久；但注意服务端也可能**提前静默失效**旧会话（见下方排错），届时需重新导出一次。

#### 导出 cookies.txt 的步骤

1. 在 Edge 中登录 B 站（网页版）。
2. 安装并打开 **Cookie-Editor** 扩展。
3. 点击扩展图标 → `Export` → 选择 **Netscape format（netscape / cookies.txt）**，会下载一个 `cookies.txt` 文件。

> ⚠️ 请使用 **Cookie-Editor**（或同类可信扩展）导出。不要使用曾被曝「偷取 cookie」的「Get cookies.txt」类扩展，避免泄露登录凭证。

#### 配置路径

把导出的文件放到项目内（**务必确认它已被忽略**，见下方 `.gitignore`），然后在根目录 `.env` 中配置其**绝对路径**：

```bash
COOKIE_FILE=E:/bilibili_cookies.txt
```

保存后**重启后端**即可。未配置 `COOKIE_FILE` 时，公开视频仍可解析、下载、总结，仅 B 站 AI 字幕受限。

#### 排错：下载只剩 480p / 只有一个清晰度选项

`cookies.txt` 里的 `SESSDATA` **过期时间在未来，不代表还能登录**。B 站在服务端会由于以下原因**静默失效**旧会话：在其它设备重新登录、退出登录、改密，或平台强制重登。一旦失效，yt-dlp 会被当作**匿名**用户，导致：

- 所有视频清晰度被限到 **360p/480p**（界面只剩一两个低清选项）；
- 大会员专属的 **1080p60 / 4K** 视频直接返回 **0 个可下载格式**，报「解析失败」。

判断方法（后端/命令行跑一次）：

```bash
# 来自 cookies.txt 的 SESSDATA，nav 返回 code=-101 即「账号未登录」
python -c "import httpx;c={'SESSDATA':'你的值'};print(httpx.get('https://api.bilibili.com/x/web-interface/nav',cookies=c,headers={'Referer':'https://www.bilibili.com/','User-Agent':'Mozilla/5.0'}).json().get('code'))"
```

**修复**：重新执行上面的「导出步骤」，导出**当前已登录** B 站的干净 `cookies.txt`，覆盖旧文件后重启后端。别复用旧文件。

#### 安全提醒

`cookies.txt` 含你的 B 站登录凭证，**绝不能提交到仓库**。项目已在 `.gitignore` 中忽略：

```gitignore
# Cookie 凭证文件（含登录态，绝不可提交）
cookies.txt
*.cookies
```

导入导出遵循该约定即可。

### 视频增强功能：思维导图与 AI 问答

在视频卡片下方提供三个能复用同一份字幕的 AI 功能（都在解析出视频后使用）：

| 功能 | 接口 | 说明 |
|------|------|------|
| 视频总结 | `POST /api/summary` | 生成结构化中文总结（一句话概括/内容大纲/知识点/结论） |
| 思维导图 | `POST /api/mindmap` | 生成层级 Markdown，前端用 markmap 渲染成可缩放/折叠的交互式导图 |
| AI 问答 | `POST /api/qa` | 基于字幕多轮问答，SSE 流式逐字输出 |

字幕通过**进程内内存缓存**按 URL 复用：`summary` / `mindmap` / `qa` 三个接口共享同一个提取结果，第一个功能触发提取后，其余直接复用，不会重复请求平台。缓存有容量上限（默认 50 条），进程重启后清空。

问答与导图不依赖先点「总结」——各自会按需自动提取字幕。字幕仍来自平台接口（B 站 AI 字幕需登录，见上方 Cookie 配置）。

#### 重要

`/api/qa` 使用 **SSE（text/event-stream）** 流式返回。前端通过 `fetch` + `ReadableStream` 消费，因此开发时代理需保持流式转发，不要用会缓冲整个响应的中间件。生产环境部署到 Nginx 时需设置 `X-Accel-Buffering: no`（后端已设置该响应头）。

### 前端构建参数（`frontend/vite.config.js`）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `server.port` | `5173` | 前端开发服务器端口 |
| `proxy['/api'].target` | `'http://localhost:8000'` | 后端 API 代理目标地址 |
| `proxy['/ws'].target` | `'ws://localhost:8000'` | WebSocket 代理目标地址 |

> ⚠️ 修改端口后，请同步更新 `start-frontend.bat` 和 `start-backend.bat` 中的端口提示信息。

### 前端请求参数（`frontend/src/utils/api.js`）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `timeout` | `30000`（30秒） | axios 请求超时时间（毫秒），解析较大视频可适当调大 |
| `baseURL` | `'/api'` | API 基础路径，一般不修改 |

### 前端显示参数（`frontend/src/views/DownloadView.vue`）

`supportedPlatforms` 数组控制页面底部展示的平台名称列表，可按需增删。
