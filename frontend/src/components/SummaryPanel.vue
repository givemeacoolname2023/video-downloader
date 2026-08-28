<template>
  <div>
    <!-- Header -->
    <div class="flex items-center gap-3 mb-5">
      <div class="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center shrink-0">
        <svg class="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z" />
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold text-slate-900">AI 视频总结</h3>
        <p class="text-xs text-slate-400">基于字幕快速了解视频大纲与核心要点</p>
      </div>
    </div>

    <!-- Loading (only before any text has started arriving) -->
    <div v-if="loading && !summary" class="py-4">
      <LoadingSpinner text="AI 正在阅读字幕并生成总结，请稍候..." />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
      <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div class="flex-1">
        <p class="text-red-700 text-sm">{{ error }}</p>
        <button @click="generate" class="mt-3 text-sm font-medium text-primary-600 hover:text-primary-700">
          重试
        </button>
      </div>
    </div>

    <!-- Result -->
    <div v-else-if="summary">
      <div class="space-y-4 text-slate-700 text-[15px] leading-relaxed">
        <template v-for="(block, idx) in blocks" :key="idx">
          <h4 v-if="block.type === 'h2'" class="text-base font-bold text-slate-900 mt-3 first:mt-0">
            <InlineText :text="block.text" />
          </h4>
          <h5 v-else-if="block.type === 'h3'" class="text-sm font-bold text-slate-900 mt-2">
            <InlineText :text="block.text" />
          </h5>
          <ul v-else-if="block.type === 'ul'" class="space-y-2">
            <li
              v-for="(item, i) in block.items"
              :key="i"
              class="flex items-start gap-2"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-primary-400 mt-2 shrink-0"></span>
              <span class="flex-1"><InlineText :text="item" /></span>
            </li>
          </ul>
          <p v-else class="text-slate-600"><InlineText :text="block.text" /></p>
        </template>
      </div>

      <!-- Streaming indicator -->
      <p v-if="loading" class="mt-4 flex items-center gap-2 text-xs text-slate-400">
        <span class="w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse"></span>
        正在生成…
      </p>

      <!-- Actions -->
      <div class="mt-6 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-3">
        <button
          @click="copySummary"
          class="btn-primary text-sm !py-2.5 !px-5 flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
          </svg>
          {{ copied ? '已复制' : '复制总结' }}
        </button>
        <button @click="generate" class="text-sm text-slate-500 hover:text-slate-700 font-medium">
          重新生成
        </button>
        <span v-if="model" class="ml-auto text-xs text-slate-300">{{ model }}</span>
      </div>
    </div>

    <!-- Idle -->
    <div v-else class="py-6 text-center">
      <p class="text-sm text-slate-400 mb-4">
        解析出视频后，可一键生成大纲与核心要点，适合长视频快速了解内容。
      </p>
      <button @click="generate" :disabled="!url" class="btn-cta text-sm !py-3 !px-8">
        <svg class="w-5 h-5 inline-block mr-2 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        AI 智能总结
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { streamSummary } from '../utils/api'
import LoadingSpinner from './LoadingSpinner.vue'
import InlineText from './InlineText.vue'

const props = defineProps({
  url: { type: String, default: '' },
  // 为 true 时，一旦有 URL 就自动生成总结（用于「解析后自动总结」）。
  auto: { type: Boolean, default: false },
})

// 记录是否已自动触发过，避免同一份总结被重复生成。
let autoTriggered = false

const summary = ref('')
const model = ref('')
const loading = ref(false)
const error = ref('')
const copied = ref(false)

// Lightweight markdown-lite parser: map transcript lines to heading / bullet / paragraph.
const blocks = computed(() => {
  if (!summary.value) return []
  const out = []
  let list = null
  const flushList = () => {
    if (list && list.length) {
      out.push({ type: 'ul', items: [...list] })
      list = null
    }
  }
  for (const raw of summary.value.split('\n')) {
    const line = raw.trim()
    if (!line) continue
    const match = line.match(/^(#{1,3})\s+(.*)$/)
    if (match) {
      flushList()
      out.push({ type: match[1].length === 1 ? 'h2' : 'h3', text: match[2] })
      continue
    }
    if (/^[-*•]\s+/.test(line) || /^\d+[.、]\s+/.test(line)) {
      if (!list) list = []
      list.push(line.replace(/^[-*•]\s+|^\d+[.、]\s+/, ''))
      continue
    }
    flushList()
    out.push({ type: 'p', text: line })
  }
  flushList()
  return out
})

async function generate() {
  if (loading.value || !props.url.trim()) return
  loading.value = true
  error.value = ''
  summary.value = ''
  model.value = ''
  copied.value = false

  await streamSummary(
    { url: props.url.trim() },
    {
      onText(chunk) {
        summary.value += chunk
      },
      onError(msg) {
        error.value = msg
      },
      onDone() {
        loading.value = false
      },
    }
  )
  loading.value = false
}

async function copySummary() {
  if (!summary.value) return
  try {
    await navigator.clipboard.writeText(summary.value.trim())
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch (e) {
    // Ignore clipboard errors (e.g. non-secure context)
  }
}

// 换了一个视频后清空旧总结；若开启 auto 且尚未触发，则自动生成一次。
// immediate 保证挂载时（解析已完成的视频）也能触发。
watch(
  () => props.url,
  (val) => {
    summary.value = ''
    model.value = ''
    error.value = ''
    copied.value = false
    if (props.auto && val.trim() && !autoTriggered) {
      autoTriggered = true
      generate()
    }
  },
  { immediate: true }
)
</script>
