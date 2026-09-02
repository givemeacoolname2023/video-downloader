import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── 会员/账号：localStorage 存 token + 匿名设备号，自动注入每个请求 ──────────
// 只在浏览器读写 localStorage（SSR/预渲染没有 window，统一走守卫函数）。
const TOKEN_KEY = 'vd_token'
const USER_KEY = 'vd_user'
const DEVICE_KEY = 'vd_device_id'

function ssLocalStorage() {
  return typeof window === 'undefined' ? null : window.localStorage
}

function genDeviceId() {
  try {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID().replace(/-/g, '')
    }
  } catch (e) {
    /* ignore */
  }
  return 'dev_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10)
}

/** 确保存在一个匿名设备号并返回（无 window 时返回空串）。 */
export function ensureDeviceId() {
  const ls = ssLocalStorage()
  if (!ls) return ''
  let id = ls.getItem(DEVICE_KEY)
  if (!id) {
    id = genDeviceId()
    ls.setItem(DEVICE_KEY, id)
  }
  return id
}

function getToken() {
  const ls = ssLocalStorage()
  return ls ? ls.getItem(TOKEN_KEY) : null
}

/** 给原生 fetch 请求（SSE 等）补上 Authorization / X-Device-Id。 */
export function buildAuthHeaders(extra = {}) {
  const headers = { ...extra }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const device = ensureDeviceId()
  if (device) headers['X-Device-Id'] = device
  return headers
}

// axios 拦截器：请求注入鉴权头；401 时清除过期登录态（不影响匿名用户）。
api.interceptors.request.use((cfg) => {
  const token = getToken()
  if (token) cfg.headers['Authorization'] = `Bearer ${token}`
  const device = ensureDeviceId()
  if (device) cfg.headers['X-Device-Id'] = device
  return cfg
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && ssLocalStorage()?.getItem(TOKEN_KEY)) {
      ssLocalStorage().removeItem(TOKEN_KEY)
      ssLocalStorage().removeItem(USER_KEY)
    }
    return Promise.reject(err)
  }
)

/**
 * 解析视频 URL，获取视频信息
 * @param {string} url - 视频链接
 * @returns {Promise<{success: boolean, data: object}>}
 */
export async function parseVideo(url) {
  const { data } = await api.post('/parse', { url })
  return data
}

/**
 * 开始下载视频
 * @param {string} url - 视频链接
 * @param {string} formatId - 清晰度格式 ID
 * @returns {Promise<{success: boolean, task_id: string}>}
 */
export async function startDownload(url, formatId) {
  const { data } = await api.post('/download', { url, format_id: formatId })
  return data
}

/**
 * 生成视频 AI 摘要
 * @param {string} url - 视频链接
 * @returns {Promise<{success: boolean, message: string, data: object}>}
 */
export async function generateSummary(url) {
  const { data } = await api.post('/summary', { url }, { timeout: 120000 })
  return data
}

/**
 * 生成视频思维导图（层级 Markdown）
 * @param {string} url - 视频链接
 * @returns {Promise<{success: boolean, message: string, data: object}>}
 */
export async function generateMindmap(url) {
  const { data } = await api.post('/mindmap', { url }, { timeout: 120000 })
  return data
}

/**
 * 获取视频字幕列表（带时间戳）。复用与总结/导图相同的缓存字幕，不重复提取。
 * @param {string} url - 视频链接
 * @returns {Promise<{success: boolean, message: string, data: {title, lang, segments}}>}
 */
export async function getSubtitles(url) {
  const { data } = await api.post('/subtitles', { url }, { timeout: 120000 })
  return data
}

/**
 * 读取 POST SSE 流（data: {json} 事件，以空行分隔）。统一解析事件（text/error/done）并按回调分发。
 * @param {Response} res - fetch 返回的 stream 响应
 * @param {{onText: Function, onError: Function, onDone: Function}} handlers
 */
async function _readSse(res, { onText, onError, onDone } = {}) {
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let finished = false

  const finish = () => {
    if (finished) return
    finished = true
    onDone?.()
  }

  const handleEvent = (data) => {
    if (!data) return
    let json
    try {
      json = JSON.parse(data)
    } catch (e) {
      return
    }
    if (json.error) {
      onError?.(json.error)
      finish()
    } else if (json.text) {
      onText?.(json.text)
    }
    if (json.done) finish()
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      // SSE events are separated by a blank line.
      const parts = buffer.split('\n\n')
      buffer = parts.pop()
      for (const part of parts) {
        for (const line of part.split('\n')) {
          if (!line.startsWith('data:')) continue
          handleEvent(line.slice(5).trim())
        }
      }
    }
    if (buffer.trim()) {
      for (const line of buffer.split('\n')) {
        if (!line.startsWith('data:')) continue
        handleEvent(line.slice(5).trim())
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') onError?.(e.message || '流式请求中断。')
    return
  }
  finish()
}

/**
 * 发出一个 POST SSE 请求并解析响应。
 * @param {string} path - 接口路径（如 '/api/qa'）
 * @param {object} payload - JSON 请求体
 * @param {{onText: Function, onError: Function, onDone: Function, signal: AbortSignal, errorText: string}} handlers
 */
async function _postSse(path, payload, { onText, onError, onDone, signal, errorText = '请求失败，请稍后重试。' }) {
  let res
  try {
    res = await fetch(path, {
      method: 'POST',
      headers: buildAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
      signal,
    })
  } catch (e) {
    if (e.name !== 'AbortError') onError?.(e.message || `网络异常，${errorText}`)
    return
  }

  if (!res.ok || !res.body) {
    let detail = errorText
    try {
      const j = await res.json()
      detail = j.detail || j.message || detail
    } catch (e) {
      /* ignore parse errors */
    }
    onError?.(detail)
    return
  }

  await _readSse(res, { onText, onError, onDone })
}

/**
 * 流式 AI 问答（SSE）。逐字回调文本增量。
 * @param {{url: string, question: string, history: Array}} payload
 * @param {{onText: Function, onError: Function, onDone: Function, signal: AbortSignal}} handlers
 */
export async function streamQa(payload, handlers) {
  await _postSse('/api/qa', payload, { ...handlers, errorText: '问答失败，请稍后重试。' })
}

/**
 * 流式生成视频 AI 总结（SSE）。逐字回调文本增量，前端可实时渲染 Markdown。
 * @param {{url: string}} payload
 * @param {{onText: Function, onError: Function, onDone: Function, signal: AbortSignal}} handlers
 */
export async function streamSummary(payload, handlers) {
  await _postSse('/api/summary', payload, { ...handlers, errorText: '生成总结失败，请稍后重试。' })
}

/**
 * 获取下载文件（触发浏览器下载）
 * @param {string} taskId - 任务 ID
 */
export function getDownloadUrl(taskId) {
  return `/api/download-file/${taskId}`
}

/**
 * 创建 WebSocket 连接监听下载进度
 * @param {string} taskId - 任务 ID
 * @returns {WebSocket}
 */
export async function register(credentials) {
  const { data } = await api.post('/auth/register', credentials)
  return data // { token, user }
}

export async function login(credentials) {
  const { data } = await api.post('/auth/login', credentials)
  return data // { token, user }
}

export async function fetchMe() {
  const { data } = await api.get('/auth/me')
  return data // { user, is_member, membership, quota }
}

export async function fetchQuota() {
  const { data } = await api.get('/quota')
  return data
}

/** 创建 Stripe 下单（订阅）。mock 模式返回本地下单结果，真实模式返回跳转 URL。 */
export async function createCheckout(plan) {
  const { data } = await api.post('/payments/checkout', { plan })
  return data // { url, session_id, mock }
}

/** mock 模式专用：模拟付款成功，授予会员。 */
export async function mockActivate(plan) {
  const { data } = await api.post('/dev/mock-activate', { plan })
  return data // /auth/me 形状
}
export function createDownloadSocket(taskId) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/${taskId}`
  return new WebSocket(wsUrl)
}

export default api