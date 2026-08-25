<template>
  <div class="card p-6">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-5">
      <div class="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center shrink-0">
        <svg class="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold text-slate-900">AI 问答</h3>
        <p class="text-xs text-slate-400">基于字幕内容提问，AI 逐字回答</p>
      </div>
      <button
        v-if="messages.length"
        @click="clear"
        class="ml-auto text-sm text-slate-400 hover:text-slate-600 font-medium"
      >
        清空
      </button>
    </div>

    <!-- Messages -->
    <div v-if="messages.length" class="space-y-4 max-h-96 overflow-y-auto pr-1">
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'"
      >
        <div
          :class="[
            'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap break-words',
            msg.role === 'user'
              ? 'bg-hero-gradient text-white rounded-br-md'
              : 'bg-slate-100 text-slate-700 rounded-bl-md',
          ]"
        >
          <span v-html="renderMessage(msg.content)"></span>
          <span v-if="msg.streaming" class="inline-block w-1.5 h-4 ml-1 align-middle bg-primary-500 animate-pulse"></span>
        </div>
      </div>
    </div>

    <!-- Empty / input -->
    <div v-if="!messages.length" class="text-sm text-slate-400 text-center py-6">
      对视频内容有任何疑问，都可以问 AI，例如「视频讲了哪几个重点？」
    </div>

    <!-- Input -->
    <div class="mt-4 flex items-end gap-3">
      <textarea
        v-model="input"
        rows="1"
        placeholder="输入你的问题..."
        class="input-primary !py-3 flex-1 resize-none"
        @keydown.enter.exact.prevent="send"
        :disabled="loading"
      ></textarea>
      <button
        v-if="!loading"
        @click="send"
        :disabled="!input.trim() || !url"
        class="btn-primary text-sm !py-3 !px-5 flex items-center gap-2 shrink-0"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
        </svg>
        发送
      </button>
      <button
        v-else
        @click="stop"
        class="bg-slate-200 text-slate-600 text-sm font-medium !py-3 !px-5 rounded-xl shrink-0"
      >
        <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
        </svg>
        停止
      </button>
    </div>
    <p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { streamQa } from '../utils/api'

const props = defineProps({
  url: { type: String, default: '' },
})

const input = ref('')
const messages = ref([])
const loading = ref(false)
const error = ref('')

let abortController = null

const sendHistory = computed(() => {
  // Everything except a trailing in-progress assistant placeholder.
  const list = [...messages.value]
  if (list.length && list[list.length - 1].streaming) list.pop()
  return list.map((m) => ({ role: m.role, content: m.content }))
})

// Minimal markdown-lite for assistant replies: bold (**x**), inline code (`x`),
// and links. Keeps it safe (no v-html from user text, but this is model output).
function renderMessage(text) {
  if (!text) return ''
  const escape = (s) => s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]))
  return escape(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="px-1 py-0.5 bg-slate-200 rounded text-xs">$1</code>')
}

async function send() {
  const question = input.value.trim()
  if (!question || loading.value || !props.url.trim()) return
  error.value = ''
  input.value = ''

  messages.value.push({ role: 'user', content: question })
  messages.value.push({ role: 'assistant', content: '', streaming: true })
  loading.value = true

  abortController = new AbortController()

  const history = sendHistory.value
  const assistant = messages.value[messages.value.length - 1]

  await streamQa(
    { url: props.url.trim(), question, history },
    {
      signal: abortController.signal,
      onText(chunk) {
        assistant.content += chunk
      },
      onError(msg) {
        error.value = msg
        assistant.streaming = false
        if (!assistant.content) messages.value.pop()
      },
      onDone() {
        assistant.streaming = false
        loading.value = false
      },
    }
  )
}

function stop() {
  if (abortController) abortController.abort()
  const last = messages.value[messages.value.length - 1]
  if (last && last.streaming) {
    last.streaming = false
    if (!last.content) messages.value.pop()
  }
  loading.value = false
}

function clear() {
  messages.value = []
  error.value = ''
  loading.value = false
  if (abortController) abortController.abort()
}
</script>
