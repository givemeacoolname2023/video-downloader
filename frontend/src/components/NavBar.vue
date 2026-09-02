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

          <!-- Auth area (desktop) -->
          <template v-if="isLoggedIn">
            <router-link
              v-if="isMember"
              to="/membership"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-cta-gradient text-white text-xs font-bold"
            >
              ✦ 会员
            </router-link>
            <router-link to="/membership" class="text-slate-600 hover:text-primary-500 transition-colors font-medium text-sm">
              {{ user?.email }}
            </router-link>
            <button @click="handleLogout" class="text-slate-500 hover:text-red-500 transition-colors font-medium text-sm">
              退出
            </button>
          </template>
          <template v-else>
            <router-link to="/login" class="text-slate-600 hover:text-primary-500 transition-colors font-medium text-sm">
              登录
            </router-link>
            <button @click="$router.push('/register')" class="btn-primary text-sm !py-2 !px-5">
              免费注册
            </button>
          </template>
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

          <template v-if="isLoggedIn">
            <div class="pt-1 px-4 text-sm text-slate-500 truncate">{{ user?.email }}</div>
            <router-link to="/membership" class="block py-2 px-4 text-primary-600 hover:text-primary-500 font-medium" @click="mobileOpen = false">会员中心</router-link>
            <button @click="handleLogout" class="block w-full text-left py-2 px-4 text-slate-600 hover:text-red-500 font-medium">退出登录</button>
          </template>
          <template v-else>
            <router-link to="/login" class="block py-2 px-4 text-slate-600 hover:text-primary-500 font-medium" @click="mobileOpen = false">登录</router-link>
            <button @click="$router.push('/register'); mobileOpen = false" class="btn-primary w-full text-sm !py-2.5 mt-2">免费注册</button>
          </template>
        </div>
      </transition>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const mobileOpen = ref(false)
const { user, isMember, isLoggedIn, logout } = useAuth()

function handleLogout() {
  logout()
  mobileOpen.value = false
  if (router.currentRoute.value.path === '/membership') {
    router.push('/')
  }
}
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