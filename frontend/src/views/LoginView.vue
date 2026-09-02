<template>
  <div class="min-h-[70vh] flex items-center justify-center bg-slate-50 px-4 py-12">
    <div class="w-full max-w-md">
      <div class="card p-8">
        <div class="text-center mb-8">
          <div class="w-14 h-14 bg-hero-gradient rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-md shadow-primary-500/20">
            <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h1 class="text-2xl font-extrabold text-slate-900 mb-1">欢迎回来</h1>
          <p class="text-slate-500 text-sm">登录后即可使用会员 AI 与无限下载功能</p>
        </div>

        <!-- Error -->
        <div v-if="error" class="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          {{ error }}
        </div>

        <form class="space-y-4" @submit.prevent="handleSubmit">
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">邮箱</label>
            <input
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="you@example.com"
              class="input-primary"
            />
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">密码</label>
            <input
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              placeholder="请输入密码"
              class="input-primary"
            />
          </div>
          <button type="submit" :disabled="loading" class="btn-primary w-full !py-3.5 flex items-center justify-center gap-2">
            <LoadingSpinner v-if="loading" :size="18" inline />
            <template v-else>登录</template>
          </button>
        </form>

        <p class="text-center text-sm text-slate-500 mt-6">
          还没有账号？
          <router-link to="/register" class="text-primary-500 font-semibold hover:underline">免费注册</router-link>
        </p>
      </div>
      <p class="text-center text-xs text-slate-400 mt-4">
        免费版每天可下载 3 次、使用 AI 功能 3 次，开通会员后无限制。
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const router = useRouter()
const route = useRoute()
const { login } = useAuth()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await login({ email: email.value.trim(), password: password.value })
    // 登录后回到来时的页面，否则进下载页。
    const redirect = route.query.redirect || '/download'
    router.push(redirect)
  } catch (err) {
    error.value = err.response?.data?.detail || '登录失败，请检查邮箱或密码。'
  } finally {
    loading.value = false
  }
}
</script>