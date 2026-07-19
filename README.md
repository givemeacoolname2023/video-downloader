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
| `_COOKIE_BROWSERS` | `("edge",)` | yt-dlp 读取 Cookie 的浏览器，用于下载需要登录的平台视频 | 可改为 `("chrome",)`、`("firefox",)`、`("brave",)`，或多个 `("edge", "chrome")` |
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
