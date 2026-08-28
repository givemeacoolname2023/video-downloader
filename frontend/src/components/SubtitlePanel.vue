<template>
  <div class="card p-6">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-5">
      <div class="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center shrink-0">
        <svg class="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3.75 7.5h16.5M3.75 12h16.5m-16.5 4.5h16.5m-16.5 4.5h16.5" />
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold text-slate-900">字幕列表</h3>
        <p class="text-xs text-slate-400">逐句查看带时间点的字幕，支持导出 SRT / VTT / TXT</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-4">
      <LoadingSpinner text="正在提取字幕..." />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
      <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div class="flex-1">
        <p class="text-red-700 text-sm">{{ error }}</p>
        <button @click="load" class="mt-3 text-sm font-medium text-primary-600 hover:text-primary-700">
          重试
        </button>
      </div>
    </div>

    <!-- Result -->
    <div v-else-if="loaded">
      <!-- Meta row: title + lang + count + tools -->
      <div class="flex flex-wrap items-center gap-3 mb-4">
        <span class="text-sm font-semibold text-slate-700">{{ title || '视频字幕' }}</span>
        <span v-if="lang" class="px-2 py-0.5 rounded bg-slate-100 text-xs text-slate-500">{{ lang }}</span>
        <span class="text-xs text-slate-400">{{ filteredSegments.length }} / {{ segments.length }} 条</span>

        <!-- Download dropdown: SRT / VTT / TXT -->
        <div class="relative ml-auto">
          <button
            @click="downloadOpen = !downloadOpen"
            class="text-sm text-slate-500 hover:text-slate-700 font-medium flex items-center gap-1"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            下载字幕
          </button>
          <div
            v-if="downloadOpen"
            class="absolute z-10 mt-2 right-0 w-44 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden"
          >
            <button
              @click="downloadSrt"
              class="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
            >SRT 字幕（带时间）</button>
            <button
              @click="downloadVtt"
              class="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 border-t border-slate-100"
            >VTT 字幕（WebVTT）</button>
            <button
              @click="downloadTxt"
              class="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 border-t border-slate-100"
            >TXT 纯文本</button>
          </div>
        </div>
      </div>

      <!-- Search filter -->
      <div class="relative mb-4">
        <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
          <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <input
          v-model="query"
          type="text"
          placeholder="搜索字幕内容..."
          class="input-primary pl-9"
        />
      </div>

      <!-- Subtitle list -->
      <div class="max-h-96 overflow-y-auto rounded-xl border border-slate-100 divide-y divide-slate-50">
        <div
          v-for="(seg, i) in filteredSegments"
          :key="i"
          class="flex items-start gap-3 px-4 py-2.5 hover:bg-slate-50"
        >
          <span class="shrink-0 text-xs font-mono text-slate-400 tabular-nums leading-6 w-16">
            {{ fmtTime(seg.start) }}
          </span>
          <span class="flex-1 text-sm text-slate-700 leading-6">{{ seg.text }}</span>
        </div>
      </div>

      <p v-if="downloadMsg" class="mt-3 text-xs text-slate-400">{{ downloadMsg }}</p>
    </div>

    <!-- Idle -->
    <div v-else class="py-6 text-center">
      <p class="text-sm text-slate-400 mb-4">
        解析出视频后，可查看带时间点的字幕，并导出为常见格式。
      </p>
      <button @click="load" :disabled="!url" class="btn-cta text-sm !py-3 !px-8">
        <svg class="w-5 h-5 inline-block mr-2 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        查看字幕列表
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getSubtitles } from '../utils/api'
import LoadingSpinner from './LoadingSpinner.vue'

const props = defineProps({
  url: { type: String, default: '' },
})

const segments = ref([])
const title = ref('')
const lang = ref('')
const loading = ref(false)
const error = ref('')
const loaded = ref(false)
const query = ref('')
const downloadOpen = ref(false)
const downloadMsg = ref('')

const filteredSegments = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return segments.value
  return segments.value.filter((s) => s.text && s.text.toLowerCase().includes(q))
})

const p2 = (n) => String(n).padStart(2, '0')

// Display "MM:SS" or "HH:MM:SS" from a seconds value.
function fmtTime(sec) {
  if (sec == null || isNaN(sec)) return '--:--'
  sec = Math.max(0, Math.floor(sec))
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  if (h > 0) return `${p2(h)}:${p2(m)}:${p2(s)}`
  return `${p2(m)}:${p2(s)}`
}

// Subtitle-file timestamp helper: HH:MM:SS,mmm (SRT) / HH:MM:SS.mmm (VTT).
function stime(sec, colon) {
  if (sec == null || isNaN(sec)) sec = 0
  sec = Math.max(0, sec)
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = Math.floor(sec % 60)
  let ms = Math.round((sec % 1) * 1000)
  if (ms === 1000) ms = 999
  const sep = colon ? ',' : '.'
  return `${p2(h)}:${p2(m)}:${p2(s)}${sep}${String(ms).padStart(3, '0')}`
}

function toSrt() {
  const list = segments.value.filter((s) => s.start != null)
  return list
    .map((s, i) => {
      const end = i + 1 < list.length ? list[i + 1].start : s.start + 2
      return `${i + 1}\n${stime(s.start, true)} --> ${stime(end, true)}\n${s.text}\n`
    })
    .join('\n')
}

function toVtt() {
  const list = segments.value.filter((s) => s.start != null)
  const body = list
    .map((s, i) => {
      const end = i + 1 < list.length ? list[i + 1].start : s.start + 2
      return `${stime(s.start, false)} --> ${stime(end, false)}\n${s.text}`
    })
    .join('\n')
  return `WEBVTT\n\n${body}\n`
}

function toTxt() {
  return segments.value.map((s) => s.text).join('\n')
}

function safeFilename() {
  const base = (title.value || '视频')
    .replace(/[\\/:*?"<>|]/g, '_')
    .trim()
  return base ? `字幕_${base}` : '字幕'
}

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function download(ext, mime, content) {
  saveBlob(new Blob([content], { type: mime }), `${safeFilename()}.${ext}`)
  downloadMsg.value = `已下载 ${ext.toUpperCase()} 字幕`
  downloadOpen.value = false
  setTimeout(() => (downloadMsg.value = ''), 3000)
}

function downloadSrt() {
  download('srt', 'text/plain;charset=utf-8', toSrt())
}
function downloadVtt() {
  download('vtt', 'text/vtt;charset=utf-8', toVtt())
}
function downloadTxt() {
  download('txt', 'text/plain;charset=utf-8', toTxt())
}

async function load() {
  if (loading.value || !props.url.trim()) return
  loading.value = true
  error.value = ''
  loaded.value = false
  downloadMsg.value = ''

  try {
    const result = await getSubtitles(props.url.trim())
    if (result.success && result.data?.segments?.length) {
      segments.value = result.data.segments
      title.value = result.data.title || ''
      lang.value = result.data.lang || ''
      loaded.value = true
    } else {
      error.value = result.message || '该视频暂无可用的字幕，无法加载列表。'
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || '获取字幕失败，请检查网络后重试。'
  } finally {
    loading.value = false
  }
}

// Reset when a new video URL is set. Keep already-loaded subtitles until then.
watch(
  () => props.url,
  () => {
    segments.value = []
    title.value = ''
    lang.value = ''
    loaded.value = false
    error.value = ''
    query.value = ''
    downloadOpen.value = false
    downloadMsg.value = ''
  }
)
</script>
