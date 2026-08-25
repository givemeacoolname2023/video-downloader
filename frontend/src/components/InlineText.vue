<template>
  <!-- Render inline markdown (bold / italic / code / strikethrough) as real HTML
       elements instead of showing the raw ** markers. Uses a fragment v-for, so
       this component can be dropped inside headings, paragraphs and list items. -->
  <template v-for="(seg, i) in segs" :key="i">
    <strong v-if="seg.bold" class="font-bold text-slate-900">{{ seg.text }}</strong>
    <em v-else-if="seg.italic" class="italic">{{ seg.text }}</em>
    <code
      v-else-if="seg.code"
      class="px-1 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[0.85em]"
    >{{ seg.text }}</code>
    <del v-else-if="seg.strike" class="line-through">{{ seg.text }}</del>
    <span v-else>{{ seg.text }}</span>
  </template>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
})

// Split a string into plain + formatted segments on the inline markdown markers
// the LLM tends to emit. Order matters: ** must be tested before * so a single
// asterisk isn't mistaken for a bold closer.
const segs = computed(() => {
  const text = props.text || ''
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|~~[^~]+~~)/g
  const out = []
  let last = 0
  let m
  while ((m = re.exec(text))) {
    if (m.index > last) {
      out.push({ text: text.slice(last, m.index) })
    }
    const token = m[0]
    if (token.startsWith('**')) {
      out.push({ text: token.slice(2, -2), bold: true })
    } else if (token.startsWith('~~')) {
      out.push({ text: token.slice(2, -2), strike: true })
    } else if (token.startsWith('`')) {
      out.push({ text: token.slice(1, -1), code: true })
    } else {
      out.push({ text: token.slice(1, -1), italic: true })
    }
    last = m.index + token.length
  }
  if (last < text.length) {
    out.push({ text: text.slice(last) })
  }
  if (!out.length) {
    out.push({ text })
  }
  return out
})
</script>
