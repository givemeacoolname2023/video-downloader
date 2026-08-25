<template>
  <div class="card p-6">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-5">
      <div class="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center shrink-0">
        <svg class="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold text-slate-900">AI 思维导图</h3>
        <p class="text-xs text-slate-400">将视频核心结构可视化，可缩放、拖拽、折叠</p>
      </div>
    </div>

    <!-- Loading (only before any map content has arrived) -->
    <div v-if="loading && !mindmap" class="py-4">
      <LoadingSpinner text="AI 正在梳理视频结构并生成导图，请稍候..." />
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
    <div v-else-if="mindmap">
      <div ref="svgWrap" class="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <svg ref="svgRef" class="w-full" style="height: 420px;"></svg>
      </div>
      <p class="mt-2 text-xs text-slate-400">提示：可拖动画布、滚轮缩放、点击节点折叠/展开</p>

      <div class="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-3">
        <button @click="generate" class="text-sm text-slate-500 hover:text-slate-700 font-medium">
          重新生成
        </button>
        <button v-if="renderFailed" @click="showOutline = !showOutline" class="text-sm text-primary-600 hover:text-primary-700 font-medium">
          {{ showOutline ? '隐藏大纲' : '查看文本大纲' }}
        </button>

        <!-- Download dropdown: PNG / SVG -->
        <div class="relative">
          <button
            @click="downloadOpen = !downloadOpen"
            class="text-sm text-slate-500 hover:text-slate-700 font-medium flex items-center gap-1"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            下载
          </button>
          <div
            v-if="downloadOpen"
            class="absolute z-10 mt-2 left-0 w-40 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden"
          >
            <button
              @click="downloadPng"
              class="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
            >PNG 图片</button>
            <button
              @click="downloadSvg"
              class="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 border-t border-slate-100"
            >SVG 矢量图</button>
          </div>
        </div>

        <span v-if="model" class="ml-auto text-xs text-slate-300">{{ model }}</span>
        <span v-if="downloadMsg" class="w-full mt-2 text-xs text-slate-400">{{ downloadMsg }}</span>
      </div>

      <!-- Fallback text outline: shown if the interactive canvas is empty -->
      <pre
        v-if="renderFailed && showOutline"
        class="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 whitespace-pre-wrap overflow-auto max-h-64"
      >{{ mindmap }}</pre>
    </div>

    <!-- Idle -->
    <div v-else class="py-6 text-center">
      <p class="text-sm text-slate-400 mb-4">
        生成一份层级的思维导图，快速掌握视频的知识结构。
      </p>
      <button @click="generate" :disabled="!url" class="btn-cta text-sm !py-3 !px-8">
        <svg class="w-5 h-5 inline-block mr-2 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.75v7.5m0 0l-5.25 5.25M11 11.25l5.25 5.25M7.5 21h9" />
        </svg>
        AI 思维导图
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onBeforeUnmount, watch } from 'vue'
import { Transformer } from 'markmap-lib'
import { Markmap } from 'markmap-view'
import { toPng } from 'html-to-image'
import { generateMindmap } from '../utils/api'
import LoadingSpinner from './LoadingSpinner.vue'

const props = defineProps({
  url: { type: String, default: '' },
})

const mindmap = ref('')
const model = ref('')
const loading = ref(false)
const error = ref('')
const renderFailed = ref(false)
const showOutline = ref(false)
const downloadOpen = ref(false)
const downloadMsg = ref('')

const svgRef = ref(null)

let transformer = null
let markmap = null

// Lazy-create the markmap transformer once.
function getTransformer() {
  if (!transformer) transformer = new Transformer()
  return transformer
}

async function renderMindmap() {
  if (!svgRef.value || !mindmap.value) return

  // Give the SVG an explicit size so markmap's getBoundingClientRect() reads a
  // real value; a zero-size canvas collapses the whole tree to a point (an
  // "empty map"). Fall back to a default only if the parent can't be measured.
  const svg = svgRef.value
  const wrap = svg.parentElement
  if (wrap?.clientWidth) {
    svg.style.width = `${wrap.clientWidth}px`
  } else {
    svg.style.width = '800px'
  }
  svg.style.height = '420px'

  const { root } = getTransformer().transform(mindmap.value)
  if (markmap) {
    markmap.destroy()
    markmap = null
  }
  markmap = Markmap.create(svg, { duration: 300, scrollForPan: true })
  await markmap.setData(root)
  // fit() after the layout has settled — the instance's own fit can fire
  // before the SVG has a real size on the first paint.
  await new Promise((resolve) => requestAnimationFrame(resolve))
  markmap.fit()

  // If the tree still has no measurable bounds, mark it as a failed render so
  // the panel can fall back to the raw outline instead of a blank canvas.
  const rect = markmap.state?.rect
  if (!rect || rect.width <= 0 || rect.height <= 0) {
    renderFailed.value = true
  }
}

// Derive a safe file name from the mind map's top-level topic (first "# " line).
function extractTitle() {
  const first = mindmap.value.split('\n').find((l) => l.trim().startsWith('# '))
  const title = first
    ? first.trim().replace(/^#\s+/, '').replace(/[\\/:*?"<>|]/g, '_').trim()
    : ''
  return title ? `思维导图_${title}` : '思维导图'
}

// Trigger a browser download for an already-created blob; revoke lazily so the
// download has started.
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

function saveDataUrl(dataUrl, filename) {
  const a = document.createElement('a')
  a.href = dataUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
}

// Clone the rendered markmap <svg> with an explicit size/viewBox. Markmap sizes
// its canvas purely via CSS, so a bare SVG would have no intrinsic dimensions
// and render blank/zero-size when loaded as an image (or in an editor).
function prepareSvgClone() {
  const svg = svgRef.value
  if (!svg) return null
  const rect = svg.getBoundingClientRect()
  const w = Math.max(1, Math.round(rect.width))
  const h = Math.max(1, Math.round(rect.height))
  const clone = svg.cloneNode(true)
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  clone.setAttribute('xmlns:xhtml', 'http://www.w3.org/1999/xhtml')
  clone.setAttribute('width', w)
  clone.setAttribute('height', h)
  clone.setAttribute('viewBox', `0 0 ${w} ${h}`)
  return { clone, w, h }
}

function downloadSvg() {
  const prepared = prepareSvgClone()
  if (!prepared) return
  const data = new XMLSerializer().serializeToString(prepared.clone)
  saveBlob(new Blob([data], { type: 'image/svg+xml;charset=utf-8' }), `${extractTitle()}.svg`)
  downloadMsg.value = '已下载 SVG 文件'
  downloadOpen.value = false
}

async function downloadPng() {
  const wrap = svgRef.value?.parentElement
  if (!wrap) return

  const rect = wrap.getBoundingClientRect()
  const w = Math.max(1, Math.round(rect.width))
  const h = Math.max(1, Math.round(rect.height))

  downloadMsg.value = '正在导出 PNG…'
  downloadOpen.value = false

  try {
    // html-to-image 栅格化含 <foreignObject> 的 markmap SVG。它会把节点克隆到
    // 离屏容器并内联全部计算样式/字体，生成自包含图，从而规避 Chromium 对
    // foreignObject SVG 的 canvas 污染限制——这是手写 <img>+canvas 做不到的。
    await document.fonts.ready
    // 第一遍 toPng 先“暖”字体缓存（html-to-image + foreignObject 的已知坑），
    // 第二遍才真正导出，避免首张图文字空缺/白图。
    await toPng(wrap, {
      backgroundColor: '#ffffff',
      pixelRatio: 2,
      style: { width: `${w}px`, height: `${h}px` },
    })
    const dataUrl = await toPng(wrap, {
      backgroundColor: '#ffffff',
      pixelRatio: 2,
      style: { width: `${w}px`, height: `${h}px` },
    })
    saveDataUrl(dataUrl, `${extractTitle()}.png`)
    downloadMsg.value = '已下载 PNG 图片'
  } catch (e) {
    downloadMsg.value = '导出 PNG 失败，请重试。'
    console.error('PNG export failed', e)
  }
}

async function generate() {
  if (loading.value || !props.url.trim()) return
  loading.value = true
  error.value = ''
  mindmap.value = ''
  model.value = ''
  renderFailed.value = false
  showOutline.value = false
  downloadOpen.value = false
  downloadMsg.value = ''

  try {
    const result = await generateMindmap(props.url.trim())
    if (result.success && result.data?.mindmap) {
      mindmap.value = result.data.mindmap
      model.value = result.data.model || ''
      await nextTick()
      try {
        await renderMindmap()
      } catch (e) {
        // If the interactive canvas fails to render, offer the outline instead.
        renderFailed.value = true
      }
    } else {
      error.value = result.message || '生成思维导图失败，请稍后重试。'
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || '生成思维导图失败，请检查网络后重试。'
  } finally {
    loading.value = false
  }
}

// Re-render when the underlying url changes (e.g. a new video is parsed).
watch(
  () => props.url,
  () => {
    mindmap.value = ''
    model.value = ''
    renderFailed.value = false
    showOutline.value = false
    if (markmap) {
      markmap.destroy()
      markmap = null
    }
  }
)

onBeforeUnmount(() => {
  if (markmap) {
    markmap.destroy()
    markmap = null
  }
})
</script>
