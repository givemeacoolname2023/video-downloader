<template>
  <div class="card p-6 text-center group hover:-translate-y-1 transition-all duration-300">
    <div class="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
      {{ icon }}
    </div>
    <h3 class="text-lg font-bold text-slate-900 mb-2">{{ title }}</h3>
    <p class="text-slate-500 text-sm leading-relaxed">{{ description }}</p>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  color: { type: String, default: 'blue' },
})
</script>