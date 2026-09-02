# Stripe 支付接入指南（写给零基础的你）

> 目标：让「万能视频下载器」能真正卖会员。本文从**注册 Stripe、建价格、配 webhook、本地/线上测试、上线**一步步讲清，并专门说明**没有外网时怎么测**、**内地主体怎么处理**。
> 已确认参数：月付 **¥29**、年付 **¥199**（≈¥16.6/月），Stripe 订阅模式，**测试 mode 用 `4242 4242 4242 4242` 测试卡**。

---

## 0. 先看结论：现在就能交付（不需要先有 Stripe 账号）

代码已把支付做成**双通道**，由 `.env` 里的 `PAYMENT_MOCK` 控制：

| 模式 | `PAYMENT_MOCK` | 是否联网 | 用途 |
|------|----|------|------|
| 本地模拟 | `1` | **不联网** | 开发 / 自测 / 验收，跑通全链路 |
| 真实 Stripe | `0` | 联网 | 生产收款（需要 Stripe 账号 + 价格 + webhook） |

**即使你此刻什么都没有，也能 `PAYMENT_MOCK=1` 把「注册 → 下单 → 付款 → 会员到账 → 额度变无限」整条链路在本地演示一遍。** 等你解决主体、注册好 Stripe 后，再切 `0` 接真钱。

---

## 1. 核心认知（先懂这 3 件事，不然容易卡）

1. **Stripe 是云端支付平台**，付款发生在 Stripe 的服务器上。所以**一分钱不联网，就无法真的到 Stripe 完成一笔支付**。这就是为什么要有上面的「本地模拟」——它把「付款成功」这一步在本地假冒出来，其余（订单、库存、会员授予）都是真的。
2. **会员状态唯一可信来源是 Stripe 的 webhook**（不是前端，也不是我们手动改库）。我们收 webhook → 验签 → 幂等去重 → 写入 `memberships` 表 → 会员生效。本地模拟也复用了这条**同一条** webhook 处理管道（本地生成带签名的假事件），所以模拟和真实验收走的是**同一份后端逻辑**，模拟通过基本等于真实能通过。
3. **内地企业主体在 Stripe 直接收款受限**（见第 2 节）。这是你真正要提前想清楚的事；想不清楚就先用 Mock 把功能做完。

---

## 2. 收款主体问题（最重要，先想清楚）

Stripe **不直接支持中国大陆企业主体**直接签约收款。常见可行路线（选一条）：

| 方案 | 说明 |
|------|------|
| ① 香港 / 美国 / 新加坡 / 澳门等主体 | 注册一个这些地区的公司/个体户（或已有），用其开 Stripe 账户。最主流。 |
| ② 与 Stripe 合作的收单服务商 | 走第三方跨境收单，你专注业务，他们处理合规与结算。 |
| ③ 香港版 Stripe | 专门面向香港主体；若你有香港实体，这是最顺的选择。 |
| ④ 暂不开收款 | 先用 Mock + 测试 key 把功能、UI、验收全部做完，主体落实后再接真。**第 0 节让这成为可行选项。** |

> **建议**：不管选哪条，都先 `PAYMENT_MOCK=1` 把功能跑通；主体一落实，随时可以切真。不要因为主体没定就阻塞开发。

---

## 3. 注册 Stripe 账号并拿测试密钥

1. 打开 https://dashboard.stripe.com/register ，选择主体地区与账户类型（个人/公司），填基本资料注册。
2. 登录后，页面右上角切到 **`Test mode`（测试模式）**。
3. 进入 **Developers → API keys**：
   - 复制 **`Secret key`**（`sk_test_...`，测试模式是 `sk_test_` 开头）→ 填到 `.env` 的 `STRIPE_SECRET_KEY`。
   - `Publishable key`（`pk_test_...`）前端展示用，本项目后端下单，一般用不到，可留空。

> ⚠️ **千万别用线上 `sk_live_` 来测试**，`sk_live_` 会真实扣款。测试模式绝不动真钱。

---

## 4. 创建两个「产品/价格」（月付 + 年付）

Stripe 是先有 **Product（产品）** 再有 **Price（价格）**；价格分**一次性**和**周期性 recurring**。我们订阅需要 recurring。

1. 在测试模式下，进入 **Product catalog → Add product**。
2. 方式一（推荐，一个产品一个价格，或一个产品两个价格都行）：
   - 建两个 Product：`会员-月付`、`会员-年付`（或只建一个 `会员`，然后在价格里建两个）。
   - 每个 Product 下 **Add pricing / 新建 Price**：
     - **月付**：金额 `29`，币种按第 4.1 节选，**Billing period** = `Monthly`（每月）。
     - **年付**：金额 `199`，币种同前，**Billing period** = `Yearly`（每年）。
3. 建好后每个 Price 右侧会有一个 **`price_...`** 开头的 ID，把它复制到 `.env`：
   - `STRIPE_PRICE_ID_MONTHLY=price_xxx`
   - `STRIPE_PRICE_ID_YEARLY=price_xxx`

> 你现在看到的是 UI；真正触发「每月扣一次」靠的是 Stripe 在后台按 period 自动扣款，无需我们写定时任务。

### 4.1 币种怎么选（重要）

- 若你的 Stripe 账户主体结算货币是 **人民币（CNY）**，可直接建 `29 CNY` / `199 CNY`。
- 若主体不在 CNY 结算区，**Stripe 可能限制或需要资质才能用 CNY**。**稳妥做法：先用美元/主体支持的主流币种建价**（比如 `29 USD` / `199 USD`），等主体与结算币种确认后再调。价格只是数字，后端从 `.env` 读，**改价格不用动任何代码**。
- 代码对此无假设（不做币种强校验），所以先填能通过的币种即可。

---

## 5. 配置 webhook（会员生效的关键）

webhook 是 Stripe 在「付款成功 / 订阅变更」时**主动回调**我们的接口，我们据此授予或不授予会员。有两种配法：**本地测试（CLI）** 与 **线上（Dashboard）**。

### 5.1 本地测试：用 Stripe CLI 转发（配合 `stripe listen`）

你机器已装 **Stripe CLI 1.50.8**（`stripe --version` 可确认），正好够用。

1. 登录 CLI：`stripe login`，按提示打开浏览器授权。
2. 启动本地转发，把 Stripe 事件转发到后端 webhook 地址：
   ```bash
   stripe listen --forward-to http://127.0.0.1:8000/api/payments/webhook
   ```
   终端会打印一行：
   ```
   ⚡ Webhook signing secret: whsec_XXXXXXXXXXXXXXXX
   ```
   把 `whsec_...` 复制到 `.env` 的 `STRIPE_WEBHOOK_SECRET`。
3. 保持这个 `stripe listen` 进程开着（它同时充当「把 Stripe 事件转发到本地」的桥梁）。

> `whsec_` 每次 `stripe listen` 打印，重启 CLI 一般保持一致，但**务必每次都核对**并写进 `.env`。

### 5.2 线上（生产）：Dashboard → Developers → Webhooks

1. Add endpoint → URL 填 `https://yourdomain.com/api/payments/webhook`（你的后端公网地址）。
2. 订阅这些事件：
   - `checkout.session.completed`
   - `customer.subscription.created` / `customer.subscription.updated` / `customer.subscription.deleted`
   - `invoice.paid` / `invoice.payment_failed`
3. 创建后回到 Webhooks → Endpoint → `Signing secret` → 复制 `whsec_...` → 填到 `.env` 的 `STRIPE_WEBHOOK_SECRET`。

### 5.3 事件说明（后端已处理）

| 事件 | 后端动作 |
|------|---------|
| `checkout.session.completed` | 立即授予会员（下单成功即生效） |
| `customer.subscription.created / updated` | 写入/更新订阅状态、到期时间、plan |
| `customer.subscription.deleted` | 标记取消（降级回免费） |
| `invoice.paid` | 续费成功确认 |
| `invoice.payment_failed` | 标记 `past_due`（未付款 → 降级） |

---

## 6. 本地（离线）验收：`PAYMENT_MOCK=1`

**不需要 Stripe 账号、不需要联网。** 后端已内置一套自动测试：

```bash
cd backend
python test_membership_flow.py
```

会验证：注册/登录 → 匿名与免费用户 3 次额度、第 4 次 `429` → mock 下单 → mock 驱动 webhook → **会员到账 + 额度变无限** → **重复投递同一事件不重复加权益（幂等）** → 过期/取消降级。全部离线，跑完删临时库。

手动走查（前端）：

```bash
# 终端 1：后端
cd backend && python run.py
# 终端 2：前端
cd frontend && npm run dev
```

打开 `http://localhost:5173/membership`，注册/登录 → 选月付或年付 → 点「立即开通」。因为 `PAYMENT_MOCK=1`，前端会直接调用 `POST /api/dev/mock-activate` 模拟付款成功，随后页面刷新成「会员」、下载页额度显示「无限」。

> 这就叫**离线验收全链路**：下单、会员授予、额度变化全部真实，只有「Stripe 服务器扣款」这一步是假的。

---

## 7. 线上（联网）真实验收：测试卡 + `stripe listen`

1. 确认 `.env`：
   ```env
   PAYMENT_MOCK=0
   STRIPE_SECRET_KEY=sk_test_xxx
   STRIPE_WEBHOOK_SECRET=whsec_xxx   # 来自 stripe listen
   STRIPE_PRICE_ID_MONTHLY=price_xxx
   STRIPE_PRICE_ID_YEARLY=price_xxx
   FRONTEND_URL=http://localhost:5173
   ```
2. 启动后端（8000）、前端（5173）、`stripe listen --forward-to http://127.0.0.1:8000/api/payments/webhook`。
3. 到 `/membership`，选月付点「立即开通」→ 会跳转到 Stripe **托管 Checkout 页**（真实验收时 `PAYMENT_MOCK=0`，后端返回 Stripe URL）。
4. 在 Checkout 用测试卡：
   - 卡号：`4242 4242 4242 4242`
   - 有效日期：任意未来日期（如 `12/34`）
   - CVC：任意 3 位（如 `123`）
   - 姓名、邮箱：任意
5. 完成后 Stripe 会回调 `/api/payments/webhook`（经 `stripe listen` 转发），后端日志应打印已处理 `checkout.session.completed`，随后 `/api/auth/me` 返回 `is_member: true`、额度 `unlimited: true`。
6. 想测**续费/取消**：可在 Stripe Dashboard 该订阅上操作「取消」，`customer.subscription.deleted` 事件会触发降级。

---

## 8. 上线（切真实收款）

1. `.env` 改为线上值：
   ```env
   STRIPE_SECRET_KEY=sk_live_xxx     # 线上密钥
   STRIPE_WEBHOOK_SECRET=whsec_xxx   # 线上 endpoint 的 secret（Dashboard 配）
   FRONTEND_URL=https://yourdomain.com
   SITE_URL=https://yourdomain.com   # 前端 seo.config.js
   PAYMENT_MOCK=0                    # 必须为 0，否则是不扣款假支付！
   JWT_SECRET=<强随机 32+ 位字符串>  # 别再是 yupi_test
   ```
2. 确保 Stripe 账户已 **激活上线**（Test mode 切到 Live，且已完成开户流程）。
3. 在 Dashboard（Live）重复第 4、5.2 节的「建价格 + 配 webhook」步骤（价格 ID 与测试模式的不同）。
4. `cd frontend && npm run build` 重新生成产物，部署 `frontend/dist/` 与后端（见 README「上线前检查清单」）。
5. 用真实小额（如 ¥1 或调到可接受金额）自我秒退 / 秒退一笔验证端到端，再正式开放。

---

## 9. 会遇到的坑（提前告诉你）

| 坑 | 现象 | 处理 |
|----|------|------|
| 没配 webhook secret | 后端收到事件但验签失败 `400` | `.env` 填 `STRIPE_WEBHOOK_SECRET`（来自 `stripe listen` / Dashboard），重启后端 |
| `stripe trigger` 造事件失败 | 提示找不到 object | 最快用 `stripe trigger customer.subscription.created`；或人工在 Dashboard 用测试卡真付一笔产生真实事件 |
| 测试模式不扣款 | 很正常 | 用 `4242...` 卡，任何未来日期 + 任意 CVC |
| 用错密钥 | 扣真钱 / 连不上 | 测试用 `sk_test_`，线上用 `sk_live_`；两者分开建价、分开配 webhook |
| 会员没生效 | 付了但 `me` 仍是免费 | 多半是 webhook 没到：确认 `stripe listen` 开着、URL 一致、事件已订阅；看后端日志 |
| 用户重复付款 | — | 后端按 `event.id` 幂等 + checkout `idempotency_key`，重复事件不会重复加权益 |
| 只处理 `checkout.session.completed` | 续费/取消状态失准 | 必须订阅并处理 `customer.subscription.*` 与 `invoice.*`（后端已做） |
| 内地主体限制 | 开通/收款受限 | 见第 2 节，先主体后接真 |

---

## 10. 敏感信息安全

- `.env`（含 `sk_live_*`、`whsec_*`、`JWT_SECRET`）**绝不提交仓库**；项目 `.gitignore` 已忽略。提交/推送前 `git status` 检查。
- `sk_live_*` 一旦泄露可真实扣款，只应存在于**服务端**，前端/浏览器/公网仓库都不能出现。
- 测试模式的 `sk_test_` 无真实资金风险，但同样别提交。
- 会员校验只在**后端**判断（`gating.py`），前端禁用按钮只是提示、不构成安全边界。

---

## 11. 一句话流程图

```
用户点订阅 ─▶ 后端 create Checkout ─▶ Stripe Checkout 页
                                          │ 用户用测试卡付款
                                          ▼
                      Stripe 发 webhook（checkout.session.completed / subscription.*）
                                          │ 经 stripe listen / Dashboard 转发
                                          ▼
                      后端验签 + 幂等 + 写 memberships 表 ─▶ 会员生效
                                          │
                      前端 /api/auth/me ─▶ is_member=true, 额度无限
```

---

## 12. 可复用脚本

- `backend/test_membership_flow.py`：离线全流程（Mock）冒烟测试。
- `stripe listen --forward-to http://127.0.0.1:8000/api/payments/webhook`：本地把真实 Stripe 事件转发到本地后端。
- 测试卡：`4242 4242 4242 4242` / 任意未来日期 / 任意 CVC。
