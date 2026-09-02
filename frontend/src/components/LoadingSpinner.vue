<template>
  <div class="flex flex-col items-center justify-center" :class="inline ? '' : 'py-8'">
    <div class="relative" :style="{ width: size + 'px', height: size + 'px' }">
      <div class="absolute inset-0 rounded-full border-3 border-slate-200"></div>
      <div class="absolute inset-0 rounded-full border-3 border-transparent border-t-primary-500 animate-spin"></div>
    </div>
    <p class="mt-4 text-slate-500 text-sm" v-if="text && !inline">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: '加载中...' },
  // 外框直径（px）。按钮内联时用较小值。
  size: { type: Number, default: 48 },
  // true = 无上下留白、不显示文字，适合嵌入按钮/表单。
  inline: { type: Boolean, default: false },
})
</script>