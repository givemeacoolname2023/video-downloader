<template>
  <nav class="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2.5 group">
          <div class="w-9 h-9 bg-hero-gradient rounded-lg flex items-center justify-center shadow-md shadow-primary-500/20 group-hover:shadow-lg transition-all duration-300">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </div>
          <span class="text-lg font-bold text-slate-800">
            <span class="gradient-text">Video</span>Down
          </span>
        </router-link>

        <!-- Nav Links -->
        <div class="hidden sm:flex items-center gap-6">
          <router-link to="/" class="text-slate-600 hover:text-primary-500 transition-colors font-medium text-sm">
            首页
          </router-link>
          <router-link to="/download" class="text-slate-600 hover:text-primary-500 transition-colors font-medium text-sm">
            开始下载
          </router-link>
          <a href="#features" class="text-slate-600 hover:text-primary-500 transition-colors font-medium text-sm">
            功能介绍
          </a>
          <a href="#pricing" class="text-slate-600 hover:text-primary-500 transition-colors font-medium text-sm">
            定价方案
          </a>
          <button class="btn-primary text-sm !py-2 !px-5">
            立即使用
          </button>
        </div>

        <!-- Mobile Menu Button -->
        <button class="sm:hidden p-2 text-slate-600 hover:text-primary-500" @click="mobileOpen = !mobileOpen">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path v-if="!mobileOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Mobile Menu -->
      <transition name="slide-down">
        <div v-if="mobileOpen" class="sm:hidden pb-4 space-y-2">
          <router-link to="/" class="block py-2 px-4 text-slate-600 hover:text-primary-500 font-medium" @click="mobileOpen = false">首页</router-link>
          <router-link to="/download" class="block py-2 px-4 text-slate-600 hover:text-primary-500 font-medium" @click="mobileOpen = false">开始下载</router-link>
          <a href="#features" class="block py-2 px-4 text-slate-600 hover:text-primary-500 font-medium" @click="mobileOpen = false">功能介绍</a>
          <a href="#pricing" class="block py-2 px-4 text-slate-600 hover:text-primary-500 font-medium" @click="mobileOpen = false">定价方案</a>
          <button class="btn-primary w-full text-sm !py-2.5 mt-2">立即使用</button>
        </div>
      </transition>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'

const mobileOpen = ref(false)
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
  max-height: 300px;
}
.slide-down-enter-from,
.slide-down-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}
</style>