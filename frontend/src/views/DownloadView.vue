<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <!-- Header -->
    <div class="text-center mb-10">
      <h1 class="text-3xl md:text-4xl font-extrabold text-slate-900 mb-3">
        视频<span class="gradient-text">下载</span>
      </h1>
      <p class="text-slate-500">粘贴视频链接，一键解析下载</p>
    </div>

    <!-- Search Bar -->
    <div class="max-w-2xl mx-auto mb-10">
      <div class="flex flex-col sm:flex-row gap-3">
        <div class="flex-1 relative">
          <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            v-model="url"
            type="url"
            placeholder="粘贴视频链接，如 https://www.youtube.com/watch?v=..."
            class="input-primary pl-12"
            @keyup.enter="handleParse"
            :disabled="loading"
          />
        </div>
        <button
          @click="handleParse"
          :disabled="loading || !url.trim()"
          class="btn-primary whitespace-nowrap !py-4 !px-8 flex items-center justify-center gap-2"
        >
          <svg v-if="!loading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <template v-if="loading">解析中...</template>
          <template v-else>解析视频</template>
        </button>
      </div>

      <!-- Error message -->
      <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
        <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-red-700 text-sm">{{ error }}</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="card p-8">
      <LoadingSpinner text="正在解析视频信息..." />
    </div>

    <!-- Video Info Card -->
    <div v-if="videoInfo && !loading" class="card overflow-hidden animate-slide-up">
      <div class="md:flex">
        <!-- Thumbnail -->
        <div class="md:w-80 shrink-0 bg-slate-100">
          <img
            v-if="videoInfo.thumbnail"
            :src="videoInfo.thumbnail"
            :alt="videoInfo.title"
            class="w-full h-48 md:h-full object-cover"
            @error="onThumbnailError"
          />
          <div v-else class="w-full h-48 md:h-full bg-slate-200 flex items-center justify-center">
            <svg class="w-16 h-16 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
        </div>

        <!-- Info -->
        <div class="p-6 flex-1">
          <h2 class="text-lg font-bold text-slate-900 mb-3 line-clamp-2">{{ videoInfo.title }}</h2>
          
          <div class="flex flex-wrap gap-3 text-sm text-slate-500 mb-4">
            <span class="inline-flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ videoInfo.duration || '未知时长' }}
            </span>
            <span class="inline-flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              {{ videoInfo.view_count ? formatCount(videoInfo.view_count) + ' 次播放' : '未知播放量' }}
            </span>
            <span v-if="videoInfo.uploader" class="inline-flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              {{ videoInfo.uploader }}
            </span>
          </div>

          <!-- Formats selection -->
          <div class="mb-4">
            <label class="block text-sm font-semibold text-slate-700 mb-2">选择清晰度</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="fmt in videoInfo.formats"
                :key="fmt.format_id"
                @click="selectedFormat = fmt.format_id"
                :class="[
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 border-2',
                  selectedFormat === fmt.format_id
                    ? 'border-primary-500 bg-primary-50 text-primary-700 shadow-sm'
                    : 'border-slate-200 text-slate-600 hover:border-primary-300 hover:bg-slate-50'
                ]"
              >
                <span class="font-bold">{{ fmt.resolution || fmt.format_note }}</span>
                <span class="ml-2 text-slate-400 text-xs" v-if="fmt.filesize">
                  {{ formatSize(fmt.filesize) }}
                </span>
                <span class="ml-2 text-slate-400 text-xs" v-else-if="fmt.filesize_approx">
                  ~{{ formatSize(fmt.filesize_approx) }}
                </span>
              </button>
            </div>
            <p class="text-xs text-slate-400 mt-2" v-if="videoInfo.note">{{ videoInfo.note }}</p>
          </div>

          <!-- Download button -->
          <button
            @click="handleDownload"
            :disabled="downloading"
            class="btn-cta w-full sm:w-auto"
          >
            <template v-if="downloading">下载中...</template>
            <template v-else>
              <svg class="w-5 h-5 inline-block mr-2 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              下载视频
            </template>
          </button>
        </div>
      </div>
    </div>

    <!-- Supported platforms reminder -->
    <div class="mt-12 text-center">
      <h3 class="text-lg font-bold text-slate-800 mb-3">支持 1000+ 平台</h3>
      <div class="flex flex-wrap justify-center gap-2 max-w-2xl mx-auto">
        <span
          v-for="platform in supportedPlatforms"
          :key="platform"
          class="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-500 font-medium"
        >
          {{ platform }}
        </span>
      </div>
    </div>

    <!-- Download Progress Modal -->
    <DownloadProgressModal
      :visible="showProgressModal"
      :status="downloadStatus"
      :progress="downloadProgress"
      :speed="downloadSpeed"
      :filename="downloadFilename"
      :download-url="downloadFileUrl"
      :error-message="downloadError"
      :status-text="downloadStatusText"
      @close="handleModalClose"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { parseVideo, startDownload, getDownloadUrl, createDownloadSocket } from '../utils/api'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import DownloadProgressModal from '../components/DownloadProgressModal.vue'

const route = useRoute()

const url = ref('')
const loading = ref(false)
const downloading = ref(false)
const error = ref('')
const videoInfo = ref(null)
const selectedFormat = ref('')
const thumbnailError = ref(false)

// Progress modal
const showProgressModal = ref(false)
const downloadStatus = ref('downloading')
const downloadProgress = ref(0)
const downloadSpeed = ref('')
const downloadFilename = ref('')
const downloadFileUrl = ref('')
const downloadError = ref('')
const downloadStatusText = ref('')

const supportedPlatforms = [
  'YouTube', 'YouTube Shorts', 'Bilibili', 'TikTok', '抖音',
  'Instagram', 'Twitter/X', 'Facebook', 'Vimeo', 'Dailymotion',
  'Twitch', 'PornHub', 'xvideos', 'Youku', 'iQiyi',
  '网易云音乐', 'SoundCloud', 'Spotify', 'BBC', 'CNN',
  // ... more
]

function formatCount(count) {
  if (!count) return ''
  const n = parseInt(count)
  if (n >= 10000 && n < 100000000) return (n / 10000).toFixed(1) + '万'
  if (n >= 100000000) return (n / 100000000).toFixed(1) + '亿'
  return n.toLocaleString()
}

function formatSize(bytes) {
  if (!bytes) return ''
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return size.toFixed(1) + ' ' + units[i]
}

function onThumbnailError() {
  thumbnailError.value = true
}

async function handleParse() {
  if (!url.value.trim() || loading.value) return

  error.value = ''
  videoInfo.value = null
  loading.value = true

  try {
    const result = await parseVideo(url.value.trim())
    if (result.success && result.data) {
      videoInfo.value = result.data
      // Auto-select best format
      if (result.data.formats && result.data.formats.length > 0) {
        selectedFormat.value = result.data.formats[result.data.formats.length - 1].format_id
      }
    } else {
      error.value = result.message || '无法解析该视频，请检查链接是否正确。'
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '请求失败，请检查网络或稍后重试。'
  } finally {
    loading.value = false
  }
}

async function handleDownload() {
  if (!url.value.trim() || downloading.value) return

  downloading.value = true
  downloadError.value = ''

  try {
    const result = await startDownload(url.value.trim(), selectedFormat.value)
    if (result.success && result.task_id) {
      // Show progress modal
      showProgressModal.value = true
      downloadStatus.value = 'downloading'
      downloadProgress.value = 0
      downloadSpeed.value = ''
      downloadStatusText.value = '正在连接服务器...'

      // Connect WebSocket for progress
      connectProgressSocket(result.task_id)
    } else {
      throw new Error(result.message || '启动下载失败')
    }
  } catch (err) {
    showProgressModal.value = true
    downloadStatus.value = 'error'
    downloadError.value = err.response?.data?.detail || err.message || '下载失败'
    downloading.value = false
  }
}

function connectProgressSocket(taskId) {
  try {
    const socket = createDownloadSocket(taskId)

    socket.onopen = () => {
      downloadStatusText.value = '连接成功，开始下载...'
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'progress') {
          downloadProgress.value = Math.min(Math.round(data.progress || 0), 99)
          downloadSpeed.value = data.speed || ''
          downloadStatusText.value = data.status || '正在下载...'
        } else if (data.type === 'complete') {
          downloadStatus.value = 'completed'
          downloadProgress.value = 100
          downloadFilename.value = data.filename || 'video.mp4'
          downloadFileUrl.value = getDownloadUrl(taskId)
          downloading.value = false
          socket.close()
        } else if (data.type === 'error') {
          downloadStatus.value = 'error'
          downloadError.value = data.message || '下载出错'
          downloading.value = false
          socket.close()
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    socket.onerror = () => {
      // If WebSocket fails, fallback to polling or just wait
      setTimeout(() => {
        // Try to get the file after a delay
        downloadStatus.value = 'completed'
        downloadProgress.value = 100
        downloadFilename.value = 'video.mp4'
        downloadFileUrl.value = getDownloadUrl(taskId)
        downloading.value = false
      }, 5000)
    }

    socket.onclose = () => {
      if (downloadStatus.value === 'downloading') {
        // Connection lost while downloading
        setTimeout(() => {
          if (downloadStatus.value === 'downloading') {
            downloadStatus.value = 'completed'
            downloadFileUrl.value = getDownloadUrl(taskId)
            downloading.value = false
          }
        }, 3000)
      }
    }
  } catch (e) {
    // WebSocket fallback - after timeout, assume success
    setTimeout(() => {
      downloadStatus.value = 'completed'
      downloadProgress.value = 100
      downloadFilename.value = 'video.mp4'
      downloadFileUrl.value = getDownloadUrl(taskId)
      downloading.value = false
    }, 8000)
  }
}

function handleModalClose() {
  showProgressModal.value = false
  downloading.value = false
}

// Pre-fill URL from query parameter
onMounted(() => {
  if (route.query.url) {
    url.value = route.query.url
    handleParse()
  }
})
</script>