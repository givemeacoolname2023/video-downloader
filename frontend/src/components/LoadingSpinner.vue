<template>
  <div class="flex flex-col items-center justify-center py-8">
    <div class="relative w-12 h-12">
      <div class="absolute inset-0 rounded-full border-3 border-slate-200"></div>
      <div class="absolute inset-0 rounded-full border-3 border-transparent border-t-primary-500 animate-spin"></div>
    </div>
    <p class="mt-4 text-slate-500 text-sm" v-if="text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: '加载中...' },
})
</script>