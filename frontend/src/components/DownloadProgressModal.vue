<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm" @click.self="$emit('close')">
        <div class="glass-card w-full max-w-md p-6 relative">
          <!-- Close button -->
          <button @click="$emit('close')" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- Success state -->
          <template v-if="status === 'completed'">
            <div class="text-center py-6">
              <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 class="text-xl font-bold text-slate-900 mb-2">下载完成！</h3>
              <p class="text-slate-500 text-sm mb-6">{{ filename }}</p>
              <div class="flex gap-3 justify-center">
                <a
                  v-if="downloadUrl"
                  :href="downloadUrl"
                  download
                  class="btn-primary text-sm !py-2.5 !px-6"
                >
                  保存文件
                </a>
                <button
                  @click="$emit('close')"
                  class="px-5 py-2.5 text-slate-600 border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors text-sm"
                >
                  继续下载
                </button>
              </div>
            </div>
          </template>

          <!-- Error state -->
          <template v-else-if="status === 'error'">
            <div class="text-center py-6">
              <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h3 class="text-xl font-bold text-slate-900 mb-2">下载失败</h3>
              <p class="text-slate-500 text-sm mb-6">{{ errorMessage }}</p>
              <button
                @click="$emit('close')"
                class="btn-primary text-sm !py-2.5 !px-6"
              >
                重试
              </button>
            </div>
          </template>

          <!-- Downloading state -->
          <template v-else>
            <div class="text-center py-6">
              <h3 class="text-lg font-bold text-slate-900 mb-4">正在下载...</h3>
              
              <!-- Progress bar -->
              <div class="w-full bg-slate-200 rounded-full h-3 mb-2 overflow-hidden">
                <div
                  class="bg-hero-gradient h-full rounded-full transition-all duration-500 ease-out"
                  :style="{ width: progress + '%' }"
                ></div>
              </div>
              
              <div class="flex justify-between text-sm text-slate-500 mb-4">
                <span>{{ progress }}%</span>
                <span v-if="speed">{{ speed }}</span>
              </div>

              <p class="text-xs text-slate-400">
                {{ statusText }}
              </p>
            </div>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  status: { type: String, default: 'downloading' }, // 'downloading' | 'completed' | 'error'
  progress: { type: Number, default: 0 },
  speed: { type: String, default: '' },
  filename: { type: String, default: '' },
  downloadUrl: { type: String, default: '' },
  errorMessage: { type: String, default: '发生未知错误，请重试。' },
  statusText: { type: String, default: '正在解析视频信息...' },
})

defineEmits(['close'])
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}
.modal-enter-active > div,
.modal-leave-active > div {
  transition: transform 0.3s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from > div {
  transform: scale(0.95) translateY(10px);
}
.modal-leave-to > div {
  transform: scale(0.95) translateY(10px);
}
</style>