<template>
  <div class="min-h-[70vh] flex items-center justify-center bg-slate-50 px-4 py-12">
    <div class="w-full max-w-md">
      <div class="card p-8">
        <div class="text-center mb-8">
          <div class="w-14 h-14 bg-hero-gradient rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-md shadow-primary-500/20">
            <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h1 class="text-2xl font-extrabold text-slate-900 mb-1">创建账号</h1>
          <p class="text-slate-500 text-sm">注册后即可开通会员，解锁无限下载与 AI 功能</p>
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
              minlength="8"
              autocomplete="new-password"
              placeholder="至少 8 位"
              class="input-primary"
            />
            <p class="text-xs text-slate-400 mt-1">至少 8 位，建议字母 + 数字组合。</p>
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">确认密码</label>
            <input
              v-model="confirm"
              type="password"
              required
              autocomplete="new-password"
              placeholder="再次输入密码"
              class="input-primary"
            />
          </div>
          <button type="submit" :disabled="loading" class="btn-primary w-full !py-3.5 flex items-center justify-center gap-2">
            <LoadingSpinner v-if="loading" :size="18" inline />
            <template v-else>注册并登录</template>
          </button>
        </form>

        <p class="text-center text-sm text-slate-500 mt-6">
          已有账号？
          <router-link to="/login" class="text-primary-500 font-semibold hover:underline">去登录</router-link>
        </p>
      </div>
      <p class="text-center text-xs text-slate-400 mt-4">
        注册即表示同意
        <router-link to="/terms" class="text-slate-400 hover:text-primary-500 underline">服务条款</router-link> 与
        <router-link to="/privacy" class="text-slate-400 hover:text-primary-500 underline">隐私政策</router-link>
        。
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
const { register } = useAuth()

const email = ref('')
const password = ref('')
const confirm = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''
  if (password.value.length < 8) {
    error.value = '密码至少需要 8 位。'
    return
  }
  if (password.value !== confirm.value) {
    error.value = '两次输入的密码不一致。'
    return
  }
  loading.value = true
  try {
    await register({ email: email.value.trim(), password: password.value })
    const redirect = route.query.redirect || '/download'
    router.push(redirect)
  } catch (err) {
    error.value = err.response?.data?.detail || '注册失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}
</script>