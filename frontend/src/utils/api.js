import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
      headers: { 'Content-Type': 'application/json' },
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
export function createDownloadSocket(taskId) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/${taskId}`
  return new WebSocket(wsUrl)
}

export default api