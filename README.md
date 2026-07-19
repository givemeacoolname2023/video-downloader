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