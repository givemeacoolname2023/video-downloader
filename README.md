# 万能视频下载网站

基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的视频下载工具，支持 1000+ 平台（YouTube、Bilibili、TikTok、抖音、Instagram 等），提供美观的 Web 界面、实时下载进度，以及 AI 视频总结 / 思维导图 / AI 问答 / 字幕导出等功能。

## 技术栈

### 后端（`backend/`）

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 0.115.x |
| ASGI 服务器 | uvicorn（standard） | 0.34.x |
| 下载引擎 | yt-dlp | 2024.12.x |
| 异步 HTTP | httpx | 0.28.x |
| WebSocket | websockets | 14.x |
| 表单解析 | python-multipart | 0.0.x |
| 环境变量 | python-dotenv | 1.0.x |
| 数据库 ORM | SQLAlchemy | 2.0.x |
| 数据库 | SQLite | 内置 |
| 支付 | Stripe | 9.x |
| JWT | PyJWT | 2.13.x |

### 前端（`frontend/`）

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue 3 | 3.4.x |
| 路由 | vue-router | 4.3.x |
| 构建工具 | Vite | 5.4.x |
| CSS 框架 | TailwindCSS | 3.4.x |
| HTTP 客户端 | axios | 1.7.x |
| 思维导图 | markmap-lib / markmap-view | 0.18.x |
| 图片导出 | html-to-image | 1.11.x |
| 图标 | @heroicons/vue | 2.1.x |
| 服务端渲染 | @vue/server-renderer | 随 vue 一并安装 |

## 目录结构

```
video-downloader/
├── docs/                        # 文档
│   ├── requirements.md          # 需求分析文档
│   └── architecture.md          # 技术方案文档
├── frontend/                    # Vue 3 前端
│   ├── public/                  # 静态资源（favicon.svg、og.png 等）
│   ├── scripts/
│   │   └── make-og.mjs          # 零依赖生成 1200×630 的 OG 图（公共占位图）
│   ├── prerender.mjs            # 构建后预渲染脚本（生成各路由静态 HTML + robots/sitemap/llms.txt）
│   ├── src/
│   │   ├── App.vue              # 根组件
│   │   ├── main.js              # 客户端入口
│   │   ├── entry-server.js      # 服务端（Node/预渲染）入口，导出 render(path)
│   │   ├── style.css            # 全局样式
│   │   ├── seo.config.js        # SEO/GEO 文案与域名的唯一真源（SITE_URL 等）
│   │   ├── faq.js               # FAQ 数据 + FAQPage 结构化数据的唯一真源
│   │   ├── router/
│   │   │   └── index.js         # 路由（含每个页面的 title/description）
│   │   ├── views/               # 页面视图
│   │   │   ├── HomeView.vue
│   │   │   ├── DownloadView.vue
│   │   │   ├── LoginView.vue        # 登录页（会员/账号）
│   │   │   ├── RegisterView.vue     # 注册页（会员/账号）
│   │   │   ├── MembershipView.vue   # 会员中心（订阅/状态）
│   │   │   ├── PrivacyView.vue
│   │   │   └── TermsView.vue
│   │   ├── components/          # 组件（NavBar/Footer/FeatureCard/DownloadProgressModal/
│   │   │                        #       LoadingSpinner/AiFeatureTabs/SummaryPanel/
│   │   │                        #       MindMapPanel/QaPanel/SubtitlePanel/InlineText）
│   │   ├── composables/
│   │   │   └── useAuth.js       # 全局登录/会员状态（单例，SSR 安全）
│   │   └── utils/
│   │       └── api.js           # axios 封装（含 token/设备号注入、账号/支付接口）
│   ├── index.html               # 入口 HTML（含 SEO_BLOCK_START/END 占位）
│   ├── vite.config.js
│   ├── package.json
│   └── tailwind.config.js
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 应用（路由注册、CORS、SSE、静态托管）
│   │   ├── db.py                # SQLAlchemy 引擎/会话/建表（SQLite：backend/data/app.db）
│   │   ├── models.py            # ORM 模型：User / Membership / DailyUsage / ProcessedEvent
│   │   ├── security.py          # PBKDF2 密码哈希 / JWT / 会员判定 / 额度 subject 解析
│   │   ├── gating.py            # 免费额度限额（下载/AI 各 3 次/天）与会员无限校验
│   │   ├── auth.py              # 账号注册/登录/me/device + 额度快照
│   │   ├── payments.py          # Stripe 订阅（checkout/webhook/幂等）+ PAYMENT_MOCK 离线模拟
│   │   ├── downloader.py        # yt-dlp 封装（解析/下载/进度/字幕/清理）
│   │   ├── context.py           # 共享上下文
│   │   ├── llm.py               # DeepSeek 客户端（summary/mindmap/qa 共用）
│   │   ├── summary.py           # AI 视频总结
│   │   ├── mindmap.py           # 思维导图（Markdown）
│   │   ├── qa.py                # AI 问答（SSE 流式）
│   │   ├── subtitles.py         # 字幕换轨道 / 导出 SRT·VTT·TXT
│   │   ├── downloads/           # 下载文件存放目录（自动清理）
│   │   ├── data/                # SQLite 数据库文件（.gitignore 已忽略，勿提交）
│   │   └── (cookies.txt)        # 本机 Cookie 凭证（.gitignore 已忽略，勿提交）
│   ├── test_membership_flow.py  # 会员支付离线冒烟测试（PAYMENT_MOCK=1，无需联网）
│   ├── run.py                   # 启动脚本
│   └── requirements.txt         # Python 依赖
├── .env                         # 环境变量（cookies 路径 / API Key，.gitignore 已忽略，勿提交）
├── start-backend.bat            # Windows 一键启动后端
├── start-frontend.bat           # Windows 一键启动前端
└── README.md
```

## 环境要求

- **Python** 3.9+（实际随附环境为 3.9.13；新代码均已做 3.9 兼容，用 `pyjwt`/`stripe`/`sqlalchemy` 时勿用 3.10+ 语法如 `X | Y` 联合类型）
- **Node.js** 16+（推荐 18+，预渲染脚本需要现代 Node，支持顶层 await）
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

### 4. 配置环境变量

复制根目录 `.env.example`（如存在）为 `.env`，或手动创建，至少配置后端必填项（见下文「自定义配置」）。未配置时后端也能启动，仅 AI 总结 / B 站字幕等功能不可用。

## 运行项目

**启动后端**（端口 8000）：

```bash
cd backend
python run.py
```

**启动前端**（端口 5173，开发模式）：

```bash
cd frontend
npm run dev
```

**构建并预渲染**（生产部署用，产物在 `frontend/dist/`）：

```bash
cd frontend
npm run build      # = vite build && node prerender.mjs
```

`preview` 命令可本地预览构建产物：

```bash
npm run preview
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端页面（开发） | http://localhost:5173 |
| 前端页面（构建产物预览） | http://localhost:4173 |
| 后端 API 文档（Swagger） | http://127.0.0.1:8000/docs |

## API 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 根路由，返回服务可用性信息 |
| POST | `/api/parse` | 解析视频 URL，返回视频信息（标题、清晰度、可用字幕等） |
| POST | `/api/download` | 创建下载任务，返回 `task_id` |
| GET | `/api/download-file/{task_id}` | 下载完成后获取视频文件 |
| GET | `/api/proxy-image` | 后端代理视频封面图（解决 Referer 防盗链） |
| GET | `/api/task/{task_id}` | 查询单个任务的实时状态 |
| WS | `/ws/{task_id}` | WebSocket 实时推送下载进度 |
| POST | `/api/summary` | 提取平台字幕并用 DeepSeek 生成 AI 视频总结 |
| POST | `/api/mindmap` | 基于同一份字幕生成层级思维导图（Markdown） |
| POST | `/api/subtitles` | 获取/换用字幕轨道，或导出 SRT / VTT / TXT |
| POST | `/api/qa` | 基于字幕进行多轮 AI 问答（SSE 流式） |
| POST | `/api/auth/register` | 注册账号（邮箱+密码），返回 JWT |
| POST | `/api/auth/login` | 登录，返回 JWT |
| GET | `/api/auth/me` | 当前用户 + 会员状态 + 额度快照（Bearer 必填） |
| GET | `/api/auth/device` | 颁发匿名设备号（免费额度按设备计数） |
| GET | `/api/quota` | 公共额度快照（支持匿名 device 或登录用户） |
| POST | `/api/payments/checkout` | 创建 Stripe 订阅 Checkout（需登录） |
| POST | `/api/payments/webhook` | Stripe webhook（验签 + 幂等），会员状态唯一可信来源 |
| POST | `/api/dev/mock-activate` | Mock 模式专用：模拟付款成功、授予会员 |
| POST | `/api/dev/webhook-drive` | Mock 模式专用：驱动任意签名 webhook 事件 |

> 注意：WebSocket 路径为 **`/ws/{task_id}`**，下载文件接口为 **`/api/download-file/{task_id}`**（均为后端代理/文件流式提供）。

详细请求/响应格式请参考 [技术方案文档](./docs/architecture.md) 或访问 Swagger 文档页面。

## SEO / GEO 优化

本项目针对两种「被发现」的场景做了专项优化；两者共用一个**统一的文案/域名真源**，改一处即可全局生效。

### SEO（搜索引擎收录）

- **构建时预渲染**：`prerender.mjs` 用 Vue SSR（`@vue/server-renderer` + `vue-router` 内存历史）为 `/`、`/download`、`/privacy`、`/terms`、`/login`、`/register`、`/membership` 生成完整静态 HTML，避免 SPA 页面无内容导致不被收录。
- **每页独立 title / description / canonical / Open Graph / Twitter Card**：由 `seo.config.js` 的 `PAGES` 表驱动，构建时整块注入。
- **JSON-LD 结构化数据**：`WebSite` + `SearchAction` + `Organization` + `SoftwareApplication`（首页再追加 `FAQPage`），注入在每个页面 `</head>` 之前。
- **robots.txt + sitemap.xml + llms.txt**：均由构建脚本按真源自动生成。
- **OG 图**：`scripts/make-og.mjs` 零依赖生成 1200×630 的 `public/og.png`（当前为占位渐变图）。

### GEO / AEO（AI 对话被引用）

- `llms.txt`：面向 AI 的站点摘要（是什么 / 主要能力 / 典型问题 / 关键页面），让 AI 代理能快速理解并引用站点。
- `FAQPage` 结构化数据 + 首页可见 FAQ 区块：让 AI 在回答「支持哪些平台 / 是否付费 / 有无版权风险」等常见问题时优先引用。
- E-E-A-T 信任页：`/privacy`（隐私政策）、`/terms`（服务条款）、版权声明，以及站点联系方式。

### 真源原则

`frontend/src/seo.config.js`（域名 + 各页文案）、`frontend/src/faq.js`（FAQ 数据 + FAQPage schema）是唯一维护点。修改后重新 `npm run build` 即可让 **页面可见文案、结构化数据、sitemap、llms.txt** 全部保持一致。不要手动改 `prerender.mjs` 里的文案，也不要手工改动 `dist/` 产物。

## 上线前需要修改的检查清单

> ⚠️ 以下都是**部署/上线前必须处理**的占位项，逐个改完，避免上线后才发现。每一项都只是替换占位值，不影响任何现有功能。

### 1. 域名：替换 `SITE_URL`

项目目前用占位域名 `https://example.com`，所有 SEO/GEO 输出（canonical、og:url、sitemap、llms.txt、JSON-LD 里的 URL）都从这里取。

- 文件：`frontend/src/seo.config.js` → `SITE_URL = 'https://example.com'`
- 改成真实域名（含协议，如 `https://yourdomain.com`）
- 改完重新 `cd frontend && npm run build`，让 sitemap.xml / llms.txt / 各页 canonical 一起变
- 之后把 `frontend/dist/` 上传到服务器（见第 5 点部署）

### 2. 联系方式：替换占位邮箱 `support@example.com`

多处硬编码了占位邮箱，需替换为真实客服邮箱：

- `frontend/src/components/Footer.vue`（「联系客服」链接 + 底部「联系我们」行）
- `frontend/src/views/PrivacyView.vue`
- `frontend/src/views/TermsView.vue`

建议在 `seo.config.js` 里增加一个 `CONTACT_EMAIL` 常量，再让这三处引用，避免三处手动改造成不一致。

### 3. 后端生产化：`backend/run.py`

当前为开发参数，生产环境调整：

| 参数 | 当前值 | 生产改为 |
|------|--------|----------|
| `host` | `"127.0.0.1"` | `"0.0.0.0"`（交给反向代理/容器） |
| `port` | `8000` | 按实际端口调整 |
| `reload` | `True` | `False` |
| `log_level` | `"info"` | 按需（`"warning"` 等） |

### 4. 后端 CORS：`backend/app/main.py`

`allow_origins = ["*"]` 目前允许任意来源（开发方便）。生产环境应限制为你的前端域名：

```python
allow_origins=["https://yourdomain.com"]
```

### 5. 部署与 `/download` 路由映射

前端是 SPA + 预渲染出的静态 HTML，部署时需保证：

- 静态资源由 Nginx / CDN 托管 `frontend/dist/`
- `/api/*` 与 `/ws/*` 反向代理到后端（8000 端口）
- **`/download`、`/privacy`、`/terms` 等深链路由**要映射到对应的静态文件（`/download` → `dist/download.html`，`/privacy` → `privacy.html` 等），否则直接访问深链会 404。具体 Nginx `try_files` / 路由映射请参考 [技术方案文档](./docs/architecture.md) 第 8.6 节。

### 6. SSE 流式：确认未启用响应缓冲

`/api/qa` 用 **SSE** 流式逐字返回。后端已加 `X-Accel-Buffering: no` 响应头；若使用 Nginx 反向代理，确认未对其启用 `proxy_buffering`（或已正确透传该头），否则 AI 问答会整个缓冲后再一次性返回，前端「逐字显示」失效。

### 7. 环境变量：`.env`

部署机需自备 `backend/.env`（该文件已被 `.gitignore` 忽略，不入库）：

```env
DEEPSEEK_API_KEY=你的_DeepSeek_Key
COOKIE_FILE=/绝对路径/cookies.txt   # 如需要 B 站登录字幕
# 可选：DEEPSEEK_BASE_URL / DEEPSEEK_MODEL / DEEPSEEK_MAX_CHARS
```

确保 `cookies.txt` 也放在未跟踪目录（见下）并设置了正确权限。

### 8. 凭证保密：`cookies.txt` 与 `.env` 不要入仓

两者都已在 `.gitignore` 中忽略。提交/推送前用 `git status` 确认没有把 `.env`、`cookies.txt`、`*.cookies` 放入版本库。若已误提交过，需清除历史并换用新的登录凭证。

### 9. 搜索平台收录：提交 sitemap

部署完成后，把 `https://yourdomain.com/sitemap.xml` 提交到：

- Google Search Console（提交 sitemap，URL 检查首页）
- Bing Webmaster Tools（可导入 GSC 数据）

同时用 Rich Results Test 校验首页 JSON-LD 是否可被识别（它会渲染 JS，比源码抓取更准）。**SEO/GEO 生效的前提是站点已上线且有索引**。

### 10. Stripe 支付（会员/订阅）

会员功能已可用，含**本地离线 Mock 模式**（`PAYMENT_MOCK=1`，不联网即可跑通全流程）。要接真实收款，需按 **[Stripe 支付接入指南](./docs/stripe支付接入指南.md)** 补齐 Stripe 账号、价格与 webhook，并把关键 env 替换为真实值：

```env
STRIPE_SECRET_KEY=sk_live_xxx        # 上线必换：测试 sk_test_ → 线上 sk_live_
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_ID_MONTHLY=price_xxx     # 月付
STRIPE_PRICE_ID_YEARLY=price_xxx      # 年付
FRONTEND_URL=https://yourdomain.com   # 与 SITE_URL 一致
PAYMENT_MOCK=0                        # 生产必须为 0！
QUOTA_TZ=Asia/Shanghai
FREE_DAILY_DOWNLOADS=3
FREE_DAILY_AI=3
```

> 会员定义：免费用户每天可下载 3 次 + 使用 AI 功能 3 次（下载与 AI 分开计），**不降画质、不阉割 AI 输出**；开通会员后下载与 AI 全部无限。会员状态只由 Stripe webhook 权威写入（验签 + 按 `event.id` 幂等），本地模拟也走同一条验签/幂等管道。

## 注意事项

- 下载的视频文件存放在 `backend/app/downloads/` 目录，1 小时后自动清理
- 请遵守各平台的用户协议和版权法规，仅下载有权限的内容
- 首次使用 yt-dlp 可能较慢，因为它会下载最新的提取器信息
- 预渲染脚本对路由渲染失败会**打印错误但跳过**，不会让 `npm run build` 失败（保留 SPA 产物）。若某个页面预渲染异常，会反映在构建日志和该页 HTML 是否为空上，需留意构建输出。

## 开发计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| 1 | 搭建前端项目骨架 | ✅ |
| 2 | 搭建后端项目骨架 | ✅ |
| 3 | 实现核心下载 API | ✅ |
| 4 | 实现前端下载页面 | ✅ |
| 5 | 布局重构（首页分区 / 样式统一） | ✅ |
| 6 | AI 增值功能（总结、思维导图、AI 问答） | ✅ |
| 7 | 字幕查看与下载（SubtitlePanel） | ✅ |
| 8 | SEO 优化（预渲染 + 结构化数据 + sitemap） | ✅ |
| 9 | GEO 优化（FAQ + llms.txt + 信任页） | ✅ |
| 10 | 会员账号体系（注册/登录/JWT/免费额度） | ✅ |
| 11 | Stripe 订阅支付（checkout/webhook/幂等 + 离线 Mock） | ✅ |
| 12 | 会员前端（登录/注册/会员中心/额度展示） | ✅ |

## 会员与支付

- **账号**：邮箱 + 密码（PBKDF2-SHA256 哈希），JWT 登录态；也支持**匿名使用**（按设备号 `X-Device-Id` 计每日 3 次额度）。
- **免费额度**：每日「下载 3 次」+「AI 功能 3 次」（下载与 AI 分开计），**输出不降级**（不限清晰度、不阉割 AI 结果）；第 4 次返回 `429`，前端提示去开通会员。
- **会员**：下载与 AI 全部无限。会员状态由 Stripe webhook 权威写入，前端只用后端返回展示。
- **支付**：Stripe 订阅，月付 ¥29 / 年付 ¥199。默认 `PAYMENT_MOCK=1` 走本地模拟。

### 离线冒烟测试（PAYMENT_MOCK=1，无外网）

后端已内置一套**不联网**的会员流程测试（用临时 SQLite 库，跑完即删，不污染开发库）：

```bash
cd backend
python test_membership_flow.py
```

覆盖：注册 / 登录 / 取 me → 匿名设备额度 3 次→第 4 次被拒 → 免费用户 HTTP 端点第 4 次 `429` → mock 下单 → mock 驱动 webhook → 会员到账 + 额度变无限 → **重复投递同一 webhook 事件不重复加权益（幂等）** → 过期 / 取消降级回免费。

> 该脚本结尾会清理临时数据库，并输出「通过 N 项，失败 M 项」；失败时退出码非 0，便于 CI 接入。

### 手动离线走查（前端）

`PAYMENT_MOCK=1` 时，在 `/membership` 点「立即开通」，前端会调用 `POST /api/dev/mock-activate` 直接模拟付款成功并授予会员，随后刷新为「会员」状态、额度变为无限——全程无需联网、无需真实 Stripe。

详细对接步骤（注册 Stripe、建两个价格、配 webhook、用测试卡 `4242…` 真实验收、上线 checklist、踩坑）见 **[docs/stripe支付接入指南.md](./docs/stripe支付接入指南.md)**。

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

### 视频总结参数（`backend/app/llm.py` + `.env`）

> 说明：总结 / 思维导图 / AI 问答共用同一个 DeepSeek 客户端，配置集中在 `llm.py`（不再在 `summary.py`）。在根目录 `.env` 配置。

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

### 视频增强功能：总结、思维导图、AI 问答与字幕导出

在视频卡片下方提供能复用同一份字幕的 AI 功能（都在解析出视频后使用）：

| 功能 | 接口 | 说明 |
|------|------|------|
| 视频总结 | `POST /api/summary` | 生成结构化中文总结（一句话概括/内容大纲/知识点/结论） |
| 思维导图 | `POST /api/mindmap` | 生成层级 Markdown，前端用 markmap 渲染成可缩放/折叠的交互式导图 |
| AI 问答 | `POST /api/qa` | 基于字幕多轮问答，SSE 流式逐字输出 |
| 字幕查看/导出 | `POST /api/subtitles` | 查看可用字幕轨道、切换语言，并导出 SRT / VTT / TXT |

字幕通过**进程内内存缓存**按 URL 复用：`summary` / `mindmap` / `qa` / `subtitles` 共享同一个提取结果，第一个功能触发提取后，其余直接复用，不会重复请求平台。缓存有容量上限（默认 50 条），进程重启后清空。

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

### SEO/GEO 真源（`frontend/src/seo.config.js`）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `SITE_URL` | `'https://example.com'` | 站点域名，**上线前必改**（见上方检查清单第 1 项） |
| `OG_IMAGE` | `SITE_URL + '/og.png'` | 分享图地址，由 `make:og` 生成 |
| `PAGES` | 各页 title/description | 每页 meta 文案，修改后需重新 `npm run build` |
| `siteSchema()` | — | 返回 WebSite/Organization/SoftwareApplication 等 JSON-LD |

`frontend/src/faq.js` 提供 `faq`（数据）与 `faqPageSchema()`（结构化数据），是 FAQ 的唯一真源。
