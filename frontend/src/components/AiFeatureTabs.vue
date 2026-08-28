<template>
  <div class="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden animate-slide-up">
    <!-- Tab bar -->
    <div class="flex border-b border-slate-100 overflow-x-auto bg-slate-50/60">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        class="flex items-center gap-2 px-4 py-3.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px shrink-0"
        :class="
          activeTab === tab.key
            ? 'border-primary-500 text-primary-600 bg-white'
            : 'border-transparent text-slate-500 hover:text-slate-700'
        "
      >
        <component :is="tab.icon" class="w-4 h-4" />
        {{ tab.label }}
      </button>
    </div>

    <!-- Active panel (v-show keeps each panel's state alive across tab switches) -->
    <div class="p-5 sm:p-6 min-h-[420px]">
      <div v-show="activeTab === 'summary'">
        <SummaryPanel :url="url" :auto="autoSummary" />
      </div>
      <div v-show="activeTab === 'mindmap'">
        <MindMapPanel :url="url" :active="activeTab === 'mindmap'" />
      </div>
      <div v-show="activeTab === 'qa'">
        <QaPanel :url="url" />
      </div>
      <div v-show="activeTab === 'subtitle'">
        <SubtitlePanel :url="url" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SummaryPanel from './SummaryPanel.vue'
import MindMapPanel from './MindMapPanel.vue'
import QaPanel from './QaPanel.vue'
import SubtitlePanel from './SubtitlePanel.vue'

const props = defineProps({
  url: { type: String, default: '' },
  // 是否在解析出视频后自动生成「AI总结」（默认开启）
  autoSummary: { type: Boolean, default: true },
})

// 图标定义为内联 SVG，避免额外打包
const iconSummary = {
  template: `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/></svg>`,
}
const iconMindmap = {
  template: `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15"/></svg>`,
}
const iconQa = {
  template: `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zm0 0v6m0-6h.008V6h-.008zm0 8.25a.75.75 0 110-1.5.75.75 0 010 1.5zm-2.25 3a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-4.5zM21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`,
}
const iconSubtitle = {
  template: `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3.75 7.5h16.5M3.75 12h16.5m-16.5 4.5h16.5m-16.5 4.5h16.5"/></svg>`,
}

const tabs = [
  { key: 'summary', label: 'AI 总结', icon: iconSummary },
  { key: 'mindmap', label: '思维导图', icon: iconMindmap },
  { key: 'qa', label: 'AI 问答', icon: iconQa },
  { key: 'subtitle', label: '字幕列表', icon: iconSubtitle },
]

const activeTab = ref('summary')
</script>
