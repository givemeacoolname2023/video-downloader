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